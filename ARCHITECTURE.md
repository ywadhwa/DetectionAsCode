# Detection-as-Code Architecture (Agent-Ready Baseline)

This repository remains Detection-as-Code first, with additive service extraction for future orchestration.

## What Changed

- Added a small importable service layer in `dac/services/` for conversion, validation, backend testing, reporting, and artifact writing.
- Added `dac/backends/adx.py` for Azure Data Explorer-backed KQL compile and execution.
- Added `dac/backends/elastic.py` for Elasticsearch-backed Lucene query compile and execution.
- Kept existing scripts in `scripts/` as thin wrappers with compatible CLI behavior.
- Added machine-readable result artifacts under `output/artifacts/`.
- Added JSON conversion manifests to link conversion outputs to downstream validation/testing.

## Script-to-Service Mapping

- `scripts/convert_sigma.py` -> `dac.services.conversion.run_conversion`
- `scripts/validate_queries.py` -> `dac.services.query_validation.validate_queries`
- `scripts/test_splunk_queries.py` -> `dac.services.backend_tests.run_splunk_tests`
- `scripts/test_kql_queries.py` -> `dac.services.backend_tests.run_kql_tests`
- `scripts/test_elastic_queries.py` -> `dac.services.backend_tests.run_elastic_tests`
- `scripts/generate_report.py` -> `dac.services.reporting.generate_report`

## Structured Result Contract

Service operations now emit a consistent shape:

- `status`: `success` or `failure`
- `stage`: conversion, validation, compile, execution, testing, reporting
- `backend`: sigma, splunk, kql, adx, elasticsearch
- `errors` / `warnings`
- `metrics`: durations, row counts, pass/fail counters
- `artifacts`: generated file paths and manifest links
- `context`: runtime execution context (cluster, database, mode, etc.)

## Evolving Areas

- TODO: finalize ADX compile-only semantics once pipeline/runtime contract is stable.
- TODO: finalize exact artifact retention and gating policy in Azure DevOps once branch policies are finalized.
