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
│       ├── docs-stage.yml
│       ├── test-splunk-stage.yml
│       └── test-kql-stage.yml
└── README.md
```

## Templates

### Job Templates (`templates/jobs/`)

#### `python-setup.yml`
Reusable template for setting up Python environment.

**Parameters:**
- `pythonVersion` (default: `3.11`)

#### `install-dependencies.yml`
Reusable template for installing Python dependencies.

**Parameters:**
- `dependencies` (list of pip packages)

### Stage Templates (`templates/stages/`)

#### `lint-stage.yml`
Runs validation scripts and unit tests.

#### `convert-stage.yml`
Converts Sigma rules to SPL and KQL and validates syntax.

#### `report-stage.yml`
Generates a summary report and publishes artifacts.

#### `docs-stage.yml`
Generates documentation and publishes artifacts.

#### `test-splunk-stage.yml`
Runs Splunk query tests for `dev/*` and `main`.

#### `test-kql-stage.yml`
Runs KQL query tests for `dev/*` and `main`.

## Benefits

- **Maintainability**: Each stage is isolated and easy to modify
- **Reusability**: Job templates can be reused across stages
- **Testability**: Individual stages can be tested independently
- **Readability**: Main pipeline file is clean and shows the flow
- **Flexibility**: Easy to enable/disable stages or modify parameters
