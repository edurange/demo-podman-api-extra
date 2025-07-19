## Configuration

### Config

Configuration class that loads settings from environment variables.
- MAX_WORKERS: Thread pool size (default: 10)
- DEBUG: Enable debug mode (default: False)
- REQUEST_TIMEOUT: Operation timeout in seconds (default: 30)

## Custom Exceptions

PodmanAPIError(message, status_code=500)

Custom exception for API errors with HTTP status codes.

## Decorators

@handle_errors

Decorator that catches exceptions and converts them to PodmanAPIError:
- Catches asyncio.TimeoutError → 408 Timeout
- Catches "not found" errors → 404 Not Found
- Catches other exceptions → 500 Internal Server Error

@validate_json(required_fields=None)

Decorator that validates JSON request data:
- Ensures request contains valid JSON
- Checks for required fields
- Returns 400 Bad Request if validation fails

### Core API Class

PodmanAPI.__init__()

Initializes the API with a thread pool executor.

PodmanAPI._get_client()

Returns a new Podman client instance.

PodmanAPI._run_async(func, timeout=30)

Executes a function asynchronously in the thread pool with timeout.

PodmanAPI._handle_exec_result(result)

Helper that normalizes exec_run results to (exit_code, output_string).

## Container Management

create_container(config)

Creates and starts a new container.
- Input: {image, name, command?, environment?, ports?, volumes?, user?}
- Returns: {id, name, status}

start_container(name)

Starts an existing container.
- Input: Container name
- Returns: {name, status}

stop_container(name)

Stops a running container.
- Input: Container name
- Returns: {name, status}

remove_container(name, force=False)

Removes a container.
- Input: Container name, force flag
- Returns: {name, removed}

list_containers()

Lists all containers (running and stopped).
- Returns: Array of {id, name, status, image}

get_container_logs(name, tail=100)

Retrieves container logs.
- Input: Container name, number of lines
- Returns: {logs}

Container Operations

add_user(container_name, user_config)

Creates a user inside a container.
- Input: Container name, {username, password?, shell?}
- Returns: {username, created}

add_file(container_name, file_config)

Creates a file inside a container.
- Input: Container name, {dest_path, content}
- Returns: {dest_path, size}

execute_command(container_name, command, user=None)

Executes a command inside a container.
- Input: Container name, command string, optional user
- Returns: {exit_code, output, success}

shutdown()

Gracefully shuts down the thread pool executor.

## Error Handlers

handle_podman_error(error)

Flask error handler for PodmanAPIError exceptions.
- Returns structured JSON error response with timestamp

handle_internal_error(error)

Flask error handler for 500 Internal Server Error.
- Logs error and returns generic error response

## API Routes

POST /api/v1/containers

Creates a new container. Requires image and name fields.

POST /api/v1/containers/<name>/start
Starts the specified container.

POST /api/v1/containers/<name>/stop
Stops the specified container.

DELETE /api/v1/containers/<name>?force=bool
Removes the specified container. Optional force parameter.

GET /api/v1/containers
Lists all containers.

GET /api/v1/containers/<name>/logs?tail=int
Gets container logs. Optional tail parameter (default: 100).

POST /api/v1/containers/<name>/users
Adds a user to the container. Requires username field.

POST /api/v1/containers/<name>/files
Adds a file to the container. Requires dest_path and content fields.

POST /api/v1/containers/<name>/exec
Executes a command in the container. Requires command field.

GET /api/v1/health
Health check endpoint. Returns Podman connection status.

GET /api/v1/metrics
Returns API metrics including uptime and thread pool status.

## Signal Handlers

shutdown_handler(sig, frame)

Handles SIGINT and SIGTERM signals for graceful shutdown.
- Logs signal details including source file and line number
- Shuts down thread pool and exits cleanly

## Response Format
Successful requests will look like this:
```
{
  "success": true,
  "container|user|file|execution": { ... },
  "timestamp": "ISO-8601-timestamp"
}
```
Errors will look like this:
```
{
  "success": false,
  "error": {
    "message": "Error description",
    "code": 400,
    "type": "ErrorType"
  },
  "timestamp": "ISO-8601-timestamp"
}
```
