# Azure DevOps Pipeline Setup Guide

This guide walks you through connecting your repository to Azure DevOps and creating the CI pipeline.

## Prerequisites

1. An Azure DevOps organization and project
2. Access to create pipelines in the project
3. Repository configured with `azure-pipelines.yml`

## Step 1: Connect Repository to Azure DevOps

1. **Navigate to Azure DevOps**
   - Go to [https://dev.azure.com](https://dev.azure.com)
   - Sign in with your Microsoft account

2. **Create or Select Project**
   - Create a new project or select an existing one

3. **Import Repository**
   - Go to **Repos** → **Files**
   - Click **Import repository**
   - Select **GitHub** and enter the repository URL

## Step 2: Create the Pipeline

1. Go to **Pipelines** → **New pipeline**
2. Select **Existing Azure Pipelines YAML file**
3. Choose `/azure-pipelines.yml` and select the `develop` branch
4. Click **Run**

## Step 3: Configure Variables

Add the following variables if you plan to run KQL validation:

- `KUSTO_CLUSTER`
- `KUSTO_DATABASE`
- `KUSTO_TOKEN`

## Step 4: Validate the Pipeline

1. Make a change on `develop`
2. Push the commit
3. Confirm the pipeline runs and reports success

## Pipeline Overview

| Stage | Branches | Purpose |
|-------|----------|---------|
| Lint | develop, main | Validation, schema checks, unit tests |
| Convert | develop, main | Convert Sigma rules to Splunk/KQL |
| Report | develop, main | Generate validation report |
| Docs | develop, main | Generate documentation |
| TestSplunk | develop, main | Test Splunk queries |
| TestKql | develop, main | Test KQL queries |

## Branch Workflow

- **develop**: Daily work and integration branch
- **main**: Stable release branch

## Next Steps

1. **Customize stages** as needed for your workflow
2. **Add notifications** for pipeline results
3. **Add scheduled triggers** for regular validation

## Additional Resources

- [Azure Pipelines Documentation](https://docs.microsoft.com/en-us/azure/devops/pipelines/)
- [YAML Pipeline Reference](https://docs.microsoft.com/en-us/azure/devops/pipelines/yaml-schema)
- [Agent Pools](https://docs.microsoft.com/en-us/azure/devops/pipelines/agents/pools-queues)
