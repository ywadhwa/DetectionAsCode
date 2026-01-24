# Detection-as-Code Modernization Architecture

## High-level architecture

1. **GitHub as source of truth**
   - Sigma rules live under `sigma-rules/` and are updated via pull requests.
   - GitHub Actions runs the fast-path CI checks on every PR.

2. **Azure DevOps for enterprise validation**
   - Azure Pipelines mirrors the GitHub checks and adds gated integration tests.
   - Pipeline stages support branch promotion from `dev` → `staging` → `master`.

3. **Rule conversion and validation**
   - Sigma rules are converted to KQL and SPL using Sigma CLI.
   - Converted queries are validated syntactically and against test environments.

4. **Detection quality governance**
   - Metadata validation ensures rules carry required fields (author, tags, references).
   - Quality gates enforce log source coverage, false positives, and ATT&CK mappings.

## Repository structure

```
.
├── sigma-rules/                # Sigma rules grouped by category
├── scripts/                    # Validation, conversion, and testing utilities
├── tests/                      # Expected match assertions for CI validation
├── docker/                     # Local Splunk test harness
├── .github/workflows/          # GitHub Actions pipelines
├── azure-pipelines/            # Azure Pipelines templates
├── azure-pipelines.yml         # Main Azure DevOps pipeline
└── ui/                         # Web UI for rule authoring and PR creation
```

## CI/CD pipeline design (GitHub Actions)

**Lint and validation (PR and push)**
- `sigma lint` for schema validation.
- `validate_sigma_syntax.py` for structural checks.
- `validate_file_naming.py` for naming conventions.
- `validate_rule_metadata.py` for required metadata.
- `validate_detection_quality.py` for log source and false positive requirements.

**Conversion & syntax validation**
- `convert_sigma.py` generates KQL/SPL outputs based on `conversion_targets` metadata.
- `validate_queries.py` checks basic syntax integrity for converted queries.

**Integration testing (staging/master)**
- `test_splunk_queries.py` runs SPL against Splunk test data and enforces expected matches.
- `test_kql_queries.py` runs KQL against Azure Data Explorer and enforces expected matches.

## CI/CD pipeline design (Azure Pipelines)

**Stages**
1. **Lint**: Sigma linting, metadata, and quality gates.
2. **Convert**: Rule conversion and syntax checks.
3. **Report**: Detection report generation.
4. **TestSplunk**: Splunk integration tests using seeded test data.
5. **TestKql**: KQL integration tests using a Kusto test cluster.
6. **Promote**: Automated branch promotion once gates pass.

## Tooling choices

- **Sigma CLI**: Industry-standard rule conversion and linting.
- **GitHub Actions**: PR-based CI with artifact retention.
- **Azure Pipelines**: Enterprise-scale validation, approvals, and release controls.
- **Splunk & ADX**: Production-aligned validation environments for SPL and KQL.
- **Documentation generators**: Jinja2-driven Markdown outputs for detections and content packs.

## Security and scalability considerations

- **Least privilege**: GitHub tokens used by the UI should be scoped to repo-only permissions.
- **Branch protection**: Require CI checks before merge into `staging` or `master`.
- **Secret management**: Use GitHub/Azure secret stores for Splunk and Kusto credentials.
- **Segregated environments**: `dev`, `staging`, and `master` branches map to separate detection deployments.
- **Reproducibility**: Test datasets and expected matches are version-controlled under `tests/`.
- **Scalability**: Conversions run in parallel jobs; artifact retention keeps query outputs auditable.
