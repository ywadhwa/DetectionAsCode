# Testing Environment

Docker-based testing environments for validating generated queries against Elasticsearch and Splunk.

## Elasticsearch (Primary)

### Quick Start

```bash
# Start Elasticsearch
docker-compose up -d elasticsearch

# Wait for it to be healthy
docker-compose ps

# Load test data
docker-compose --profile init up elasticsearch-init
```

**Local NDJSON fixtures:** add redacted `*.ndjson` files under `tests/fixtures/` (gitignored). They are mounted into the init container and bulk-ingested when present; see `tests/fixtures/README.md`. If there are no `*.ndjson` files there, small embedded samples are loaded instead (same as CI).

### Access Elasticsearch

- **API**: http://localhost:9200
- **No authentication** (security disabled for testing)

### Test Queries

```bash
# Validate query syntax (compile mode)
python scripts/test_elastic_queries.py --mode compile --directory output/elasticsearch

# Execute queries against test data
python scripts/test_elastic_queries.py \
  --host http://localhost:9200 \
  --index security-events \
  --mode execute \
  --directory output/elasticsearch \
  --expectations tests/expected_matches.yml

# Run both compile and execute
python scripts/test_elastic_queries.py --mode both --directory output/elasticsearch
```

### Test Data

The Elasticsearch test data includes (loaded into `security-events` index):
- Windows process creation events (Sysmon-like)
- DNS query events (including ufile.io queries for detection testing)
- Network connection events
- AWS CloudTrail events
- File creation events

### Stop Elasticsearch

```bash
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

---

## Splunk (Optional)

### Configure Environment

```bash
cp .env.example .env
# Edit .env to set SPLUNK_PASSWORD and SPLUNK_HEC_TOKEN
```

### Start Splunk

```bash
# Start Splunk (uses profile)
docker-compose --profile splunk up -d

# Load test data
docker-compose --profile splunk-init up splunk-init
```

### Access Splunk

- **Web UI**: http://localhost:8000
- **Username**: admin
- **Password**: (set via `SPLUNK_PASSWORD` environment variable)
- **HEC Port**: 8088
- **Management Port**: 8089

### Test Queries

```bash
python scripts/test_splunk_queries.py --expectations tests/expected_matches.yml
```

---

## Troubleshooting

### Elasticsearch not starting
- Check logs: `docker-compose logs elasticsearch`
- Ensure port 9200 is not in use
- Wait for health check (can take 1-2 minutes)

### Queries not returning results
- Verify test data was loaded: `curl http://localhost:9200/security-events/_count`
- Check index mappings: `curl http://localhost:9200/security-events/_mapping`
- Review query syntax matches ECS field names

### Memory issues
- Elasticsearch needs at least 512MB heap
- Adjust `ES_JAVA_OPTS` in docker-compose.yml if needed
