# Detection as Code Pipeline

A Detection as Code (DaC) pipeline for managing Sigma rules with automated linting, validation, and conversion to Splunk and KQL queries.

## Features

- Sigma rule management organized by category (endpoint, cloud, macOS, network, web)
- File naming validation (`<category>_<name>.yml`)
- Automated linting and syntax checking
- Metadata and detection quality validation (log source coverage, false positives, ATT&CK mappings)
- JSON Schema validation for rules, metadata, content packs, and deployment maps
- Reference/URL validation and spelling checks for metadata fields
- Query generation for Splunk and KQL
- Docker-based Splunk testing
- Azure Data Explorer (KQL) validation hooks
- CI/CD integration with GitHub Actions (dev → staging → master)

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Create Sigma Rules

Add rules to category directories following the naming convention: `<category>_<descriptive_name>.yml`

```bash
# Example
vim sigma-rules/endpoint/endpoint_suspicious_powershell.yml
```

**Naming rules**: Category matches directory, lowercase with underscores, no consecutive underscores.

### Validate & Convert

```bash
# Validate naming and syntax
python scripts/validate_file_naming.py
python scripts/validate_sigma_syntax.py
python scripts/validate_rule_metadata.py
python scripts/validate_detection_quality.py
python scripts/validate_schema.py
python scripts/validate_links.py
python scripts/validate_spelling.py
python scripts/validate_repo_structure.py
python scripts/validate_content_packs.py

# Convert to queries
python scripts/convert_sigma.py --backend splunk
python scripts/convert_sigma.py --backend kql

# Validate generated queries
python scripts/validate_queries.py --type splunk --directory output/splunk
python scripts/validate_queries.py --type kql --directory output/kql
```

### Test with Splunk (Optional)

```bash
cd docker
docker-compose up -d
docker-compose --profile init up splunk-init
python scripts/test_splunk_queries.py --expectations tests/expected_matches.yml
docker-compose down
```

See [Docker README](docker/README.md) for details.

### Test with Azure Data Explorer (Optional)

```bash
export KUSTO_CLUSTER="https://<cluster>.kusto.windows.net"
export KUSTO_DATABASE="detections_test"
export KUSTO_TOKEN="<aad token>"
python scripts/test_kql_queries.py --directory output/kql --expectations tests/expected_matches.yml
```

### Documentation & Changelog Automation

```bash
python scripts/generate_docs.py
python scripts/generate_changelog.py
```

Generated outputs are written to `documentation/` and are deterministic for a given git history.

### Versioning Enforcement

```bash
BASE_REF=origin/main python scripts/validate_versions.py
```

Sigma rules, detection metadata (`*.meta.yml`), and content packs must bump their semantic versions when modified.

### Deployment

```bash
python scripts/build_deploy_matrix.py
python scripts/deploy.py --platform sentinel --content-pack sample-pack --action deploy --dry-run
```

Deployment mapping is configured in `deployments/mapping.json`. Required secrets for deployment are `SENTINEL_TOKEN`, `SENTINEL_WORKSPACE_ID`, `SPLUNK_HOST`, and `SPLUNK_TOKEN`.

### KQL Validation via Kusto.Language (optional)

```bash
python scripts/validate_kql_dotnet.py \
  --kusto-dll /path/to/Kusto.Language.dll \
  --services-dll /path/to/Microsoft.Azure.Sentinel.KustoServices.dll \
  --file-dir output/kql
```

### Release Notes

```bash
python scripts/generate_release_notes.py
```

## GitHub Actions Workflow

**Branch Strategy**: `dev` → `staging` → `master`
- **dev**: Basic validation and query generation
- **staging**: Includes Splunk query testing
- **master**: Production-ready rules

**Workflow Jobs**: Lint rules → Validate naming → Convert queries → Validate queries → Test Splunk (staging/master) → Generate report

**View Results**: Actions tab → Latest run → Download `generated-queries` and `detection-report` artifacts

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
        Image|endswith: '\powershell.exe'
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

## Advanced Usage

```bash
# Convert single rule
python scripts/convert_sigma.py --backend splunk --rule sigma-rules/endpoint/my_rule.yml

# Generate report
python scripts/generate_report.py
```

## Troubleshooting

- **Sigma CLI not found**: `pip install sigmatools`
- **Conversion fails**: Check Sigma syntax, required fields, and review `output/*/` error files
- **Query validation**: Basic checks syntax only; use Splunk SDK or Azure Log Analytics for full validation
- **KQL testing**: Ensure `KUSTO_CLUSTER`, `KUSTO_DATABASE`, and `KUSTO_TOKEN` are configured
- **Schema validation errors**: Review `schemas/` definitions and required metadata fields

## Resources

- [Sigma Specification](https://github.com/SigmaHQ/sigma)
- [MITRE ATT&CK](https://attack.mitre.org/)
- [Detection-as-Code Architecture](docs/architecture.md)
- [Git Workflow & Branching Strategy](docs/git-workflow.md)
- [Branching Workflow Contributor Guide](docs/branching-workflow.md)
