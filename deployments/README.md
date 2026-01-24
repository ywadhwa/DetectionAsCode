# Deployment Mapping

`mapping.json` defines which content packs deploy to which environment/tenant/platform.

## Required secrets

- `SENTINEL_TOKEN`
- `SENTINEL_WORKSPACE_ID`
- `SPLUNK_HOST`
- `SPLUNK_TOKEN`

## Dry-run

Set `dry_run: true` in the mapping or pass `--dry-run` to `scripts/deploy.py`.
