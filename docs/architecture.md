# Detection-as-Code Architecture

## High-level architecture

1. **Git repository as source of truth**
   - Sigma rules live under `sigma-rules/` and are updated via pull requests.
   - `main` is the only long-lived branch; all work happens in short-lived `dev/*` branches.

2. **Azure DevOps Pipelines for CI/CD**
   - CI runs linting, schema validation, conversions, and tests in Azure DevOps Pipelines.
   - Local validation remains the primary pre-push check.

3. **Rule conversion and validation**
   - Sigma rules are converted to KQL and SPL using Sigma CLI.
   - Converted queries are validated syntactically and against test environments.

4. **Detection quality governance**
   - Metadata validation ensures rules carry required fields (author, tags, references).
   - Quality gates enforce log source coverage and ATT&CK mappings.

## Core components

- **Sigma rules**: Raw detections in `sigma-rules/`.
- **Validation scripts**: `scripts/validate*.py` and `scripts/validate.sh`.
- **Conversion scripts**: `scripts/convert_sigma.py` for SPL and KQL output.
- **Testing utilities**: Splunk + ADX testing helpers in `scripts/` and `docker/`.
- **Documentation generator**: Jinja2-driven Markdown output for detections.

## Security and scalability considerations

- **Least privilege**: Service connections in Azure DevOps should be scoped to the repo.
- **Branch protection**: Require checks before merge into `main`.
- **Secret management**: Use Azure DevOps variable groups for Splunk and Kusto credentials.
- **Reproducibility**: Test datasets and expected matches are version-controlled under `tests/`.
- **Scalability**: Conversions run in parallel jobs; artifact retention keeps outputs auditable.
