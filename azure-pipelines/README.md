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
│       └── test-splunk-stage.yml
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

## Usage

The main `azure-pipelines.yml` file orchestrates all stages by including these templates. To customize:

1. **Change agent pool**: Update `poolName` parameter in `azure-pipelines.yml`
2. **Modify stage behavior**: Edit the corresponding template file
3. **Add new stages**: Create new template files and include them in the main pipeline

## Benefits

- **Maintainability**: Each stage is isolated and easy to modify
- **Reusability**: Job templates can be reused across stages
- **Testability**: Individual stages can be tested independently
- **Readability**: Main pipeline file is clean and shows the flow
- **Flexibility**: Easy to enable/disable stages or modify parameters
