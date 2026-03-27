# ADX Integration (KQL Compile + Execute)

This repo now supports Azure Data Explorer-backed KQL checks in two modes:

- `compile`: low-impact compile/binding check
- `execute`: run query against dataset
- `both`: compile first, then execute

## Configuration

All ADX settings are environment/CLI driven.

Supported inputs:

- `KUSTO_CLUSTER` or `ADX_CLUSTER_URI`
- `KUSTO_DATABASE` or `ADX_DATABASE` (target can be `dfir`)
- `KUSTO_TOKEN` or `ADX_TOKEN` (optional if using other auth)
- `KUSTO_TENANT_ID` / `AZURE_TENANT_ID`
- `KUSTO_CLIENT_ID` / `AZURE_CLIENT_ID`
- `KUSTO_CLIENT_SECRET` / `AZURE_CLIENT_SECRET`
- `KUSTO_USE_MANAGED_IDENTITY=true|false`
- `KUSTO_QUERY_TIMEOUT` (seconds)
- `KUSTO_ROW_LIMIT`
- `KUSTO_SAMPLE_ROWS`

No credentials are hardcoded in service logic.

## Auth Modes

`dac/backends/adx.py` supports:

- direct bearer token
- AAD client credentials (tenant + client + secret)
- managed identity (IMDS/App Service identity endpoints)

## CLI Usage

```bash
python scripts/test_kql_queries.py \
  --cluster "https://<cluster>.kusto.windows.net" \
  --database "dfir" \
  --mode both \
  --directory output/kql \
  --expectations tests/expected_matches.yml
```

Optional backend-aware flow via manifest:

```bash
python scripts/test_kql_queries.py \
  --manifest output/kql/conversion_manifest.kql.json \
  --mode both
```

## Artifacts

KQL testing writes structured JSON artifacts (default `output/artifacts/kql-testing.json`) with:

- backend and stage outcomes
- cluster/database/mode context
- duration and row counts
- compile/execution failure details
- per-query stage summaries

## Azure DevOps Notes

`azure-pipelines/templates/stages/test-kql-stage.yml` now:

- discovers conversion manifest if present
- runs KQL in `both` mode for compile + execution
- writes `output/artifacts/kql-testing.json`
- publishes KQL artifacts as pipeline artifacts

## Current Limitations

- TODO: replace low-impact compile execution with a dedicated ADX compile API/contract if/when standardized in this project.
