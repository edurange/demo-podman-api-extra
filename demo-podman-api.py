from flask import Flask, request, jsonify
from flask_cors import CORS
import podman
import asyncio
import io
import tarfile
import logging
import os
import signal
import sys
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Configuration
class Config:
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '10'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Track startup time for metrics
startup_time = datetime.utcnow()


class PodmanAPIError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except asyncio.TimeoutError:
            logger.error(f"Timeout in {func.__name__}")
            raise PodmanAPIError("Operation timed out", 408)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            if "not found" in str(e).lower() or "no such" in str(e).lower():
                raise PodmanAPIError("Resource not found", 404)
            else:
                raise PodmanAPIError(f"Podman error: {str(e)}", 500)
    return wrapper


def validate_json(required_fields=None):
    """Simple validation decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.json or {}
            
            # Check required fields
            if required_fields:
                missing = [field for field in required_fields if not data.get(field)]
                if missing:
                    return jsonify({
                        "success": False,
                        "error": f"Missing required fields: {', '.join(missing)}"
                    }), 400
            
            return f(data, *args, **kwargs)
        return wrapper
    return decorator


class PodmanAPI:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS)
        logger.info(f"PodmanAPI initialized with {Config.MAX_WORKERS} workers")

    def _get_client(self):
        return podman.PodmanClient()

    async def _run_async(self, func, timeout=Config.REQUEST_TIMEOUT):
        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(self.executor, func), 
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise PodmanAPIError(f"Operation timed out after {timeout} seconds", 408)

    def _handle_exec_result(self, result):
        """Helper to handle exec_run results consistently"""
        if hasattr(result, 'exit_code'):
            exit_code = result.exit_code
            output = result.output
        else:
            exit_code, output = result

        output_str = output.decode('utf-8') if isinstance(output, bytes) else str(output)
        return exit_code, output_str

    def _safe_get_attr(self, obj, path, default="unknown"):
        """Safely get nested attributes from container objects"""
        try:
            current = obj
            for key in path:
                if hasattr(current, 'get') and callable(getattr(current, 'get')):
                    current = current.get(key, {})
                elif hasattr(current, key):
                    current = getattr(current, key)
                else:
                    return default
            
            # Ensure we return a string, not a dict or other object
            if current is None:
                return default
            elif isinstance(current, (dict, list)):
                return str(current)
            else:
                return str(current)
        except Exception as e:
            logger.debug(f"Error getting attribute {path}: {e}")
            return default

    @handle_errors
    def create_container(self, config):
        logger.info(f"Creating container: {config.get('name')}")
        
        def _create():
            with self._get_client() as client:
                container_config = {
                    k: v for k, v in {
                        "image": config.get("image"),
                        "name": config.get("name"),
                        "command": config.get("command"),
                        "environment": config.get("environment"),
                        "ports": config.get("ports"),
                        "volumes": config.get("volumes"),
                        "user": config.get("user"),
                        "detach": True,
                    }.items() if v is not None
                }

                container = client.containers.create(**container_config)
                container.start()
                
                container_info = client.containers.get(config.get("name"))
                
                # Get attributes more safely
                container_id = self._safe_get_attr(container_info, ['attrs', 'Id'], "")
                container_name = self._safe_get_attr(container_info, ['attrs', 'Name'], "")
                container_status = self._safe_get_attr(container_info, ['attrs', 'State', 'Status'], "unknown")
                
                result = {
                    "id": container_id[:12] if container_id else "",
                    "name": container_name.lstrip("/") if container_name and isinstance(container_name, str) else container_name,
                    "status": container_status,
                }
                
                return result

        result = asyncio.run(self._run_async(_create))
        logger.info(f"Container created successfully: {result['id']}")
        return result

    @handle_errors
    def start_container(self, name):
        logger.info(f"Starting container: {name}")
        
        def _start():
            with self._get_client() as client:
                container = client.containers.get(name)
                container.start()
                return {"name": name, "status": "started"}

        return asyncio.run(self._run_async(_start))

    @handle_errors
    def stop_container(self, name):
        logger.info(f"Stopping container: {name}")
        
        def _stop():
            with self._get_client() as client:
                container = client.containers.get(name)
                container.stop()
                return {"name": name, "status": "stopped"}

        return asyncio.run(self._run_async(_stop))

    @handle_errors
    def remove_container(self, name, force=False):
        logger.info(f"Removing container: {name} (force={force})")
        
        def _remove():
            with self._get_client() as client:
                container = client.containers.get(name)
                container.remove(force=force)
                return {"name": name, "removed": True}

        return asyncio.run(self._run_async(_remove))

    @handle_errors
    def list_containers(self):
        logger.debug("Listing containers")
        
        def _list():
            with self._get_client() as client:
                containers = client.containers.list(all=True)
                result = []
                
                for container in containers:
                    try:
                        # Get raw attributes
                        container_id = self._safe_get_attr(container, ['attrs', 'Id'], "")
                        container_name = self._safe_get_attr(container, ['attrs', 'Name'], "")
                        container_status = self._safe_get_attr(container, ['attrs', 'State', 'Status'], "unknown")
                        container_image = self._safe_get_attr(container, ['attrs', 'Config', 'Image'], "unknown")
                        
                        # Process the data safely
                        container_data = {
                            "id": container_id[:12] if container_id else "",
                            "name": container_name.lstrip("/") if container_name and isinstance(container_name, str) else str(container_name),
                            "status": container_status,
                            "image": container_image,
                        }
                        result.append(container_data)
                    except Exception as e:
                        logger.error(f"Error processing container: {e}")
                        # Add a minimal entry for problematic containers
                        result.append({
                            "id": "error",
                            "name": "error",
                            "status": "error",
                            "image": "error"
                        })
                
                return result

        return asyncio.run(self._run_async(_list))

    @handle_errors
    def get_container_logs(self, name, tail=100):
        logger.info(f"Getting logs for container: {name}")
        
        def _get_logs():
            with self._get_client() as client:
                try:
                    container = client.containers.get(name)
                    container.reload()
                    
                    # Try different approaches to get logs
                    try:
                        logs = container.logs(tail=tail)
                    except Exception as e:
                        logger.warning(f"Failed to get logs with tail parameter: {e}")
                        logs = container.logs()
                    
                    if logs is None:
                        return {"logs": "No logs available"}
                    
                    # Handle different return types
                    if isinstance(logs, bytes):
                        log_content = logs.decode('utf-8', errors='replace')
                    elif isinstance(logs, str):
                        log_content = logs
                    else:
                        log_content = str(logs)
                    
                    # Limit output if no tail was applied
                    if tail and len(log_content.split('\n')) > tail:
                        lines = log_content.split('\n')
                        log_content = '\n'.join(lines[-tail:])
                    
                    return {"logs": log_content}
                    
                except Exception as e:
                    logger.error(f"Error getting logs for {name}: {e}")
                    return {"logs": f"Error retrieving logs: {str(e)}"}

        return asyncio.run(self._run_async(_get_logs))

    @handle_errors
    def add_user(self, container_name, user_config):
        username = user_config.get("username")
        logger.info(f"Adding user {username} to container: {container_name}")
        
        def _add_user():
            with self._get_client() as client:
                container = client.containers.get(container_name)
                password = user_config.get("password", "")
                shell = user_config.get("shell", "/bin/bash")

                result = container.exec_run(["useradd", "-m", "-s", shell, username])
                exit_code, output_str = self._handle_exec_result(result)

                if exit_code != 0:
                    raise PodmanAPIError(f"Failed to create user: {output_str}")

                if password:
                    container.exec_run(["bash", "-c", f"echo '{username}:{password}' | chpasswd"])

                return {"username": username, "created": True}

        return asyncio.run(self._run_async(_add_user))

    @handle_errors
    def add_file(self, container_name, file_config):
        dest_path = file_config.get("dest_path")
        logger.info(f"Adding file {dest_path} to container: {container_name}")
        
        def _add_file():
            with self._get_client() as client:
                container = client.containers.get(container_name)
                content = file_config.get("content", "")

                tar_buffer = io.BytesIO()
                tar = tarfile.open(fileobj=tar_buffer, mode="w")

                file_data = content.encode("utf-8")
                tarinfo = tarfile.TarInfo(name=dest_path.lstrip("/"))
                tarinfo.size = len(file_data)
                tar.addfile(tarinfo, io.BytesIO(file_data))
                tar.close()

                tar_buffer.seek(0)
                container.put_archive("/", tar_buffer.getvalue())

                return {"dest_path": dest_path, "size": len(content)}

        return asyncio.run(self._run_async(_add_file))

    @handle_errors
    def execute_command(self, container_name, command, user=None):
        logger.info(f"Executing command in container {container_name}: {command[:50]}...")
        
        def _execute():
            with self._get_client() as client:
                container = client.containers.get(container_name)
                
                exec_kwargs = {"cmd": ["bash", "-c", command]}
                if user:
                    exec_kwargs["user"] = user
                
                result = container.exec_run(**exec_kwargs)
                exit_code, output_str = self._handle_exec_result(result)
                
                return {
                    "exit_code": exit_code,
                    "output": output_str,
                    "success": exit_code == 0,
                }

        return asyncio.run(self._run_async(_execute))

    def shutdown(self):
        logger.info("Shutting down PodmanAPI...")
        self.executor.shutdown(wait=True)


# Initialize API
api = PodmanAPI()


# Error handlers
@app.errorhandler(PodmanAPIError)
def handle_podman_error(error):
    return jsonify({
        "success": False,
        "error": {
            "message": error.message,
            "code": error.status_code,
            "type": "PodmanAPIError"
        },
        "timestamp": datetime.utcnow().isoformat(),
    }), error.status_code


@app.errorhandler(500)
def handle_internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "success": False,
        "error": {
            "message": "Internal server error",
            "code": 500,
            "type": "InternalError"
        },
        "timestamp": datetime.utcnow().isoformat(),
    }), 500


# API Routes (v1)
@app.route("/api/v1/containers", methods=["POST"])
@validate_json(required_fields=["image", "name"])
def create_container(data):
    result = api.create_container(data)
    return jsonify({"success": True, "container": result})


@app.route("/api/v1/containers/<name>/start", methods=["POST"])
def start_container(name):
    result = api.start_container(name)
    return jsonify({"success": True, "container": result})


@app.route("/api/v1/containers/<name>/stop", methods=["POST"])
def stop_container(name):
    result = api.stop_container(name)
    return jsonify({"success": True, "container": result})


@app.route("/api/v1/containers/<name>", methods=["DELETE"])
def remove_container(name):
    force = request.args.get("force", False, type=bool)
    result = api.remove_container(name, force)
    return jsonify({"success": True, "container": result})


@app.route("/api/v1/containers", methods=["GET"])
def list_containers():
    containers = api.list_containers()
    return jsonify({"success": True, "containers": containers})


@app.route("/api/v1/containers/<name>/logs", methods=["GET"])
def get_container_logs(name):
    tail = request.args.get('tail', 100, type=int)
    result = api.get_container_logs(name, tail)
    return jsonify({"success": True, "container": result})


@app.route("/api/v1/containers/<name>/users", methods=["POST"])
@validate_json(required_fields=["username"])
def add_user(data, name):
    result = api.add_user(name, data)
    return jsonify({"success": True, "user": result})


@app.route("/api/v1/containers/<name>/files", methods=["POST"])
@validate_json(required_fields=["dest_path", "content"])
def add_file(data, name):
    result = api.add_file(name, data)
    return jsonify({"success": True, "file": result})


@app.route("/api/v1/containers/<name>/exec", methods=["POST"])
@validate_json(required_fields=["command"])
def execute_command(data, name):
    result = api.execute_command(name, data.get("command"), data.get("user"))
    return jsonify({"success": True, "execution": result})


@app.route("/api/v1/health", methods=["GET"])
def health():
    try:
        with api._get_client() as client:
            client.containers.list(limit=1)
        return jsonify({
            "status": "healthy",
            "podman": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "podman": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503


@app.route("/api/v1/metrics", methods=["GET"])
def metrics():
    uptime = datetime.utcnow() - startup_time
    return jsonify({
        "uptime_seconds": int(uptime.total_seconds()),
        "uptime_human": str(uptime),
        "active_threads": len(api.executor._threads) if hasattr(api.executor, '_threads') else 0,
        "max_workers": Config.MAX_WORKERS,
        "timestamp": datetime.utcnow().isoformat()
    })


# Handle shutdown signals with frame info
def shutdown_handler(sig, frame):
    signal_name = signal.Signals(sig).name
    logger.info(f'Received {signal_name} signal at {frame.f_code.co_filename}:{frame.f_lineno}')
    logger.info('Shutting down gracefully...')
    api.shutdown()
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


if __name__ == "__main__":
    logger.info("Starting Podman API server...")
    app.run(
        debug=Config.DEBUG,
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
