# Azure Pipelines Templates

This directory contains modular Azure Pipelines templates following best practices for maintainability and reusability.

## Structure

```
azure-pipelines/
├── templates/
│   ├── jobs/              # Reusable job templates
│   │   ├── python-setup.yml
│   │   └── install-dependencies.yml
│   └── stages/            # Stage templates
│       ├── lint-stage.yml
│       ├── convert-stage.yml
│       ├── report-stage.yml
│       ├── test-splunk-stage.yml
│       └── promote-branch-stage.yml
└── README.md
```

## Templates

### Job Templates (`templates/jobs/`)

#### `python-setup.yml`
Reusable template for setting up Python environment.

**Parameters:**
- `pythonVersion` (default: '3.11'): Python version to use

#### `install-dependencies.yml`
Reusable template for installing Python dependencies.

**Parameters:**
- `dependencies`: List of Python packages to install

### Stage Templates (`templates/stages/`)

#### `lint-stage.yml`
Lints and validates Sigma rules.

**Parameters:**
- `pythonVersion`: Python version
- `pool`: Agent pool configuration

#### `convert-stage.yml`
Converts Sigma rules to Splunk and KQL queries.

**Parameters:**
- `pythonVersion`: Python version
- `pool`: Agent pool configuration
- `dependsOn`: Previous stage name

#### `report-stage.yml`
Generates detection report from converted queries.

**Parameters:**
- `pythonVersion`: Python version
- `pool`: Agent pool configuration
- `dependsOn`: Previous stage name

#### `test-splunk-stage.yml`
Tests Splunk queries against Docker Splunk instance.

**Parameters:**
- `pythonVersion`: Python version
- `pool`: Agent pool configuration
- `dependsOn`: Previous stage name
- `splunkHost`: Splunk host (default: 'localhost')
- `splunkPort`: Splunk port (default: '8089')
- `splunkUsername`: Splunk username (default: 'admin')
- `splunkPassword`: Splunk password
- `splunkIndex`: Splunk index name (default: 'test_data')

#### `promote-branch-stage.yml`
Automatically promotes code between branches after successful validation.

**Parameters:**
- `sourceBranch`: Source branch to promote from (e.g., 'dev' or 'staging')
- `targetBranch`: Target branch to promote to (e.g., 'staging' or 'master')
- `pool`: Agent pool configuration
- `dependsOn`: Stage name that must succeed before promotion (e.g., 'Report' or 'TestSplunk')

**Behavior:**
- Only runs when pipeline is triggered from `sourceBranch`
- Waits for `dependsOn` stage to succeed
- Merges `sourceBranch` into `targetBranch`
- Creates a promotion tag
- Requires Git credentials with write permissions

## Usage

The main `azure-pipelines.yml` file orchestrates all stages by including these templates. To customize:

1. **Change agent pool**: Update `poolName` parameter in `azure-pipelines.yml`
2. **Modify stage behavior**: Edit the corresponding template file
3. **Add new stages**: Create new template files and include them in the main pipeline

## Branch Promotion Workflow

The pipeline automatically promotes code between branches:

1. **dev → staging**: After `Report` stage succeeds on `dev` branch
   - All validation checks pass
   - Queries generated successfully
   - Report created
   - Automatically merges `dev` into `staging`

2. **staging → master**: After `TestSplunk` stage succeeds on `staging` branch
   - All validation checks pass
   - Splunk queries tested successfully
   - Automatically merges `staging` into `master`

**Requirements for Branch Promotion:**
- Git credentials with write permissions (configured via `persistCredentials: true`)
- Branch protection rules should allow pipeline to push
- No merge conflicts (pipeline will fail if conflicts exist)

**Promotion Tags:**
Each promotion creates a tag: `promote-<targetBranch>-<timestamp>`

## Benefits

- **Maintainability**: Each stage is isolated and easy to modify
- **Reusability**: Job templates can be reused across stages
- **Testability**: Individual stages can be tested independently
- **Readability**: Main pipeline file is clean and shows the flow
- **Flexibility**: Easy to enable/disable stages or modify parameters
- **Automation**: Automatic branch promotion reduces manual intervention
