#!/bin/bash

API_URL="http://localhost:5000/api/v1"
CONTAINER_NAME="demo-container"

echo "=== Podman API Demo ==="
echo

echo "1. Health Check..."
curl -s -X GET $API_URL/health | jq '.status'
echo

echo "2. Creating Alpine container..."
curl -s -X POST $API_URL/containers \
  -H "Content-Type: application/json" \
  -d "{\"image\": \"alpine:latest\", \"name\": \"$CONTAINER_NAME\", \"command\": \"sleep 300\"}" | jq '.success'
echo

echo "3. Listing containers..."
curl -s -X GET $API_URL/containers | jq '.containers[] | {name, status, image}'
echo

echo "4. Executing command..."
curl -s -X POST $API_URL/containers/$CONTAINER_NAME/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "echo Hello World && uname -a"}' | jq '.execution.output'
echo

echo "5. Adding user..."
curl -s -X POST $API_URL/containers/$CONTAINER_NAME/users \
  -H "Content-Type: application/json" \
  -d '{"username": "demouser", "shell": "/bin/sh"}' | jq '.success'
echo

echo "6. Adding file..."
curl -s -X POST $API_URL/containers/$CONTAINER_NAME/files \
  -H "Content-Type: application/json" \
  -d '{"dest_path": "/tmp/demo.txt", "content": "API Demo File\nCreated successfully!"}' | jq '.success'
echo

echo "7. Reading file..."
curl -s -X POST $API_URL/containers/$CONTAINER_NAME/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "cat /tmp/demo.txt"}' | jq -r '.execution.output'
echo

echo "8. Cleanup..."
curl -s -X POST $API_URL/containers/$CONTAINER_NAME/stop | jq '.success'
curl -s -X DELETE "$API_URL/containers/$CONTAINER_NAME?force=true" | jq '.success'
echo

echo "Demo complete!"