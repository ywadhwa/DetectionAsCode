# Branch Strategy and Workflow

This document describes the branch strategy and CI/CD workflow for the Detection as Code pipeline.

## Branch Structure

- **`dev`**: Development branch for active work
- **`staging`**: Pre-production testing and validation
- **`master`**: Production-ready rules and queries

## Workflow: dev → staging → master

### 1. Development (dev branch)

**Purpose**: Active development of new Sigma rules and features

**Workflow**:
- Developers create feature branches from `dev`
- Make changes to Sigma rules
- Create pull request to `dev`
- Pipeline runs on PR:
  - ✅ Lint Sigma rules
  - ✅ Validate file naming
  - ✅ Validate syntax
  - ✅ Convert to queries
  - ✅ Basic query validation

**What runs**:
- All validation checks
- Query generation
- Basic syntax validation

**What doesn't run**:
- Splunk query testing (resource-intensive)

### 2. Staging (staging branch)

**Purpose**: Comprehensive testing before production

**Workflow**:
- Merge `dev` → `staging` when ready for testing
- Pipeline runs automatically on push to `staging`:
  - ✅ All dev branch checks
  - ✅ **Splunk query testing** (Docker-based)
  - ✅ Full validation suite

**What runs**:
- All dev branch checks
- **Splunk instance deployment**
- **Query execution against test data**
- **Result validation**

### 3. Production (master branch)

**Purpose**: Production-ready detection rules

**Workflow**:
- After staging tests pass, promote to `master`
- Can be done via:
  1. **Automatic**: Workflow triggers after successful staging run
  2. **Manual**: Use "Promote to Master" workflow dispatch

**What runs**:
- All validation checks
- Query generation
- Optional: Splunk testing (if configured)

## Pipeline Jobs by Branch

| Job | dev | staging | master |
|-----|-----|---------|--------|
| Lint Sigma Rules | ✅ | ✅ | ✅ |
| Validate File Naming | ✅ | ✅ | ✅ |
| Validate Syntax | ✅ | ✅ | ✅ |
| Convert to Queries | ✅ | ✅ | ✅ |
| Validate Query Syntax | ✅ | ✅ | ✅ |
| Test Splunk Queries | ❌ | ✅ | ✅* |
| Generate Report | ✅ | ✅ | ✅ |

*Optional on master, can be enabled via workflow_dispatch

## Promotion Workflow

### Automatic Promotion

When staging pipeline completes successfully:
1. `promote-to-master.yml` workflow triggers
2. Verifies staging pipeline passed
3. Merges `staging` → `master`
4. Creates release tag

### Manual Promotion

1. Go to Actions → "Promote to Master"
2. Click "Run workflow"
3. Select source branch (staging)
4. Workflow merges and tags release

## File Naming Convention

All Sigma rule files must follow this convention:

```
<category>_<descriptive_name>.yml
```

**Examples**:
- `endpoint_suspicious_powershell.yml`
- `cloud_aws_suspicious_api_activity.yml`
- `macos_suspicious_process_execution.yml`
- `network_suspicious_dns_queries.yml`
- `web_webshell_upload_detection.yml`

**Rules**:
- Category must match directory name
- Descriptive name: lowercase, underscores, numbers
- No consecutive underscores
- Minimum 3 characters in descriptive name

## Best Practices

1. **Always validate locally first**:
   ```bash
   python scripts/validate_file_naming.py
   python scripts/validate_sigma_syntax.py
   ```

2. **Test queries locally** (optional):
   ```bash
   cd docker && docker-compose up -d
   python scripts/test_splunk_queries.py
   ```

3. **Small, focused PRs**: One rule or related rules per PR

4. **Clear commit messages**: Describe what the rule detects

5. **Review before promoting**: Always review staging results before promoting to master

## Troubleshooting

### Staging tests failing
- Check Splunk container logs: `docker-compose logs splunk`
- Verify test data loaded correctly
- Review query syntax errors

### Promotion not triggering
- Ensure staging pipeline completed successfully
- Check workflow_run event permissions
- Verify branch protection rules allow promotion

### File naming errors
- Run validation locally: `python scripts/validate_file_naming.py`
- Follow naming convention exactly
- Ensure category matches directory
