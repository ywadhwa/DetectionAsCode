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
main (long-lived)
↑
PRs from dev/*
```

## Common Commands

### New Detections (dev/*)

```bash
git checkout main
git pull origin main

git checkout -b dev/new-suspicious-powershell
./scripts/validate.sh

git add .
git commit -m "Add suspicious PowerShell detection"

git push origin dev/new-suspicious-powershell
```

### Small Fixes / Typos (direct to main)

```bash
git checkout main
git pull origin main

git add .
git commit -m "TYPO: fix README wording"

git push origin main
```

### Infrastructure / Tooling (dev/pipeline-test)

```bash
git checkout main
git pull origin main

git checkout -b dev/pipeline-test
./scripts/validate.sh

git add .
git commit -m "Update validation tooling"

git push origin dev/pipeline-test
```

## Workflow Triggers

| Action | Branch | What Runs |
|--------|--------|-----------|
| Push to `dev/*` | dev/* | Validation + Query Generation + Tests |
| Push to `main` | main | Validation + Query Generation + Tests |
| PR to `main` | - | Validation + Query Generation |

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
3. ✅ Branch workflow (dev/* → main) - **DONE**
4. 🚀 Start adding your Sigma rules! - **DONE**
