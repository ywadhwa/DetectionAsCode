# Create Azure DevOps Pipeline - Step by Step

Since you've already connected your GitHub repository to Azure DevOps, follow these steps to create the pipeline:

## Step 1: Navigate to Pipelines

1. Go to your Azure DevOps project
2. Click on **Pipelines** in the left sidebar
3. Click **New pipeline** or **Create Pipeline**

## Step 2: Select Repository

1. Choose **GitHub** (since you connected via GitHub)
2. If prompted, authorize Azure DevOps to access your GitHub repositories
3. Select your repository
4. Click **Continue**

## Step 3: Configure Pipeline

1. Select **Existing Azure Pipelines YAML file**
2. In the path field, enter: `/azure-pipelines.yml`
3. Select the branch: `develop` or `main`
4. Click **Continue**

## Step 4: Run and Verify

1. Click **Run**
2. Confirm the pipeline completes successfully
3. Review the stage outputs (Lint, Convert, Report, Docs, TestSplunk, TestKql)

## Troubleshooting

### Pipeline won't start
- **Check**: Agent pool has an available Windows agent
- **Fix**: Ensure the pool is online and permissions are correct

### Python setup fails
- **Check**: Python 3.11 is available
- **Fix**: Use Microsoft-hosted agents or update the pool image

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
- **Branches**: `main`, `develop`
- **Python Version**: 3.11
- **Agent OS**: Windows (required)
