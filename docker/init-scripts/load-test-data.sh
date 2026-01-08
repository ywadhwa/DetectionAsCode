#!/bin/sh
# Load test data into Splunk instance

set -e

SPLUNK_HOST="splunk"
SPLUNK_PORT="8089"
SPLUNK_USER="admin"
SPLUNK_PASS="ChangeMe123!"

echo "Waiting for Splunk to be ready..."
sleep 30

# Create index for test data
echo "Creating test index..."
curl -k -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
  "https://${SPLUNK_HOST}:${SPLUNK_PORT}/services/data/indexes" \
  -d name=test_data \
  -d datatype=event

# Load test data using HEC
echo "Loading test data via HEC..."
HEC_URL="http://${SPLUNK_HOST}:8088/services/collector"
HEC_TOKEN="test-token-12345"

# Sample Windows event data
cat <<EOF | curl -k -H "Authorization: Splunk ${HEC_TOKEN}" \
  -H "Content-Type: application/json" \
  "${HEC_URL}" \
  --data-binary @-
{"time": $(date +%s), "event": {"EventCode": 4688, "Image": "C:\\Windows\\System32\\powershell.exe", "CommandLine": "powershell.exe -enc ZQBjAGgAbwAgACIASABlAGwAbABvACIA"}}
{"time": $(date +%s), "event": {"EventCode": 4688, "Image": "C:\\Windows\\System32\\cmd.exe", "CommandLine": "cmd.exe /c dir"}}
{"time": $(date +%s), "event": {"EventCode": 4688, "Image": "C:\\Windows\\System32\\powershell.exe", "CommandLine": "powershell.exe -ExecutionPolicy Bypass -File script.ps1"}}
EOF

# Sample AWS CloudTrail data
cat <<EOF | curl -k -H "Authorization: Splunk ${HEC_TOKEN}" \
  -H "Content-Type: application/json" \
  "${HEC_URL}" \
  --data-binary @-
{"time": $(date +%s), "event": {"eventName": "GetObject", "sourceIPAddress": "203.0.113.1", "userIdentity": {"type": "IAMUser", "userName": "testuser"}}}
{"time": $(date +%s), "event": {"eventName": "PutObject", "sourceIPAddress": "10.0.0.1", "userIdentity": {"type": "IAMUser", "userName": "admin"}}}
EOF

echo "Test data loaded successfully!"
