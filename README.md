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

## Testing

### Prerequisites

```bash
# Pull required image
podman pull alpine:latest

# Start the API
python3 demo-podman-api.py
```

### Complete Test Script

```bash
#!/bin/bash
set -e

API_URL="http://localhost:5000/api/v1"
CONTAINER_NAME="test-container-$(date +%s)"

echo "Testing Podman API with container: $CONTAINER_NAME"

# 1. Health check
echo "1. Health check"
HEALTH=$(curl -s -X GET $API_URL/health | jq -r .status)
if [ "$HEALTH" != "healthy" ]; then
    echo "❌ Health check failed"
    exit 1
fi
echo "✅ Health check passed"

# 2. Create container
echo "2. Creating container"
CREATE_RESULT=$(curl -s -X POST $API_URL/containers \
  -H "Content-Type: application/json" \
  -d "{\"image\": \"alpine:latest\", \"name\": \"$CONTAINER_NAME\", \"command\": \"sleep 300\"}")

CREATE_SUCCESS=$(echo $CREATE_RESULT | jq -r .success)
if [ "$CREATE_SUCCESS" != "true" ]; then
    echo "❌ Container creation failed"
    echo $CREATE_RESULT | jq
    exit 1
fi
echo "✅ Container created successfully"

# 3. List containers and verify
echo "3. Verifying container exists"
CONTAINER_EXISTS=$(curl -s -X GET $API_URL/containers | jq -r ".containers[] | select(.name==\"$CONTAINER_NAME\") | .name")
if [ "$CONTAINER_EXISTS" != "$CONTAINER_NAME" ]; then
    echo "❌ Container not found in list"
    exit 1
fi
echo "✅ Container found in list"

# 4. Add user
echo "4. Adding user"
USER_RESULT=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/users \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass", "shell": "/bin/sh"}')

USER_SUCCESS=$(echo $USER_RESULT | jq -r .success)
if [ "$USER_SUCCESS" != "true" ]; then
    echo "❌ User creation failed"
    echo $USER_RESULT | jq
    exit 1
fi
echo "✅ User created successfully"

# 5. Verify user exists
echo "5. Verifying user exists"
USER_CHECK=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "grep testuser /etc/passwd"}')

USER_EXIT_CODE=$(echo $USER_CHECK | jq -r .execution.exit_code)
if [ "$USER_EXIT_CODE" != "0" ]; then
    echo "❌ User verification failed"
    echo $USER_CHECK | jq
    exit 1
fi
echo "✅ User verified in /etc/passwd"

# 6. Add file
echo "6. Adding file"
FILE_CONTENT="Hello from API test!\nThis file was created via REST API.\nTimestamp: $(date)"
FILE_RESULT=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/files \
  -H "Content-Type: application/json" \
  -d "{\"dest_path\": \"/tmp/test-file.txt\", \"content\": \"$FILE_CONTENT\"}")

FILE_SUCCESS=$(echo $FILE_RESULT | jq -r .success)
if [ "$FILE_SUCCESS" != "true" ]; then
    echo "❌ File creation failed"
    echo $FILE_RESULT | jq
    exit 1
fi
echo "✅ File created successfully"

# 7. Verify file exists and content
echo "7. Verifying file content"
FILE_CHECK=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "cat /tmp/test-file.txt"}')

FILE_EXIT_CODE=$(echo $FILE_CHECK | jq -r .execution.exit_code)
FILE_OUTPUT=$(echo $FILE_CHECK | jq -r .execution.output)

if [ "$FILE_EXIT_CODE" != "0" ]; then
    echo "❌ File verification failed"
    echo $FILE_CHECK | jq
    exit 1
fi

if [[ "$FILE_OUTPUT" != *"Hello from API test!"* ]]; then
    echo "❌ File content verification failed"
    echo "Expected content not found in: $FILE_OUTPUT"
    exit 1
fi
echo "✅ File content verified"

# 8. Execute command as specific user
echo "8. Testing command execution as user"
USER_CMD_RESULT=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "whoami", "user": "testuser"}')

USER_CMD_OUTPUT=$(echo $USER_CMD_RESULT | jq -r .execution.output)
if [[ "$USER_CMD_OUTPUT" != *"testuser"* ]]; then
    echo "❌ User command execution failed"
    echo "Expected 'testuser', got: $USER_CMD_OUTPUT"
    exit 1
fi
echo "✅ User command execution verified"

# 9. Check logs
echo "9. Checking container logs"
LOGS_RESULT=$(curl -s -X GET "$API_URL/containers/$CONTAINER_NAME/logs?tail=10")
LOGS_SUCCESS=$(echo $LOGS_RESULT | jq -r .success)
if [ "$LOGS_SUCCESS" != "true" ]; then
    echo "❌ Log retrieval failed"
    echo $LOGS_RESULT | jq
    exit 1
fi
echo "✅ Logs retrieved successfully"

# 10. Stop container
echo "10. Stopping container"
STOP_RESULT=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/stop)
STOP_SUCCESS=$(echo $STOP_RESULT | jq -r .success)
if [ "$STOP_SUCCESS" != "true" ]; then
    echo "❌ Container stop failed"
    echo $STOP_RESULT | jq
    exit 1
fi
echo "✅ Container stopped successfully"

# 11. Verify container is stopped
echo "11. Verifying container status"
CONTAINER_STATUS=$(curl -s -X GET $API_URL/containers | jq -r ".containers[] | select(.name==\"$CONTAINER_NAME\") | .status")
if [ "$CONTAINER_STATUS" != "exited" ] && [ "$CONTAINER_STATUS" != "stopped" ]; then
    echo "⚠️  Container status is '$CONTAINER_STATUS' (expected 'exited' or 'stopped')"
else
    echo "✅ Container status verified as stopped"
fi

# 12. Remove container
echo "12. Removing container"
REMOVE_RESULT=$(curl -s -X DELETE "$API_URL/containers/$CONTAINER_NAME?force=true")
REMOVE_SUCCESS=$(echo $REMOVE_RESULT | jq -r .success)
if [ "$REMOVE_SUCCESS" != "true" ]; then
    echo "❌ Container removal failed"
    echo $REMOVE_RESULT | jq
    exit 1
fi
echo "✅ Container removed successfully"

# 13. Verify container is gone
echo "13. Verifying container removal"
CONTAINER_GONE=$(curl -s -X GET $API_URL/containers | jq -r ".containers[] | select(.name==\"$CONTAINER_NAME\") | .name")
if [ -n "$CONTAINER_GONE" ]; then
    echo "❌ Container still exists after removal"
    exit 1
fi
echo "✅ Container removal verified"

# 14. Check metrics
echo "14. Checking API metrics"
METRICS_RESULT=$(curl -s -X GET $API_URL/metrics)
UPTIME=$(echo $METRICS_RESULT | jq -r .uptime_seconds)
if [ "$UPTIME" -lt 0 ] 2>/dev/null; then
    echo "❌ Metrics retrieval failed"
    exit 1
fi
echo "✅ Metrics retrieved (uptime: ${UPTIME}s)"

echo ""
echo "🎉 All tests passed successfully!"
echo "Container lifecycle, user management, file operations, and API endpoints all working correctly."
```

