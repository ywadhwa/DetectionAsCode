# Test fixtures (local only)

Place **ECS / Elastic Beats–style NDJSON** exports here (one JSON document per line) for Docker Elasticsearch ingestion.

## Usage

1. Copy your redacted sample files into this directory as `*.ndjson` (for example `sample-sysmon.ndjson`).
2. These files are **gitignored** and are **not** pushed to GitHub.
3. Start Elasticsearch and load data:

   ```bash
   cd docker
   docker compose up -d elasticsearch
   docker compose --profile init up elasticsearch-init
   ```

The init container mounts this directory at `/fixtures`. If **any** `*.ndjson` file is present, only fixture data is loaded (no embedded minimal samples). If the directory has no `*.ndjson` files, the loader falls back to small synthetic documents (used in CI).

## CI

GitHub Actions does not receive ignored files; the pipeline uses the embedded samples automatically.

## Adjusting expectations

If your fixtures do not contain events that match a given Sigma rule’s Elasticsearch query, update `tests/expected_matches.yml` for that rule (for example set `min: 0` or tune counts) so local runs stay green.
