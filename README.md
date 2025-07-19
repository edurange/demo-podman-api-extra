# Podman REST API Documentation

A Flask-based REST API for managing Podman containers with comprehensive container lifecycle management, user management, file operations, and command execution capabilities.

## Table of Contents

- [Overview](#overview)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Testing](#testing)

## Overview

This API provides a RESTful interface to Podman container operations, including:

- Container lifecycle management (create, start, stop, remove)
- Container listing and monitoring
- Log retrieval
- User management within containers
- File operations
- Command execution
- Health checks and metrics

## Installation & Setup

### Prerequisites

- Python 3.7+
- Podman installed and configured
- Required Python packages:
  ```bash
  pip install flask flask-cors podman
  ```

### Running the API

```bash
python3 demo-podman-api.py
```

The API will start on `http://localhost:5000` by default.

## Configuration

Configure the API using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_WORKERS` | `10` | Maximum number of worker threads |
| `DEBUG` | `False` | Enable debug mode |
| `REQUEST_TIMEOUT` | `30` | Request timeout in seconds |

Example:
```bash
export MAX_WORKERS=20
export DEBUG=true
export REQUEST_TIMEOUT=60
python3 demo-podman-api.py
```

## API Endpoints

### Base URL
All endpoints are prefixed with `/api/v1`

### Container Management

#### Create Container
**POST** `/containers`

Creates and starts a new container.

**Request Body:**
```json
{
  "image": "alpine:latest",
  "name": "my-container",
  "command": "sleep 300",
  "environment": {"ENV_VAR": "value"},
  "ports": {"8080": "80"},
  "volumes": {"/host/path": "/container/path"},
  "user": "root"
}
```

**Required Fields:** `image`, `name`

**Response:**
```json
{
  "success": true,
  "container": {
    "id": "abc123def456",
    "name": "my-container",
    "status": "running"
  }
}
```

#### List Containers
**GET** `/containers`

Lists all containers (running and stopped).

**Response:**
```json
{
  "success": true,
  "containers": [
    {
      "id": "abc123def456",
      "name": "my-container",
      "status": "running",
      "image": "alpine:latest"
    }
  ]
}
```

#### Start Container
**POST** `/containers/{name}/start`

Starts a stopped container.

**Response:**
```json
{
  "success": true,
  "container": {
    "name": "my-container",
    "status": "started"
  }
}
```

#### Stop Container
**POST** `/containers/{name}/stop`

Stops a running container.

**Response:**
```json
{
  "success": true,
  "container": {
    "name": "my-container",
    "status": "stopped"
  }
}
```

#### Remove Container
**DELETE** `/containers/{name}`

Removes a container.

**Query Parameters:**
- `force` (boolean): Force removal of running container

**Response:**
```json
{
  "success": true,
  "container": {
    "name": "my-container",
    "removed": true
  }
}
```

#### Get Container Logs
**GET** `/containers/{name}/logs`

Retrieves container logs.

**Query Parameters:**
- `tail` (integer): Number of lines to retrieve (default: 100)

**Response:**
```json
{
  "success": true,
  "container": {
    "logs": "Container log output here..."
  }
}
```

### Container Operations

#### Execute Command
**POST** `/containers/{name}/exec`

Executes a command inside a container.

**Request Body:**
```json
{
  "command": "ls -la /tmp",
  "user": "root"
}
```

**Required Fields:** `command`

**Response:**
```json
{
  "success": true,
  "execution": {
    "exit_code": 0,
    "output": "total 4\ndrwxrwxrwt 2 root root 4096 Jan 1 00:00 .\n",
    "success": true
  }
}
```

#### Add User
**POST** `/containers/{name}/users`

Creates a new user inside a container.

**Request Body:**
```json
{
  "username": "newuser",
  "password": "password123",
  "shell": "/bin/bash"
}
```

**Required Fields:** `username`

**Response:**
```json
{
  "success": true,
  "user": {
    "username": "newuser",
    "created": true
  }
}
```

#### Add File
**POST** `/containers/{name}/files`

Creates a file inside a container.

**Request Body:**
```json
{
  "dest_path": "/tmp/myfile.txt",
  "content": "Hello, World!\nThis is file content."
}
```

**Required Fields:** `dest_path`, `content`

**Response:**
```json
{
  "success": true,
  "file": {
    "dest_path": "/tmp/myfile.txt",
    "size": 32
  }
}
```

### System Endpoints

#### Health Check
**GET** `/health`

Checks API and Podman connectivity.

**Response:**
```json
{
  "status": "healthy",
  "podman": "connected",
  "timestamp": "2025-01-19T15:47:19.123456"
}
```

#### Metrics
**GET** `/metrics`

Returns API performance metrics.

**Response:**
```json
{
  "uptime_seconds": 3600,
  "uptime_human": "1:00:00",
  "active_threads": 2,
  "max_workers": 10,
  "timestamp": "2025-01-19T15:47:19.123456"
}
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "message": "Error description",
    "code": 404,
    "type": "PodmanAPIError"
  },
  "timestamp": "2025-01-19T15:47:19.123456"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (missing required fields) |
