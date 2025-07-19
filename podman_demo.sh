#!/bin/bash

API_URL="http://localhost:5000/api/v1"
CONTAINER_NAME="test-container-$(date +%s)"
FAILED_TESTS=0
TOTAL_TESTS=0

# Function to run test and check result
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo "Test $TOTAL_TESTS: $test_name"
    
    result=$(eval "$test_command" 2>/dev/null)
    
    if [ "$result" = "$expected_result" ]; then
        echo "PASS: $test_name"
        return 0
    else
        echo "FAIL: $test_name"
        echo "  Expected: $expected_result"
        echo "  Got: $result"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo "Testing Podman API with container: $CONTAINER_NAME"
echo "=================================================="

# Test 1: Health check
run_test "Health check" \
    "curl -s -X GET $API_URL/health | jq -r .status" \
    "healthy"

# Test 2: Create container
echo "Test 2: Creating container"
CREATE_RESULT=$(curl -s -X POST $API_URL/containers \
  -H "Content-Type: application/json" \
  -d "{\"image\": \"alpine:latest\", \"name\": \"$CONTAINER_NAME\", \"command\": \"sleep 300\"}")

CREATE_SUCCESS=$(echo $CREATE_RESULT | jq -r .success 2>/dev/null)
if [ "$CREATE_SUCCESS" = "true" ]; then
    echo "PASS: Container creation"
else
    echo "FAIL: Container creation"
    echo "Response: $CREATE_RESULT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 3: Verify container exists
run_test "Container exists in list" \
    "curl -s -X GET $API_URL/containers | jq -r \".containers[] | select(.name==\\\"$CONTAINER_NAME\\\") | .name\"" \
    "$CONTAINER_NAME"

# Test 4: Add user
echo "Test 4: Adding user"
USER_RESULT=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/users \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass", "shell": "/bin/sh"}')

USER_SUCCESS=$(echo $USER_RESULT | jq -r .success 2>/dev/null)
if [ "$USER_SUCCESS" = "true" ]; then
    echo "PASS: User creation"
else
    echo "FAIL: User creation"
    echo "Response: $USER_RESULT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 5: Verify user exists
echo "Test 5: Verifying user exists"
USER_CHECK=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "grep testuser /etc/passwd"}')

USER_EXIT_CODE=$(echo $USER_CHECK | jq -r .execution.exit_code 2>/dev/null)
if [ "$USER_EXIT_CODE" = "0" ]; then
    echo "PASS: User verification"
else
    echo "FAIL: User verification"
    echo "Response: $USER_CHECK"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 6: Add file
echo "Test 6: Adding file"
FILE_CONTENT="Hello from API test!\nThis file was created via REST API.\nTimestamp: $(date)"
FILE_RESULT=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/files \
  -H "Content-Type: application/json" \
  -d "{\"dest_path\": \"/tmp/test-file.txt\", \"content\": \"$FILE_CONTENT\"}")

FILE_SUCCESS=$(echo $FILE_RESULT | jq -r .success 2>/dev/null)
if [ "$FILE_SUCCESS" = "true" ]; then
    echo "PASS: File creation"
else
    echo "FAIL: File creation"
    echo "Response: $FILE_RESULT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 7: Verify file exists and content
echo "Test 7: Verifying file content"
FILE_CHECK=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "cat /tmp/test-file.txt"}')

FILE_EXIT_CODE=$(echo $FILE_CHECK | jq -r .execution.exit_code 2>/dev/null)
FILE_OUTPUT=$(echo $FILE_CHECK | jq -r .execution.output 2>/dev/null)

if [ "$FILE_EXIT_CODE" = "0" ] && [[ "$FILE_OUTPUT" == *"Hello from API test!"* ]]; then
    echo "PASS: File content verification"
else
    echo "FAIL: File content verification"
    echo "Exit code: $FILE_EXIT_CODE"
    echo "Output: $FILE_OUTPUT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 8: Execute command as specific user
echo "Test 8: Testing command execution as user"
USER_CMD_RESULT=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "whoami", "user": "testuser"}')

USER_CMD_OUTPUT=$(echo $USER_CMD_RESULT | jq -r .execution.output 2>/dev/null)
if [[ "$USER_CMD_OUTPUT" == *"testuser"* ]]; then
    echo "PASS: User command execution"
else
    echo "FAIL: User command execution"
    echo "Expected 'testuser', got: $USER_CMD_OUTPUT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 9: Check logs
echo "Test 9: Checking container logs"
LOGS_RESULT=$(curl -s -X GET "$API_URL/containers/$CONTAINER_NAME/logs?tail=10")
LOGS_SUCCESS=$(echo $LOGS_RESULT | jq -r .success 2>/dev/null)
if [ "$LOGS_SUCCESS" = "true" ]; then
    echo "PASS: Log retrieval"
else
    echo "FAIL: Log retrieval"
    echo "Response: $LOGS_RESULT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 10: Stop container
echo "Test 10: Stopping container"
STOP_RESULT=$(curl -s -X POST $API_URL/containers/$CONTAINER_NAME/stop)
STOP_SUCCESS=$(echo $STOP_RESULT | jq -r .success 2>/dev/null)
if [ "$STOP_SUCCESS" = "true" ]; then
    echo "PASS: Container stop"
else
    echo "FAIL: Container stop"
    echo "Response: $STOP_RESULT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 11: Verify container is stopped
echo "Test 11: Verifying container status"
sleep 2  # Give container time to stop
CONTAINER_STATUS=$(curl -s -X GET $API_URL/containers | jq -r ".containers[] | select(.name==\"$CONTAINER_NAME\") | .status" 2>/dev/null)
if [ "$CONTAINER_STATUS" = "exited" ] || [ "$CONTAINER_STATUS" = "stopped" ]; then
    echo "PASS: Container status verification (status: $CONTAINER_STATUS)"
else
    echo "FAIL: Container status verification"
    echo "Expected 'exited' or 'stopped', got: $CONTAINER_STATUS"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 12: Remove container
echo "Test 12: Removing container"
REMOVE_RESULT=$(curl -s -X DELETE "$API_URL/containers/$CONTAINER_NAME?force=true")
REMOVE_SUCCESS=$(echo $REMOVE_RESULT | jq -r .success 2>/dev/null)
if [ "$REMOVE_SUCCESS" = "true" ]; then
    echo "PASS: Container removal"
else
    echo "FAIL: Container removal"
    echo "Response: $REMOVE_RESULT"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 13: Verify container is gone
echo "Test 13: Verifying container removal"
sleep 1  # Give time for removal
CONTAINER_GONE=$(curl -s -X GET $API_URL/containers | jq -r ".containers[] | select(.name==\"$CONTAINER_NAME\") | .name" 2>/dev/null)
if [ -z "$CONTAINER_GONE" ]; then
    echo "PASS: Container removal verification"
else
    echo "FAIL: Container removal verification"
    echo "Container still exists: $CONTAINER_GONE"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 14: Check metrics
run_test "Metrics retrieval" \
    "curl -s -X GET $API_URL/metrics | jq -r 'if .uptime_seconds >= 0 then \"valid\" else \"invalid\" end'" \
    "valid"

# Summary
echo ""
echo "=================================================="
echo "Test Summary:"
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $((TOTAL_TESTS - FAILED_TESTS))"
echo "Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo "All tests passed successfully!"
    exit 0
else
    echo "Some tests failed. Check the output above for details."
    exit 1
fi
