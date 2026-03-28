#!/usr/bin/env python3
"""Validate Sigma rule YAML parsing and basic Sigma structure."""
import sys
import yaml
from pathlib import Path
from typing import Any, Dict, List

def validate_sigma_rule(file_path: Path) -> tuple[bool, List[str]]:
    """
    Validate a single Sigma rule file.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            rule = yaml.safe_load(f)

        if not rule:
            return False, ["Rule file is empty"]

        if not isinstance(rule, dict):
            return False, ["Rule file must deserialize to a YAML mapping/object"]

        # Basic Sigma shape checks only. Metadata completeness belongs to
        # validate_rule_metadata.py and detection quality belongs to
        # validate_detection_quality.py.

        # Validate logsource
        if "logsource" in rule:
            logsource = rule["logsource"]
            if not isinstance(logsource, dict):
                errors.append("logsource must be a dictionary")
            else:
                if "category" not in logsource and "product" not in logsource and "service" not in logsource:
                    errors.append("logsource must have either 'category' or 'product'")

        # Validate detection
        if "detection" in rule:
            detection = rule["detection"]
            if not isinstance(detection, dict):
                errors.append("detection must be a dictionary")
            else:
                if "condition" not in detection:
                    errors.append("detection must have 'condition'")
                selection_keys = [key for key in detection.keys() if key not in {"condition", "timeframe"}]
                if not selection_keys:
                    errors.append("detection must include at least one selection block")

        # Validate ID format (should be UUID)
        if "id" in rule:
            rule_id = rule["id"]
            if not isinstance(rule_id, str):
                errors.append("id must be a string")
            elif len(rule_id) != 36 or rule_id.count("-") != 4:
                errors.append(f"id should be a UUID format: {rule_id}")

        return len(errors) == 0, errors

    except yaml.YAMLError as e:
        return False, [f"YAML parsing error: {str(e)}"]
    except Exception as e:
        return False, [f"Error reading file: {str(e)}"]

def main():
    """Main validation function."""
    sigma_rules_dir = Path(__file__).parent.parent / "sigma-rules"

    if not sigma_rules_dir.exists():
        print(f"Error: {sigma_rules_dir} does not exist")
        sys.exit(1)

    all_valid = True
    rule_files = list(sigma_rules_dir.rglob("*.yml")) + list(sigma_rules_dir.rglob("*.yaml"))

    if not rule_files:
        print("No Sigma rule files found")
        sys.exit(0)

    print(f"Validating {len(rule_files)} Sigma rule(s)...\n")

    for rule_file in rule_files:
        is_valid, errors = validate_sigma_rule(rule_file)
        relative_path = rule_file.relative_to(sigma_rules_dir.parent)

        if is_valid:
            print(f"✓ {relative_path}")
        else:
            print(f"✗ {relative_path}")
            for error in errors:
                print(f"  ERROR: {error}")
            all_valid = False

    if not all_valid:
        print("\nValidation failed!")
        sys.exit(1)
    else:
        print("\nAll rules validated successfully!")


if __name__ == "__main__":
    main()
