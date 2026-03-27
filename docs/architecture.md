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
5. **Service-first execution contracts**
   - Scripts are thin wrappers over reusable services in `dac/services/`.
   - Structured JSON artifacts and conversion manifests support deterministic CI and future orchestration.

## Core components

- **Sigma rules**: Raw detections in `sigma-rules/`.
- **Validation scripts**: `scripts/validate*.py` and `scripts/validate.sh`.
- **Conversion scripts**: `scripts/convert_sigma.py` for SPL, KQL, and Elasticsearch output.
- **Testing utilities**: Splunk + ADX + Elasticsearch testing helpers in `scripts/` and `docker/`.
- **Documentation generator**: Jinja2-driven Markdown output for detections.
- **Service layer**: `dac/services/` for conversion, query validation, backend tests, reporting, artifacts.
- **ADX backend adapter**: `dac/backends/adx.py` for KQL compile/execute with environment-driven auth.
- **Elasticsearch backend adapter**: `dac/backends/elastic.py` for Lucene query compile/execute with environment-driven config.

## Security and scalability considerations

- **Least privilege**: Service connections in Azure DevOps should be scoped to the repo.
- **Branch protection**: Require checks before merge into `main`.
- **Secret management**: Use Azure DevOps variable groups for Splunk and Kusto credentials.
- **Reproducibility**: Test datasets and expected matches are version-controlled under `tests/`.
- **Scalability**: Conversions run in parallel jobs; artifact retention keeps outputs auditable.

## Additional Notes

- See `/ARCHITECTURE.md` for a concise agent-readiness architecture summary.
- See `/docs/agent-readiness.md` for tool-like entry points and artifact contracts.
- See `/docs/adx-integration.md` for ADX auth and KQL compile/execute details.
