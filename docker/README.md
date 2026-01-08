# Splunk Testing Environment

Docker-based Splunk instance for testing generated queries.

## Quick Start

### Start Splunk Instance

```bash
# Start Splunk (this will take a few minutes on first run)
docker-compose up -d

# Wait for Splunk to be ready (check health status)
docker-compose ps

# View logs
docker-compose logs -f splunk
```

### Load Test Data

```bash
# Load test data (runs after Splunk is healthy)
docker-compose --profile init up splunk-init
```

### Access Splunk

- **Web UI**: http://localhost:8000
- **Username**: admin
- **Password**: ChangeMe123!
- **HEC Port**: 8088
- **Management Port**: 8089

### Test Queries

```bash
# Test all queries
python scripts/test_splunk_queries.py

# Test specific query
python scripts/test_splunk_queries.py --query output/splunk/endpoint/example.splunk

# Custom Splunk instance
python scripts/test_splunk_queries.py --host splunk.example.com --port 8089
```

### Stop Splunk

```bash
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

## Configuration

Edit `docker-compose.yml` to customize:
- Splunk password
- HEC token
- Ports
- Test data location

## Test Data

Test data is loaded via HEC (HTTP Event Collector) and includes:
- Windows event logs (PowerShell execution, process creation)
- AWS CloudTrail events
- Sample security events

You can add more test data by modifying `init-scripts/load-test-data.sh`.

## Troubleshooting

### Splunk not starting
- Check logs: `docker-compose logs splunk`
- Ensure ports 8000, 8088, 8089 are not in use
- Wait for health check to pass (can take 2-3 minutes)

### Queries not returning results
- Verify test data was loaded: `docker-compose logs splunk-init`
- Check index exists: Search in Splunk UI for `index=test_data`
- Verify query syntax is correct

### Connection refused
- Ensure Splunk container is running: `docker-compose ps`
- Check firewall settings
- Verify port mappings in docker-compose.yml
