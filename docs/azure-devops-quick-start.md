# Azure DevOps Quick Start

## Quick Setup Checklist

- [ ] Azure DevOps organization and project created
- [ ] Repository imported/connected to Azure DevOps
- [ ] Pipeline created from `azure-pipelines.yml`
- [ ] Agent pool configured (Windows agent available)
- [ ] Pipeline variables set (KQL credentials if needed)
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
     KUSTO_CLUSTER
     KUSTO_DATABASE
     KUSTO_TOKEN
   ```

## Pipeline Stages

1. **Lint** - Validation, schema checks, and unit tests
2. **Convert** - Convert Sigma rules to Splunk/KQL
3. **Report** - Generate validation report
4. **Docs** - Generate documentation
5. **TestSplunk** - Tests Splunk queries (dev/* and main only)
6. **TestKql** - Tests KQL queries (dev/* and main only)

## Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| Pipeline won't start | Check agent pool has available agents |
| Python setup fails | Verify Python 3.11 is available on agent |
| Splunk test fails | Verify Splunk is accessible from agent |
| KQL test fails | Check KUSTO_* variables are set correctly |

## Next Steps

See [azure-devops-setup.md](./azure-devops-setup.md) for detailed instructions.
