# Azure DevOps Quick Start

## Quick Setup Checklist

- [ ] Azure DevOps organization and project created
- [ ] Repository imported/connected to Azure DevOps
- [ ] Pipeline created from `azure-pipelines.yml`
- [ ] Agent pool configured (Windows agent available)
- [ ] Pipeline variables set (KQL credentials if needed)
- [ ] Permissions configured for branch promotion
- [ ] Pipeline tested with a commit

## One-Minute Setup

1. **Import Repository**
   ```
   Azure DevOps → Repos → Import repository → GitHub → Enter repo URL
   ```

2. **Create Pipeline**
   ```
   Pipelines → New pipeline → Azure Repos Git → Select repo → 
   Existing YAML file → Path: /azure-pipelines.yml → Run
   ```

3. **Configure Variables** (if needed)
   ```
   Pipeline → Edit → Variables → Add:
   - KUSTO_CLUSTER (if using KQL testing)
   - KUSTO_DATABASE (if using KQL testing)
   - KUSTO_TOKEN (Secret, if using KQL testing)
   ```

4. **Test Pipeline**
   ```
   Make a commit to develop branch → Pipeline auto-triggers
   ```

## Branch Configuration

The pipeline is configured for:
- **develop**: Development branch (triggers all validation)
- **staging**: Pre-production (includes Splunk/KQL testing)
- **master**: Production (includes all tests)

## Common Commands

### Check Pipeline Status
```bash
# Via Azure DevOps UI
Pipelines → Select pipeline → View runs
```

### Manual Pipeline Trigger
```bash
# Via Azure DevOps UI
Pipelines → Select pipeline → Run pipeline → Select branch → Run
```

### View Pipeline Logs
```bash
# Via Azure DevOps UI
Pipelines → Select run → View logs for each stage
```

## Pipeline Stages

1. **Lint** - Validates Sigma rule syntax and naming
2. **Convert** - Converts Sigma rules to Splunk/KQL queries
3. **Report** - Generates detection quality report
4. **Docs** - Generates documentation
5. **TestSplunk** - Tests Splunk queries (staging/master only)
6. **TestKql** - Tests KQL queries (staging/master only)
7. **Deploy** - Deploys content packs (if configured)
8. **Promote** - Auto-promotes branches (develop→staging, staging→master)

## Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| Pipeline won't start | Check agent pool has available agents |
| Python setup fails | Verify Python 3.11 is available on agent |
| Branch promotion fails | Check Build Service has write permissions |
| Splunk test fails | Verify Splunk is accessible from agent |
| KQL test fails | Check KUSTO_* variables are set correctly |

## Next Steps

See [azure-devops-setup.md](./azure-devops-setup.md) for detailed instructions.