### Manual Testing Commands

```bash
# Start the API server
python3 demo-podman-api.py

# Health Check
curl -X GET http://localhost:5000/api/v1/health | jq

# Container listing
curl -X GET http://localhost:5000/api/v1/containers | jq

# Container creation
curl -X POST http://localhost:5000/api/v1/containers \
  -H "Content-Type: application/json" \
  -d '{
    "image": "alpine:latest",
    "name": "demo-container",
    "command": "sleep 300"
  }' | jq

# Verify container is running
curl -X GET http://localhost:5000/api/v1/containers | jq '.containers[] | select(.name=="demo-container")'

# Command Execution
curl -X POST http://localhost:5000/api/v1/containers/demo-container/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "uname -a && whoami"}' | jq

# Add a User
curl -X POST http://localhost:5000/api/v1/containers/demo-container/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass",
    "shell": "/bin/sh"
  }' | jq

# Verify user was created
curl -X POST http://localhost:5000/api/v1/containers/demo-container/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "grep testuser /etc/passwd"}' | jq

# Add a File
curl -X POST http://localhost:5000/api/v1/containers/demo-container/files \
  -H "Content-Type: application/json" \
  -d '{
    "dest_path": "/tmp/demo.txt",
    "content": "Hello from the API!\nThis file was created via REST API.\nLine 3 content."
  }' | jq

# Verify file was created and has correct content
curl -X POST http://localhost:5000/api/v1/containers/demo-container/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "cat /tmp/demo.txt"}' | jq

# Test file permissions
curl -X POST http://localhost:5000/api/v1/containers/demo-container/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la /tmp/demo.txt"}' | jq

# Test command execution as specific user
curl -X POST http://localhost:5000/api/v1/containers/demo-container/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "whoami && id", "user": "testuser"}' | jq

# Check Container Logs
curl -X GET "http://localhost:5000/api/v1/containers/demo-container/logs?tail=20" | jq

# Stop container
curl -X POST http://localhost:5000/api/v1/containers/demo-container/stop | jq

# Verify container is stopped
curl -X GET http://localhost:5000/api/v1/containers | jq '.containers[] | select(.name=="demo-container") | .status'

# Remove container
curl -X DELETE "http://localhost:5000/api/v1/containers/demo-container?force=true" | jq

# Verify container is removed
curl -X GET http://localhost:5000/api/v1/containers | jq '.containers[] | select(.name=="demo-container")'

# Check Container Metrics
curl -X GET http://localhost:5000/api/v1/metrics | jq
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
