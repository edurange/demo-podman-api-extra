Testing Checklist:


Start With:
```
python3 demo-podman-api.py
```

Health Check:
``` 
curl -X GET http://localhost:5000/api/v1/health | jq
```

Container listing:
```
curl -X GET http://localhost:5000/api/v1/containers | jq
```

Container creation:
```
curl -X POST http://localhost:5000/api/v1/containers \
  -H "Content-Type: application/json" \
  -d '{
    "image": "alpine:latest",
    "name": "demo-container",
    "command": "sleep 300"
  }' | jq
  ```

  Container health check:
  ```
  curl -X GET http://localhost:5000/api/v1/containers | jq
  ```

  Command Execution:
  ```
  curl -X POST http://localhost:5000/api/v1/containers/demo-container/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "uname -a && whoami"}' | jq
  ```

  Add a User:
  ```
  curl -X POST http://localhost:5000/api/v1/containers/demo-container/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass",
    "shell": "/bin/sh"
  }' | jq
  ```

  Add a File:
  ```
  curl -X POST http://localhost:5000/api/v1/containers/demo-container/files \
  -H "Content-Type: application/json" \
  -d '{
    "dest_path": "/tmp/demo.txt",
    "content": "Hello from the API!\nThis file was created via REST API."
  }' | jq
  ```

  Check Files and Users:
  ```
  # Check the file
curl -X POST http://localhost:5000/api/v1/containers/demo-container/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "cat /tmp/demo.txt"}' | jq

# Check the user
curl -X POST http://localhost:5000/api/v1/containers/demo-container/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "cat /etc/passwd | grep testuser"}' | jq
  ```

  Check Container Logs:
  ```
  curl -X GET "http://localhost:5000/api/v1/containers/demo-container/logs?tail=20" | jq
  ```

  Check Container Metrics:
  ```
  curl -X GET http://localhost:5000/api/v1/metrics | jq
  ```
  