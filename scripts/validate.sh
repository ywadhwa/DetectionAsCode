#!/usr/bin/env bash
set -euo pipefail # Exit immediately on errors, treat unset variables as errors, and fail pipelines if any command fails

# Set up paths relative to the script location
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
bundle_ts=$(date +%Y%m%d_%H%M%S)

echo "-------------------------------------------------------"
echo "Step 1: Running Core Validations"
echo "-------------------------------------------------------"
python scripts/validate_file_naming.py
python scripts/validate_sigma_syntax.py
python scripts/validate_rule_metadata.py
python scripts/validate_detection_quality.py
python scripts/validate_schema.py
python scripts/validate_links.py
python scripts/validate_spelling.py
python scripts/validate_repo_structure.py

# Versioning check against the main branch
if git rev-parse --verify origin/main >/dev/null 2>&1; then
  echo "Running versioning validation against ${BASE_REF:-origin/main}..."
  BASE_REF=${BASE_REF:-origin/main} python scripts/validate_versions.py
else
  echo "Skipping versioning validation (origin/main not available)."
fi

echo ""
echo "-------------------------------------------------------"
echo "Step 2: Checking for Conversion Targets"
echo "-------------------------------------------------------"

rule_args=("$@")
if [ "${#rule_args[@]}" -gt 0 ]; then
  TARGET_PATHS=("${rule_args[@]}")
else
  TARGET_PATHS=("sigma-rules")
fi

# Global flags to track if any file in the batch needs a backend
ANY_SPLUNK=0
ANY_KQL=0
ANY_ELASTICSEARCH=0

for path in "${TARGET_PATHS[@]}"; do
  [ -e "$path" ] || continue
  if [ -d "$path" ]; then
    mapfile -t FILES < <(find "$path" -type f \( -name "*.yml" -o -name "*.yaml" \))
  else
    FILES=("$path")
  fi

  for f in "${FILES[@]}"; do
    [ -f "$f" ] || continue

    # Check for the conversion_targets key (allowing for some indentation)
    if grep -q "^[[:space:]]*conversion_targets:" "$f"; then
      # Extract the block: starts at key, ends at first line with no leading spaces
      block=$(awk '/^[[:space:]]*conversion_targets:/ {p=1; next} /^[A-Za-z0-9]/ {p=0} p' "$f")
      
      # Set global flags if specific backends are found in the block
      if echo "$block" | grep -Eiq 'splunk'; then
        ANY_SPLUNK=1
      fi
      if echo "$block" | grep -Eiq 'kql'; then
        ANY_KQL=1
      fi
      if echo "$block" | grep -Eiq 'elasticsearch'; then
        ANY_ELASTICSEARCH=1
      fi
    fi
  done
done

# Final execution based on accumulated global flags
if [ "$ANY_SPLUNK" -eq 1 ] || [ "$ANY_KQL" -eq 1 ] || [ "$ANY_ELASTICSEARCH" -eq 1 ]; then
  echo "Verified conversion targets found. Initializing backend processing..."

  if [ "$ANY_SPLUNK" -eq 1 ]; then
    echo "[PROCESSING] >> Running Splunk Conversions..."
    python scripts/convert_sigma.py --backend splunk --bundle-output "output/splunk/splunk_bundle_${bundle_ts}.json"
    python scripts/validate_queries.py --type splunk --directory output/splunk
  fi

  if [ "$ANY_KQL" -eq 1 ]; then
    echo "[PROCESSING] >> Running KQL Conversions..."
    python scripts/convert_sigma.py --backend kql --bundle-output "output/kql/kql_bundle_${bundle_ts}.json"
    python scripts/validate_queries.py --type kql --directory output/kql
  fi

  if [ "$ANY_ELASTICSEARCH" -eq 1 ]; then
    echo "[PROCESSING] >> Running Elasticsearch Conversions..."
    python scripts/convert_sigma.py --backend elasticsearch --bundle-output "output/elasticsearch/elasticsearch_bundle_${bundle_ts}.json"
    python scripts/validate_queries.py --type elasticsearch --directory output/elasticsearch
  fi
else
  echo "Result: No conversion_targets found. Skipping Sigma conversion phase."
fi

echo ""
echo "-------------------------------------------------------"
echo "Step 3: Running Unit Tests"
echo "-------------------------------------------------------"
HAS_GENERATED_QUERIES=0

# Check Splunk output
if [ -d "output/splunk" ] && find "output/splunk" -type f \( -name "*.splunk" -o -name "*.spl" \) -print -quit | grep -q .; then
  HAS_GENERATED_QUERIES=1
fi

# Check KQL output
if [ -d "output/kql" ] && find "output/kql" -type f -name "*.kql" -print -quit | grep -q .; then
  HAS_GENERATED_QUERIES=1
fi

# Check Elasticsearch output
if [ -d "output/elasticsearch" ] && find "output/elasticsearch" -type f -name "*.elasticsearch" -print -quit | grep -q .; then
  HAS_GENERATED_QUERIES=1
fi

if [ "$HAS_GENERATED_QUERIES" -eq 1 ]; then
  if python -m pytest --version >/dev/null 2>&1; then
    python -m pytest -q
  else
    echo "Skipping tests (pytest not installed)."
  fi
else
  echo "Skipping tests (no generated Splunk/KQL queries to validate)."
fi

echo ""
echo "✅ Validation complete."
