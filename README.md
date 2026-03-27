# Detection as Code

A Detection as Code (DaC) repository for managing Sigma rules with automated linting, validation, and conversion to Splunk and KQL queries.

## Features

- Sigma rule management organized by category (endpoint, cloud, macOS, network, web)
- File naming validation (`<category>_<name>.yml`)
- Automated linting and syntax checking
- Metadata and detection quality validation (log source coverage, false positives, ATT&CK mappings)
- JSON Schema validation for rules and metadata
- Reference/URL validation and spelling checks for metadata fields
- Query generation for Splunk, KQL, and Elasticsearch
- Docker-based Splunk testing
- Azure Data Explorer (KQL) validation hooks
- Elasticsearch (Lucene) query testing against local or remote clusters
- Web UI to submit Sigma rules and open pull requests
- Service-layer modules for importable conversion/validation/testing workflows
- Structured JSON artifacts for CI and future orchestration integration
- Conversion manifests for backend-aware downstream validation and testing

## Repository Structure

```
DetectionAsCode/
├── sigma-rules/          # Sigma rules by category
├── scripts/              # Validation, conversion, and testing scripts
├── dac/                  # Reusable services, backend adapters, result schemas
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

### Local Validation (pre-PR)

Run the full validation suite before opening a PR:

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
export KUSTO_DATABASE="dfir"
# One auth mode:
# export KUSTO_TOKEN="<aad token>"
# or export KUSTO_TENANT_ID / KUSTO_CLIENT_ID / KUSTO_CLIENT_SECRET
# or export KUSTO_USE_MANAGED_IDENTITY=true
python scripts/test_kql_queries.py --mode both --directory output/kql --expectations tests/expected_matches.yml
```

### Optional: Elasticsearch Testing

```bash
export ELASTIC_HOST="http://localhost:9200"
export ELASTIC_INDEX="dfir-json-*"
# Optional for Elastic Cloud:
# export ELASTIC_API_KEY="<base64-encoded-api-key>"
python scripts/test_elastic_queries.py --mode both --directory output/elasticsearch --expectations tests/expected_matches.yml
```

### Structured Artifacts

Major scripts now emit machine-readable JSON artifacts under `output/artifacts/` by default (or `--artifact-output` override), while keeping existing console output and exit code behavior.

### Conversion Manifest

`scripts/convert_sigma.py` now writes a backend conversion manifest (`conversion_manifest.<backend>.json`) and per-rule manifests. Downstream scripts can use `--manifest` to validate/test only generated outputs.

## CI/CD

CI/CD is handled in **Azure DevOps Pipelines**. The pipeline definition lives in `azure-pipelines.yml`, and reusable templates live under `azure-pipelines/templates/`. Local validation (`./scripts/validate.sh`) is the primary pre-PR check.

## Git Workflow

This personal repo uses **one long-lived branch** and **one short-lived branch prefix**:

- **`main`**: the only long-lived branch
- **`dev/*`**: short-lived working branches for detections and tooling

### Scenario A — New Detections (dev/* → main via PR)

**Rule**: Never push detection changes directly to `main`.

```bash
git checkout main
git pull origin main

git checkout -b dev/new-suspicious-powershell
./scripts/validate.sh

git add .
git commit -m "Add suspicious PowerShell detection"

git push origin dev/new-suspicious-powershell
```

Open a PR targeting `main` and include:
- what the detection does
- data sources
- validation performed

### Scenario B — Small Fixes / Typos (direct to main)

Direct commits to `main` are allowed **only** for:
- typos
- comments
- README/docs wording
- non-functional formatting changes

**Commit message prefixes are required:**
- `FIX:` for small functional fixes
- `TYPO:` for documentation or spelling fixes

```bash
git checkout main
git pull origin main

git add .
git commit -m "TYPO: fix README wording"

git push origin main
```

### Scenario C — Infrastructure / Tooling (dev/pipeline-test → main via PR)

All changes to pipelines, scripts, validation tooling, or repo automation **must** use:

- `dev/pipeline-test`

```bash
git checkout main
git pull origin main

git checkout -b dev/pipeline-test
./scripts/validate.sh

git add .
git commit -m "Update validation tooling"

git push origin dev/pipeline-test
```

Open a PR targeting `main`.

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
- [Architecture Summary](ARCHITECTURE.md)
- [Git Workflow & Branching Strategy](docs/git-workflow.md)
- [Agent Readiness Notes](docs/agent-readiness.md)
- [ADX Integration Notes](docs/adx-integration.md)
