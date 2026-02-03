# Azure DevOps Pipeline Setup Guide

## Quick Setup (5 Minutes)

### Step 1: Create the Pipeline

1. **Go to Azure DevOps**
   - Navigate to: https://dev.azure.com
   - Sign in and select your organization/project

2. **Create New Pipeline**
   - Click **Pipelines** in the left menu
   - Click **New pipeline**

3. **Select Your Repository**
   - Choose **GitHub** (since you connected via GitHub)
   - If prompted, authorize Azure DevOps
   - Select your repository
   - Click **Continue**

4. **Configure Pipeline**
   - Select **Existing Azure Pipelines YAML file**
   - **Path**: `/azure-pipelines.yml`
   - **Branch**: Select `develop`
   - Click **Continue**

5. **Save and Run**
   - Review the YAML preview
   - Click **Save and run**

---

## Required Variables (Optional)

If you run KQL validation, add these variables:

- `KUSTO_CLUSTER`
- `KUSTO_DATABASE`
- `KUSTO_TOKEN`

---

## Pipeline Stages

| Stage | Branches | Purpose |
|-------|----------|---------|
| **Lint** | develop, main | Validation, schema checks, unit tests |
| **Convert** | develop, main | Convert Sigma rules to SPL/KQL |
| **Report** | develop, main | Generate validation report |
| **Docs** | develop, main | Generate documentation |
| **TestSplunk** | develop, main | Test Splunk queries |
| **TestKql** | develop, main | Test KQL queries |

---

## Branch Workflow

```
develop (integration)
  ↓
[Validation + Conversion + Tests]
  ↓
main (stable)
```

---

## Quick Reference

- **Pipeline File**: `/azure-pipelines.yml`
- **Templates**: `/azure-pipelines/templates/`
- **Branches**: `main`, `develop`
- **Python**: 3.11
- **Agent OS**: Windows (required)

---

## Next Steps

1. **Customize Pipeline**: Modify stage templates as needed
2. **Add Notifications**: Configure email/Slack notifications for pipeline results
3. **Set Up Scheduled Runs**: Add scheduled triggers for regular validation
