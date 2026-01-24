# Azure DevOps Pipeline Setup Guide

## Quick Setup (5 Minutes)

### Step 1: Create the Pipeline

1. **Go to Azure DevOps**
   - Navigate to: https://dev.azure.com
   - Sign in and select your organization/project

2. **Create New Pipeline**
   - Click **Pipelines** in the left menu
   - Click **New pipeline** (or **Create Pipeline**)

3. **Select Your Repository**
   - Choose **GitHub** (since you connected via GitHub)
   - If prompted, authorize Azure DevOps
   - Select repository: `ywadhwa/DetectionAsCode`
   - Click **Continue**

4. **Configure Pipeline**
   - Select **Existing Azure Pipelines YAML file**
   - **Path**: `/azure-pipelines.yml`
   - **Branch**: Select `develop` or `main`
   - Click **Continue**

5. **Review and Save**
   - Review the YAML preview
   - Click **Save** (or **Save & queue** to run immediately)

---

## Step 2: Configure Agent Pool (Required!)

The pipeline needs a Windows agent. Choose one option:

### Option A: Use Microsoft-Hosted Agents (Easiest - Recommended)

1. Click **Edit** on your pipeline
2. Find the `pool` sections (around line 49-52, 57-60, etc.)
3. Replace each pool configuration from:
   ```yaml
   pool:
     name: $(agentPoolName)
     demands:
       - Agent.OS -equals Windows_NT
   ```
   
   To:
   ```yaml
   pool:
     vmImage: 'windows-latest'
   ```

4. **Save** the pipeline

**OR** update the variable at the top (line 40):
```yaml
variables:
  pythonVersion: '3.11'
  agentPoolName: 'Azure Pipelines'  # Use Microsoft-hosted pool
```

### Option B: Use Self-Hosted Agent

1. Ensure you have a Windows self-hosted agent configured
2. Update line 40 in `azure-pipelines.yml`:
   ```yaml
   agentPoolName: 'YourPoolName'
   ```
3. Agent must have:
   - Python 3.11 installed
   - Git installed
   - Docker (for Splunk testing)

---

## Step 3: Configure Variables (Optional)

Only needed if you want to test KQL queries:

1. **Go to Pipeline Variables**
   - Open your pipeline → Click **Edit** → **Variables**
   - Or: **Pipelines** → **Library** → **Variable groups**

2. **Add KQL Variables** (if using KQL testing):
   - `KUSTO_CLUSTER`: Your cluster URL
     - Example: `https://yourcluster.kusto.windows.net`
   - `KUSTO_DATABASE`: Database name
     - Example: `detections_test`
   - `KUSTO_TOKEN`: Azure AD token
     - **Mark as Secret** (🔒 icon)
     - Get token from Azure Portal or Azure CLI

3. **Splunk Variables** (optional - defaults are in YAML):
   - Defaults work for local Docker testing
   - Override if using remote Splunk instance

---

## Step 4: Configure Permissions (For Branch Promotion)

To enable automatic `develop → main` promotion:

1. **Go to Project Settings**
   - Click **Project Settings** (bottom left)
   - Go to **Repositories**

2. **Set Build Service Permissions**
   - Select your repository
   - Click **Security** tab
   - Find **Build Service** account
   - Set these permissions to **Allow**:
     - ✅ **Contribute**
     - ✅ **Create branch**
     - ✅ **Create tag**

3. **Save** changes

---

## Step 5: Run the Pipeline

### First Run

1. **Manual Run**
   - Go to **Pipelines** → Select your pipeline
   - Click **Run pipeline**
   - Select branch: `develop` or `main`
   - Click **Run**

2. **Monitor Execution**
   - Watch stages execute in real-time
   - Click any stage to see detailed logs
   - Stages will run:
     - ✅ Lint (validates Sigma rules)
     - ✅ Convert (generates queries)
     - ✅ Report (generates report)
     - ✅ Docs (generates documentation)
     - ✅ TestSplunk (tests Splunk queries - on develop/main)
     - ✅ TestKql (tests KQL queries - on develop/main)
     - ✅ Deploy (deploys content packs)
     - ✅ Promote (promotes develop → main after tests pass)

