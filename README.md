# Detection as Code

A Detection as Code (DaC) repository for managing Sigma rules with automated linting, validation, and conversion to Splunk and KQL queries.

## Features

- Sigma rule management organized by category (endpoint, cloud, macOS, network, web)
- File naming validation (`<category>_<name>.yml`)
- Automated linting and syntax checking
- Metadata and detection quality validation (log source coverage, false positives, ATT&CK mappings)
- JSON Schema validation for rules and metadata
- Reference/URL validation and spelling checks for metadata fields
- Query generation for Splunk and KQL
- Docker-based Splunk testing
- Azure Data Explorer (KQL) validation hooks
- Web UI to submit Sigma rules and open pull requests

## Repository Structure

```
DetectionAsCode/
├── sigma-rules/          # Sigma rules by category
├── scripts/              # Validation, conversion, and testing scripts
├── schemas/              # JSON schemas for rules and metadata
├── templates/            # Documentation templates
├── documentation/        # Generated documentation output
├── tests/                # Test fixtures and expected matches
├── docker/               # Splunk testing environment
├── azure-pipelines.yml   # Azure DevOps pipeline definition
├── azure-pipelines/      # Pipeline templates
└── ui/                   # Web UI for rule submissions
```

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Create Sigma Rules

Add rules to category directories following the naming convention: `<category>_<descriptive_name>.yml`

```bash
vim sigma-rules/endpoint/endpoint_suspicious_powershell.yml
```

### Local Validation (pre-push)

Run the full validation suite before pushing to `develop`:

```bash
./scripts/validate.sh
```

### Optional: Splunk Testing

```bash
cd docker
docker-compose up -d
docker-compose --profile init up splunk-init
python scripts/test_splunk_queries.py --expectations tests/expected_matches.yml
docker-compose down
```

### Optional: Azure Data Explorer (KQL) Testing

```bash
export KUSTO_CLUSTER="https://<cluster>.kusto.windows.net"
export KUSTO_DATABASE="detections_test"
export KUSTO_TOKEN="<aad token>"
python scripts/test_kql_queries.py --directory output/kql --expectations tests/expected_matches.yml
```

## CI/CD

CI/CD is handled in **Azure DevOps Pipelines**. The pipeline definition lives in `azure-pipelines.yml`, and reusable templates live under `azure-pipelines/templates/`. Local validation (`./scripts/validate.sh`) is the primary pre-push check.

## Git Workflow (main + develop only)

- **develop**: Daily work and integration branch
- **main**: Stable release branch

### Normal Work

```bash
git checkout develop
git pull origin develop

git add .
git commit -m "Describe your change"

git push origin develop
```

### Release

```bash
git checkout main
git pull origin main

git merge --no-ff develop
git push origin main

git tag -a release-<version> -m "Release <version>"
git push origin release-<version>
```

### Fixes

Use `git revert` on `main` if a rollback is required, then fix forward on `develop`.

## Sigma Rule Format

```yaml
title: Rule Title
id: 12345678-1234-1234-1234-123456789012
status: experimental
description: Description of what this rule detects
references:
    - https://attack.mitre.org/techniques/T1059/
author: Your Name
date: 2024/01/01
tags:
    - attack.execution
    - attack.t1059
logsource:
    product: windows
    category: process_creation
detection:
    selection:
        Image|endswith: '\\powershell.exe'
        CommandLine|contains: '-enc'
    condition: selection
level: high
```

## Categories

- **endpoint**: Windows, Linux, macOS endpoint detections
- **cloud**: AWS, Azure, GCP cloud platform detections
- **macos**: macOS-specific detections
- **network**: Network traffic and protocol detections
- **web**: Web application and server detections

## Resources

- [Sigma Specification](https://github.com/SigmaHQ/sigma)
- [MITRE ATT&CK](https://attack.mitre.org/)
- [Detection-as-Code Architecture](docs/architecture.md)
- [Git Workflow & Branching Strategy](docs/git-workflow.md)
