# Create Azure DevOps Pipeline - Step by Step

Since you've already connected your GitHub repository to Azure DevOps, follow these steps to create the pipeline:

## Step 1: Navigate to Pipelines

1. Go to your Azure DevOps project
2. Click on **Pipelines** in the left sidebar
3. Click **New pipeline** or **Create Pipeline**

## Step 2: Select Repository

1. Choose **GitHub** (since you connected via GitHub)
2. If prompted, authorize Azure DevOps to access your GitHub repositories
3. Select your repository: `ywadhwa/DetectionAsCode`
4. Click **Continue**

## Step 3: Configure Pipeline

1. Select **Existing Azure Pipelines YAML file**
2. In the path field, enter: `/azure-pipelines.yml`
3. Select the branch: `develop` or `main` (you can change this later)
4. Click **Continue**

## Step 4: Review Pipeline

1. Review the pipeline YAML that appears
2. You should see all the stages:
   - Lint
   - Convert
   - Report
   - Docs
   - TestSplunk
   - TestKql
   - Deploy
   - Branch Promotion stages

## Step 5: Configure Agent Pool (Important!)

Before running, you need to configure the agent pool:

### Option A: Use Microsoft-Hosted Agents (Recommended for testing)

1. Click **Edit** on the pipeline
2. Find the `pool` sections in the YAML
3. Replace agent pool configuration with:
   ```yaml
   pool:
     vmImage: 'windows-latest'
   ```
4. Or update the variable at the top:
   ```yaml
   variables:
     pythonVersion: '3.11'
     useMicrosoftHosted: true
   ```

### Option B: Use Self-Hosted Agent

1. Ensure you have a Windows self-hosted agent configured
2. Update `agentPoolName: 'Default'` to your actual pool name
3. The agent must have:
   - Python 3.11 installed
   - Git installed
   - Network access to Splunk (if testing)
   - Network access to Azure Data Explorer (if testing KQL)

## Step 6: Configure Variables (Optional but Recommended)

1. Click **Edit** → **Variables** (or go to **Pipelines** → **Library** → **Variable groups**)
2. Add variables if you plan to use KQL testing:
   - `KUSTO_CLUSTER`: Your Azure Data Explorer cluster URL
     - Example: `https://yourcluster.kusto.windows.net`
   - `KUSTO_DATABASE`: Database name
     - Example: `detections_test`
   - `KUSTO_TOKEN`: Azure AD authentication token
     - **Mark as Secret** (🔒 icon)
     - This is required for KQL testing

3. For Splunk testing, default values are in the YAML, but you can override:
   - `SPLUNK_HOST` (default: `localhost`)
   - `SPLUNK_PORT` (default: `8089`)
   - `SPLUNK_USERNAME` (default: `admin`)
   - `SPLUNK_PASSWORD` (mark as Secret)
   - `SPLUNK_INDEX` (default: `test_data`)

## Step 7: Save and Run

1. Click **Save** (or **Save & queue**)
2. If you clicked **Save**, you can run it later by:
   - Going to **Pipelines** → Select your pipeline → **Run pipeline**
3. Select the branch to run on (start with `develop` or `main`)
4. Click **Run**

## Step 8: Monitor Pipeline Execution

1. Watch the pipeline run in real-time
2. Each stage will show:
   - ✅ Green checkmark if successful
   - ❌ Red X if failed
   - ⏸️ Yellow if skipped (due to conditions)

3. Click on any stage to see detailed logs

## Step 9: Configure Permissions for Branch Promotion

For automatic branch promotion to work:

1. Go to **Project Settings** → **Repositories**
2. Select your repository
3. Go to **Security** tab
4. Find **Build Service** (or `[Project Name] Build Service`)
5. Set permissions:
   - **Contribute**: Allow
   - **Create branch**: Allow
   - **Create tag**: Allow
   - **Force push**: Allow (if needed)

## Step 10: Test the Pipeline

1. Make a small commit to the `develop` branch
2. The pipeline should automatically trigger
3. Monitor the execution
4. Check artifacts after completion:
   - Generated queries
   - Reports
   - Documentation

## Troubleshooting

### Pipeline won't start
- **Check**: Agent pool has available agents
- **Fix**: Use Microsoft-hosted agents (`vmImage: 'windows-latest'`)

### Python setup fails
- **Check**: Python 3.11 is available
- **Fix**: Microsoft-hosted agents have Python pre-installed

### Branch promotion fails
- **Check**: Build Service has write permissions
- **Fix**: Configure permissions in Step 9

### Template not found
- **Check**: All template files are in `azure-pipelines/templates/`
- **Fix**: Ensure repository is fully synced

## Next Steps

After the pipeline is created and working:

1. **Set up branch policies** (optional)
2. **Configure notifications** for pipeline results
3. **Add scheduled triggers** for regular validation
4. **Customize stages** as needed for your workflow

## Quick Reference

- **Pipeline YAML**: `/azure-pipelines.yml`
- **Templates**: `/azure-pipelines/templates/`
- **Branches**: `main`, `develop`, `staging`
- **Python Version**: 3.11
- **Agent OS**: Windows (required)