### Automatic Runs

The pipeline automatically triggers on:
- **Commits** to `main` or `develop` branches
- **Pull requests** to `main` or `develop` branches
- **Changes** to:
  - `sigma-rules/**`
  - `scripts/**`
  - `azure-pipelines.yml`
  - Other configured paths

---

## Step 6: Verify It Works

1. **Make a Test Commit**
   ```bash
   git checkout develop
   # Make a small change to a file
   git add .
   git commit -m "Test pipeline"
   git push origin develop
   ```

2. **Check Pipeline**
   - Go to **Pipelines** in Azure DevOps
   - You should see a new run triggered automatically
   - Wait for it to complete

3. **Check Artifacts**
   - After pipeline completes, click on the run
   - Go to **Artifacts** tab
   - Download:
     - `generated-queries` (Splunk/KQL queries)
     - `detection-report` (validation report)
     - `documentation` (generated docs)

---

## Troubleshooting

### ❌ Pipeline won't start
**Problem**: No agents available  
**Solution**: Use Microsoft-hosted agents (Option A in Step 2)

### ❌ Python setup fails
**Problem**: Python not found  
**Solution**: Microsoft-hosted agents have Python pre-installed. If using self-hosted, install Python 3.11

### ❌ Branch promotion fails
**Problem**: Permission denied  
**Solution**: Check Step 4 - ensure Build Service has write permissions

### ❌ Template not found
**Problem**: YAML can't find template files  
**Solution**: Ensure all files in `azure-pipelines/templates/` are committed and pushed

### ❌ Splunk test fails
**Problem**: Can't connect to Splunk  
**Solution**: 
- If using Docker: Ensure Docker is available on agent
- If using remote: Update `splunkHost` parameter
- Check Splunk credentials

### ❌ KQL test fails
**Problem**: KQL authentication fails  
**Solution**: 
- Verify `KUSTO_CLUSTER`, `KUSTO_DATABASE`, `KUSTO_TOKEN` variables are set
- Ensure token is valid and not expired
- Check network connectivity from agent

---

## Pipeline Stages Overview

| Stage | Runs On | Purpose |
|-------|---------|---------|
| **Lint** | All branches | Validates Sigma rule syntax and naming |
| **Convert** | All branches | Converts Sigma rules to Splunk/KQL queries |
| **Report** | All branches | Generates detection quality report |
| **Docs** | All branches | Generates documentation |
| **TestSplunk** | develop, main | Tests Splunk queries against Docker instance |
| **TestKql** | develop, main | Tests KQL queries against Azure Data Explorer |
| **Deploy** | All branches | Deploys content packs (if configured) |
| **Promote** | develop only | Auto-promotes develop → main after tests pass |

---

## Branch Workflow

```
develop (development)
  ↓
  [All validation + Tests]
  ↓
  [Auto-promote if tests pass]
  ↓
main (production)
  ↓
  [All validation + Tests]
```

---

## Quick Reference

- **Pipeline File**: `/azure-pipelines.yml`
- **Templates**: `/azure-pipelines/templates/`
- **Branches**: `main`, `develop`
- **Python**: 3.11
- **Agent OS**: Windows (required)
- **Agent Pool**: `Azure Pipelines` (Microsoft-hosted) or your self-hosted pool

---

## Next Steps

After setup is complete:

1. ✅ **Test the pipeline** with a commit
2. ✅ **Review artifacts** to verify output
3. ✅ **Set up branch policies** (optional)
4. ✅ **Configure notifications** for pipeline results
5. ✅ **Customize stages** as needed

---

## Need Help?

- Check pipeline logs for detailed error messages
- Review [Azure Pipelines documentation](https://docs.microsoft.com/en-us/azure/devops/pipelines/)
- Verify all template files are in the repository
- Ensure agent has required software installed
