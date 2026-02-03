#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

echo "Running core validations..."
python scripts/validate_file_naming.py
python scripts/validate_sigma_syntax.py
python scripts/validate_rule_metadata.py
python scripts/validate_detection_quality.py
python scripts/validate_schema.py
python scripts/validate_links.py
python scripts/validate_spelling.py
python scripts/validate_repo_structure.py

if git rev-parse --verify origin/main >/dev/null 2>&1; then
  echo "Running versioning validation against ${BASE_REF:-origin/main}..."
  BASE_REF=${BASE_REF:-origin/main} python scripts/validate_versions.py
else
  echo "Skipping versioning validation (origin/main not available)."
fi

echo "Converting Sigma rules..."
python scripts/convert_sigma.py --backend splunk
python scripts/convert_sigma.py --backend kql

python scripts/validate_queries.py --type splunk --directory output/splunk
python scripts/validate_queries.py --type kql --directory output/kql

if python -m pytest --version >/dev/null 2>&1; then
  python -m pytest -q
else
  echo "Skipping tests (pytest not installed)."
fi

echo "Validation complete."
