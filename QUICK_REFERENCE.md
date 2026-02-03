# Quick Reference Guide

## File Naming Convention

**Format**: `<category>_<descriptive_name>.yml`

**Examples**:
- ✅ `endpoint_suspicious_powershell.yml`
- ✅ `cloud_aws_suspicious_api_activity.yml`
- ❌ `example_rule.yml` (missing category prefix)
- ❌ `endpoint-suspicious-powershell.yml` (use underscores, not hyphens)

## Branch Workflow

```
develop → main
```

1. **Develop** on `develop` branch
2. **Release** to `main` when ready

## Common Commands

### Local Validation

```bash
./scripts/validate.sh
```

### Splunk Testing

```bash
# Start Splunk
cd docker && docker-compose up -d

# Load test data
docker-compose --profile init up splunk-init

# Test queries
python scripts/test_splunk_queries.py

# Stop Splunk
docker-compose down
```

## Workflow Triggers

| Action | Branch | What Runs |
|--------|--------|-----------|
| Push to `develop` | develop | Validation + Query Generation + Tests |
| Push to `main` | main | Validation + Query Generation + Tests |
| PR to `develop` or `main` | - | Validation + Query Generation |

## Troubleshooting

### File naming errors
```bash
python scripts/validate_file_naming.py
```
Fix: Rename file to follow `<category>_<name>.yml` pattern

### Splunk connection errors
```bash
docker-compose ps  # Check if Splunk is running
docker-compose logs splunk  # Check logs
```

### Query conversion failures
- Check Sigma rule syntax: `python scripts/validate_sigma_syntax.py`
- Review error files in `output/*/` directories

## Project Structure

```
DetectionAsCode/
├── sigma-rules/          # Your Sigma rules (organized by category)
├── scripts/              # Validation and conversion scripts
├── docker/               # Splunk testing environment
├── output/               # Generated queries (gitignored)
└── azure-pipelines.yml   # Azure DevOps pipeline definition
```

## Next Steps

1. ✅ File naming validation - **DONE**
2. ✅ Docker Splunk testing - **DONE**
3. ✅ Branch workflow (develop → main) - **DONE**
4. 🚀 Start adding your Sigma rules!
