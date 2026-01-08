# Detection as Code Pipeline

A comprehensive Detection as Code (DaC) pipeline for managing Sigma rules with automated linting, syntax checking, and conversion to Splunk and KQL queries.

## Features

- ✅ **Sigma Rule Management**: Organize rules by category (endpoint, cloud, macOS, network, web)
- ✅ **File Naming Validation**: Enforces consistent naming convention (`<category>_<name>.yml`)
- ✅ **Automated Linting**: Validate Sigma rule syntax and structure
- ✅ **Query Generation**: Convert Sigma rules to Splunk and KQL queries
- ✅ **Query Validation**: Syntax checking for generated queries
- ✅ **Splunk Testing**: Docker-based Splunk instance for query testing
- ✅ **CI/CD Integration**: GitHub Actions workflow with dev → staging → master flow
- ✅ **Cost-Effective**: Uses GitHub Actions (free for public repos, generous free tier for private)

## Project Structure

```
DetectionAsCode/
├── sigma-rules/          # Sigma rule files organized by category
│   ├── endpoint/         # Endpoint detection rules
│   ├── cloud/            # Cloud detection rules
│   ├── macos/            # macOS-specific rules
│   ├── network/          # Network detection rules
│   └── web/              # Web application rules
├── scripts/              # Automation scripts
│   ├── validate_sigma_syntax.py
│   ├── convert_sigma.py
│   ├── validate_queries.py
│   └── generate_report.py
├── output/               # Generated queries (gitignored)
│   ├── splunk/          # Splunk queries
│   └── kql/             # KQL queries
└── .github/
    └── workflows/
        └── dac-pipeline.yml
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Sigma Rules

Add your Sigma rules to the appropriate category directory following the naming convention:

**Naming Convention**: `<category>_<descriptive_name>.yml`

```bash
# Example: Create an endpoint detection rule
vim sigma-rules/endpoint/endpoint_suspicious_powershell.yml
vim sigma-rules/cloud/cloud_aws_suspicious_api_activity.yml
```

**Important**: File names must follow the pattern `category_descriptive_name.yml` where:
- Category matches the directory name
- Descriptive name is lowercase with underscores
- No consecutive underscores

### 3. Validate Rules Locally

```bash
# Validate file naming convention
python scripts/validate_file_naming.py

# Validate Sigma rule syntax
python scripts/validate_sigma_syntax.py

# Or use sigma CLI directly
sigma lint sigma-rules/**/*.yml
```

### 4. Convert to Queries

```bash
# Convert to Splunk queries
python scripts/convert_sigma.py --backend splunk

# Convert to KQL queries
python scripts/convert_sigma.py --backend kql
```

### 5. Validate Generated Queries

```bash
# Validate Splunk queries
python scripts/validate_queries.py --type splunk --directory output/splunk

# Validate KQL queries
python scripts/validate_queries.py --type kql --directory output/kql
```

### 6. Test Queries Against Splunk (Optional)

```bash
# Start Splunk test environment
cd docker
docker-compose up -d

# Load test data
docker-compose --profile init up splunk-init

# Test queries
python scripts/test_splunk_queries.py

# Stop Splunk
docker-compose down
```

See [Docker README](docker/README.md) for detailed Splunk testing instructions.

## GitHub Actions Workflow

### Branch Strategy

The pipeline follows a **dev → staging → master** workflow:

- **`dev`**: Development branch - basic validation and query generation
- **`staging`**: Testing branch - includes Splunk query testing with Docker
- **`master`**: Production branch - validated and tested rules

See [Branch Strategy Documentation](.github/BRANCH_STRATEGY.md) for details.

### Workflow Triggers

The pipeline automatically runs on:
- Push to `dev`, `staging`, or `master` branches
- Pull requests to any branch
- Manual trigger via `workflow_dispatch`

### Workflow Jobs

1. **Lint Sigma Rules**: Validates all Sigma rule syntax and structure
2. **Validate File Naming**: Ensures consistent naming convention
3. **Convert to Queries**: Generates Splunk and KQL queries from Sigma rules
4. **Validate Queries**: Checks syntax of generated queries
5. **Test Splunk Queries** (staging/master only): Executes queries against Docker Splunk instance
6. **Generate Report**: Creates a summary report of all detections

### Viewing Results

After the workflow runs:
1. Go to the **Actions** tab in your GitHub repository
2. Click on the latest workflow run
3. Download artifacts:
   - `generated-queries`: Contains all Splunk and KQL queries
   - `detection-report`: Summary report in Markdown format

## Sigma Rule Format

Each Sigma rule should follow this structure:

```yaml
title: Rule Title
id: 12345678-1234-1234-1234-123456789012  # UUID format
status: experimental  # or production, deprecated
description: Description of what this rule detects
references:
    - https://attack.mitre.org/techniques/T1059/
author: Your Name
date: 2024/01/01
modified: 2024/01/01
tags:
    - attack.execution
    - attack.t1059
logsource:
    product: windows
    category: process_creation
detection:
    selection:
        Image|endswith: '\powershell.exe'
        CommandLine|contains: '-enc'
    condition: selection
falsepositives:
    - Legitimate administrative scripts
level: high  # informational, low, medium, high, critical
```

## Categories

Organize your rules into these categories:

- **endpoint**: Windows, Linux, macOS endpoint detections
- **cloud**: AWS, Azure, GCP cloud platform detections
- **macos**: macOS-specific detections
- **network**: Network traffic and protocol detections
- **web**: Web application and server detections

## Cost Comparison

### GitHub Actions (Recommended)
- **Public Repos**: Free (unlimited minutes)
- **Private Repos**: 2,000 minutes/month free, then $0.008/minute
- **Best for**: Personal projects, open source

### Azure DevOps Pipelines
- **Public Projects**: Free (unlimited minutes)
- **Private Projects**: 1,800 minutes/month free, then $0.006/minute
- **Best for**: Enterprise environments already using Azure

**Recommendation**: GitHub Actions is more cost-effective for personal use, especially with public repositories.

## Advanced Usage

### Convert Single Rule

```bash
python scripts/convert_sigma.py --backend splunk --rule sigma-rules/endpoint/my_rule.yml
```

### Generate Report

```bash
python scripts/generate_report.py
```

The report will be saved to `output/report.md` with:
- Total rule count
- Rules by category
- Conversion statistics
- Next steps

## Troubleshooting

### Sigma CLI Not Found

```bash
pip install sigmatools
```

### Conversion Fails

1. Check that your Sigma rule syntax is valid
2. Ensure all required fields are present
3. Review error files in `output/*/` directories

### Query Validation Warnings

The basic validation checks syntax only. For full validation:
- **Splunk**: Use Splunk SDK or test in Splunk environment
- **KQL**: Use Azure Log Analytics query validator

## Contributing

1. Create a new branch for your changes
2. Add or modify Sigma rules in appropriate category
3. Test locally before pushing
4. Create a pull request
5. The pipeline will automatically validate your changes

## Resources

- [Sigma Specification](https://github.com/SigmaHQ/sigma)
- [Sigma Rules Repository](https://github.com/SigmaHQ/sigma)
- [MITRE ATT&CK](https://attack.mitre.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## License

This project is for personal use. Adapt as needed for your environment.
