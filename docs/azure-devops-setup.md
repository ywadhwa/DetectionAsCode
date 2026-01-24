# Azure DevOps Pipeline Setup Guide

This guide will walk you through connecting your repository to Azure DevOps and creating the CI/CD pipeline.

## Prerequisites

1. An Azure DevOps organization and project
2. Access to create pipelines in the project
3. Your repository code (already configured with `azure-pipelines.yml`)

## Step 1: Connect Repository to Azure DevOps

### Option A: Import Repository from GitHub

1. **Navigate to Azure DevOps**
   - Go to [https://dev.azure.com](https://dev.azure.com)
   - Sign in with your Microsoft account

2. **Create or Select Project**
   - Create a new project or select an existing one
   - Choose your organization and project

3. **Import Repository**
   - Go to **Repos** → **Files**
   - Click **Import repository**
   - Select **GitHub** as source
   - Authenticate with GitHub (if not already connected)
   - Enter your repository URL: `https://github.com/ywadhwa/DetectionAsCode`
   - Click **Import**

### Option B: Connect Existing Repository

1. **Create New Repository in Azure DevOps**
   - Go to **Repos** → **Files**
   - Click **New repository**
   - Name it (e.g., `DetectionAsCode`)
   - Click **Create**

2. **Push Code to Azure DevOps**
   ```bash
   # Add Azure DevOps remote
   git remote add azure https://dev.azure.com/<org>/<project>/_git/<repo>
   
   # Push your code
   git push azure develop
   git push azure main
   ```

## Step 2: Create the Pipeline

1. **Navigate to Pipelines**
   - In your Azure DevOps project, go to **Pipelines** → **Pipelines**

2. **Create New Pipeline**
   - Click **New pipeline** or **Create Pipeline**

3. **Select Repository**
   - Choose **Azure Repos Git** (or **GitHub** if using GitHub integration)
   - Select your repository
   - Select the branch (start with `develop` or `main`)

4. **Configure Pipeline**
   - Choose **Existing Azure Pipelines YAML file**
   - Select the path: `/azure-pipelines.yml`
   - Click **Continue**

5. **Review and Run**
   - Review the pipeline configuration
   - Click **Run** to create and trigger the pipeline

## Step 3: Configure Pipeline Variables

1. **Go to Pipeline Settings**
   - Open your pipeline
   - Click **Edit** → **Variables** (or go to **Pipelines** → **Library**)

2. **Add Required Variables**

   **For KQL Testing (Optional):**
   - `KUSTO_CLUSTER`: Your Azure Data Explorer cluster URL
     - Example: `https://<cluster>.kusto.windows.net`
   - `KUSTO_DATABASE`: Database name
     - Example: `detections_test`
   - `KUSTO_TOKEN`: Azure AD token for authentication
     - Mark as **Secret** (🔒)

   **For Splunk Testing:**
   - The default values are in `azure-pipelines.yml`, but you can override:
     - `SPLUNK_HOST`: Splunk host (default: `localhost`)
     - `SPLUNK_PORT`: Splunk port (default: `8089`)
     - `SPLUNK_USERNAME`: Splunk username (default: `admin`)
     - `SPLUNK_PASSWORD`: Splunk password (mark as **Secret**)
     - `SPLUNK_INDEX`: Splunk index name (default: `test_data`)

3. **Save Variables**
   - Click **Save** after adding variables

## Step 4: Configure Agent Pool

1. **Check Agent Pool**
   - The pipeline uses `Default` pool by default
   - Go to **Project Settings** → **Agent pools**
   - Ensure you have a Windows agent available (required for this pipeline)

2. **Update Pool Name (if needed)**
   - Edit `azure-pipelines.yml`
   - Change `agentPoolName: 'Default'` to your pool name
   - Or use Microsoft-hosted agents:
     ```yaml
     pool:
       vmImage: 'windows-latest'
     ```

## Step 5: Configure Branch Protection and Permissions

### For Branch Promotion to Work

1. **Enable Pipeline Permissions**
   - Go to **Project Settings** → **Repositories**
   - Select your repository
   - Go to **Security** tab
   - Find **Build Service** account
   - Grant **Contribute** and **Create branch** permissions

2. **Configure Branch Policies (Optional)**
   - Go to **Repos** → **Branches**
   - Select `develop`, `staging`, or `master`
   - Click **...** → **Branch policies**
   - Configure required reviewers and status checks

## Step 6: Test the Pipeline

1. **Trigger Pipeline**
   - Make a commit to `develop` branch
   - Or manually trigger: **Pipelines** → Select pipeline → **Run pipeline**

2. **Monitor Execution**
   - Watch the pipeline run in real-time
   - Check each stage:
     - ✅ **Lint**: Validates Sigma rules
     - ✅ **Convert**: Converts to Splunk/KQL queries
     - ✅ **Report**: Generates detection report
     - ✅ **Docs**: Generates documentation
     - ✅ **TestSplunk**: Tests Splunk queries (staging/master only)
     - ✅ **TestKql**: Tests KQL queries (staging/master only)
     - ✅ **Deploy**: Deploys content packs (if configured)

3. **Review Artifacts**
   - After pipeline completes, download artifacts:
     - Generated queries (`output/splunk`, `output/kql`)
     - Detection reports
     - Documentation

## Step 7: Configure Automatic Branch Promotion (Optional)

The pipeline includes automatic branch promotion:
- `dev` → `staging`: After Report stage succeeds
- `staging` → `master`: After TestSplunk and TestKql stages succeed

**To enable:**
1. Ensure pipeline has write permissions (Step 5)
2. The promotion stages are already configured in `azure-pipelines.yml`
3. They will run automatically when conditions are met

## Troubleshooting

### Pipeline Fails to Start
- **Check agent pool**: Ensure Windows agent is available
- **Check YAML syntax**: Validate `azure-pipelines.yml` syntax
- **Check permissions**: Ensure pipeline has access to repository

### Python Setup Fails
- **Check Python version**: Pipeline uses Python 3.11
- **Check dependencies**: Ensure `requirements.txt` is valid
- **Check agent**: Ensure agent has Python installed

### Branch Promotion Fails
- **Check permissions**: Build service needs write access
- **Check branch protection**: May need to allow pipeline to bypass
- **Check conflicts**: Ensure no merge conflicts exist

### Splunk Testing Fails
- **Check Splunk connection**: Ensure Splunk is accessible from agent
- **Check credentials**: Verify username/password
- **Check Docker**: If using Docker, ensure it's available on agent

### KQL Testing Fails
- **Check variables**: Ensure `KUSTO_CLUSTER`, `KUSTO_DATABASE`, `KUSTO_TOKEN` are set
- **Check token**: Ensure token is valid and not expired
- **Check network**: Ensure agent can reach Azure Data Explorer

## Using Microsoft-Hosted Agents

If you don't have a self-hosted Windows agent, you can use Microsoft-hosted agents:

1. **Update `azure-pipelines.yml`**:
   ```yaml
   variables:
     pythonVersion: '3.11'
     # Use Microsoft-hosted agent
     agentPoolName: 'Azure Pipelines'
   
   # In each stage template parameter, change:
   pool:
     vmImage: 'windows-latest'
   ```

2. **Update stage templates** to use `vmImage` instead of `name`:
   ```yaml
   pool:
     vmImage: 'windows-latest'
   ```

## Next Steps

1. **Customize Pipeline**: Modify stage templates as needed
2. **Add Notifications**: Configure email/Slack notifications for pipeline results
3. **Set Up Scheduled Runs**: Add scheduled triggers for regular validation
4. **Add More Tests**: Extend test stages with additional validation
5. **Configure Deployment**: Set up deployment stages for production

## Additional Resources

- [Azure Pipelines Documentation](https://docs.microsoft.com/en-us/azure/devops/pipelines/)
- [YAML Pipeline Reference](https://docs.microsoft.com/en-us/azure/devops/pipelines/yaml-schema)
- [Agent Pools](https://docs.microsoft.com/en-us/azure/devops/pipelines/agents/pools-queues)