| 404 | Resource not found (container, image, etc.) |
| 408 | Request timeout |
| 500 | Internal server error |
| 503 | Service unavailable (Podman connection issues) |

### Common Error Types

- **PodmanAPIError**: Podman-related errors
- **InternalError**: Server-side errors
- **ValidationError**: Request validation failures

## Examples

### Complete Container Workflow

```bash
# 1. Check API health
curl -X GET http://localhost:5000/api/v1/health | jq

# 2. Create and start container
curl -X POST http://localhost:5000/api/v1/containers \
  -H "Content-Type: application/json" \
  -d '{
    "image": "alpine:latest",
    "name": "demo-container",
    "command": "sleep 300"
  }' | jq

# 3. Add a user
curl -X POST http://localhost:5000/api/v1/containers/demo-container/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass",
    "shell": "/bin/sh"
  }' | jq

# 4. Create a file
curl -X POST http://localhost:5000/api/v1/containers/demo-container/files \
  -H "Content-Type: application/json" \
  -d '{
    "dest_path": "/tmp/demo.txt",
    "content": "Hello from the API!"
  }' | jq

# 5. Execute commands
curl -X POST http://localhost:5000/api/v1/containers/demo-container/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "cat /tmp/demo.txt"}' | jq

# 6. Check logs
curl -X GET "http://localhost:5000/api/v1/containers/demo-container/logs?tail=20" | jq

# 7. Stop and remove container
curl -X POST http://localhost:5000/api/v1/containers/demo-container/stop | jq
curl -X DELETE "http://localhost:5000/api/v1/containers/demo-container?force=true" | jq
```

### Python Client Example

```python
import requests
import json

class PodmanAPIClient:
    def __init__(self, base_url="http://localhost:5000/api/v1"):
        self.base_url = base_url
    
    def create_container(self, image, name, **kwargs):
        data = {"image": image, "name": name, **kwargs}
        response = requests.post(f"{self.base_url}/containers", json=data)
        return response.json()
    
    def execute_command(self, container_name, command, user=None):
        data = {"command": command}
        if user:
            data["user"] = user
        response = requests.post(
            f"{self.base_url}/containers/{container_name}/exec", 
            json=data
        )
        return response.json()

# Usage
client = PodmanAPIClient()
result = client.create_container("alpine:latest", "test-container")
print(json.dumps(result, indent=2))
```


## Security Considerations

- The API runs without authentication by default
- Container commands are executed with full privileges
- File operations can write anywhere in the container filesystem
- Consider implementing authentication and authorization for production use
- Validate and sanitize all user inputs
- Consider running the API behind a reverse proxy with rate limiting

## Troubleshooting

### Common Issues

1. **"Container not found" errors**: Ensure the container name is correct and the container exists
2. **"Image not found" errors**: Pull the image with `podman pull <image>` first
3. **Permission errors**: Ensure Podman is properly configured for your user
4. **Connection errors**: Check that Podman service is running

### Debug Mode

Enable debug mode for detailed logging:
```bash
export DEBUG=true
python3 demo-podman-api.py
```

### Logs

The API logs all operations. Check the console output for detailed error information.
