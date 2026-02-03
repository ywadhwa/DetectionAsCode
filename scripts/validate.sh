#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

rule_args=("$@")

echo "Running core validations..."
python scripts/validate_file_naming.py "${rule_args[@]}"
python scripts/validate_sigma_syntax.py "${rule_args[@]}"
python scripts/validate_rule_metadata.py "${rule_args[@]}"
python scripts/validate_detection_quality.py "${rule_args[@]}"
python scripts/validate_schema.py "${rule_args[@]}"
python scripts/validate_links.py "${rule_args[@]}"
python scripts/validate_spelling.py "${rule_args[@]}"
python scripts/validate_repo_structure.py

if git rev-parse --verify origin/main >/dev/null 2>&1; then
  echo "Running versioning validation against ${BASE_REF:-origin/main}..."
  BASE_REF=${BASE_REF:-origin/main} python scripts/validate_versions.py
else
  echo "Skipping versioning validation (origin/main not available)."
fi

echo "Converting Sigma rules..."
if [ "${#rule_args[@]}" -gt 0 ]; then
  for rule_file in "${rule_args[@]}"; do
    python scripts/convert_sigma.py --backend splunk --rule "$rule_file"
    python scripts/convert_sigma.py --backend kql --rule "$rule_file"
  done
else
  python scripts/convert_sigma.py --backend splunk
  python scripts/convert_sigma.py --backend kql
fi

python scripts/validate_queries.py --type splunk --directory output/splunk
python scripts/validate_queries.py --type kql --directory output/kql

if python -m pytest --version >/dev/null 2>&1; then
  python -m pytest -q
else
  echo "Skipping tests (pytest not installed)."
fi

echo "Validation complete."
