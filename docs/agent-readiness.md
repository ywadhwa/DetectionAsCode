# Agent Readiness Notes

This repository is now easier to call from an orchestration layer without changing its current CI and CLI workflows.

## Readiness Improvements

- Core logic extracted into importable functions under `dac/`.
- Scripts remain as compatibility wrappers for local and pipeline usage.
- JSON artifacts are produced for major stages, enabling deterministic machine parsing.
- Conversion manifests provide explicit backend output contracts.

## Tool-Like Entry Points

Use these functions from Python automation:

- `dac.services.conversion.run_conversion(...)`
- `dac.services.query_validation.validate_queries(...)`
- `dac.services.backend_tests.run_splunk_tests(...)`
- `dac.services.backend_tests.run_kql_tests(...)`
- `dac.backends.adx.validate_kql_query(...)`
- `dac.backends.adx.run_kql_query(...)`
- `dac.backends.adx.summarize_kql_results(...)`
- `dac.services.artifacts.write_result_artifact(...)`

## Deterministic Outputs

Default artifacts are written to `output/artifacts/`:

- conversion: `conversion-<backend>.json`
- validation: `validation-<backend>.json`
- backend tests: `splunk-testing.json`, `kql-testing.json`
- reporting: `reporting.json`

Conversion also emits run and per-rule manifests (JSON) in output backend folders.

## Backward Compatibility

- Existing script names and default behavior are retained.
- Existing Azure DevOps stage structure is preserved.
- New flags are additive (`--manifest`, `--artifact-output`, KQL auth/mode options).

## Open Decisions

- Confirm final fail/warn policy for ADX compile vs execute outcomes by branch/environment.
- Define a stable cross-stage artifact contract version once pipeline consumers are finalized.
