#!/usr/bin/env python3
"""
Validate detection quality requirements for Sigma rules.
"""
import sys
import yaml
from pathlib import Path
from typing import Dict, List


def validate_quality(rule: Dict[str, object]) -> List[str]:
    errors: List[str] = []

    logsource = rule.get("logsource")
    if not isinstance(logsource, dict):
        errors.append("logsource must be a dictionary")
    else:
        if not logsource.get("product") and not logsource.get("category") and not logsource.get("service"):
            errors.append("logsource must include product, category, or service")

    detection = rule.get("detection")
    if not isinstance(detection, dict):
        errors.append("detection must be a dictionary")
    else:
        selections = [key for key in detection.keys() if key not in {"condition", "timeframe"}]
        if not selections:
            errors.append("detection must include at least one selection block")
        condition = detection.get("condition")
        if not condition:
            errors.append("detection must include a condition")

    falsepositives = rule.get("falsepositives")
    if not falsepositives:
        errors.append("falsepositives must be populated with known benign scenarios")

    tags = rule.get("tags")
    if not tags:
        errors.append("tags must include ATT&CK mappings and detection context")

    return errors


def main() -> None:
    sigma_rules_dir = Path(__file__).parent.parent / "sigma-rules"
    if not sigma_rules_dir.exists():
        print(f"Error: {sigma_rules_dir} does not exist")
        sys.exit(1)

    rule_files = list(sigma_rules_dir.rglob("*.yml")) + list(sigma_rules_dir.rglob("*.yaml"))
    if not rule_files:
        print("No Sigma rule files found")
        sys.exit(0)

    print(f"Validating detection quality for {len(rule_files)} rule(s)...\n")
    all_valid = True

    for rule_file in rule_files:
        with open(rule_file, "r", encoding="utf-8") as handle:
            rule = yaml.safe_load(handle) or {}

        errors = validate_quality(rule)
        relative_path = rule_file.relative_to(sigma_rules_dir.parent)

        if errors:
            print(f"✗ {relative_path}")
            for error in errors:
                print(f"  ERROR: {error}")
            all_valid = False
        else:
            print(f"✓ {relative_path}")

    if not all_valid:
        print("\nDetection quality validation failed!")
        sys.exit(1)

    print("\nDetection quality validated successfully!")


if __name__ == "__main__":
    main()
