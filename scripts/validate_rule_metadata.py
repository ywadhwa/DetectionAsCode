#!/usr/bin/env python3
"""
Validate Sigma rule metadata fields and tagging conventions.
"""
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

VALID_STATUS = {"stable", "experimental", "test", "deprecated"}
VALID_LEVELS = {"informational", "low", "medium", "high", "critical"}
DATE_PATTERN = re.compile(r"^\d{4}[-/]\d{2}[-/]\d{2}$")
ATTACK_TACTIC_PREFIX = "attack."
ATTACK_TECHNIQUE_PATTERN = re.compile(r"^attack\.t\d{4}(?:\.\d{3})?$", re.IGNORECASE)


def validate_metadata(rule: Dict[str, object]) -> List[str]:
    errors: List[str] = []
    required_fields = [
        "title",
        "id",
        "status",
        "description",
        "author",
        "date",
        "references",
        "tags",
        "conversion_targets",
        "logsource",
        "detection",
        "level",
        "falsepositives",
        "version",
    ]

    for field in required_fields:
        if field not in rule:
            errors.append(f"Missing required metadata field: {field}")

    status = rule.get("status")
    if status and status not in VALID_STATUS:
        errors.append(f"status must be one of: {', '.join(sorted(VALID_STATUS))}")

    level = rule.get("level")
    if level and level not in VALID_LEVELS:
        errors.append(f"level must be one of: {', '.join(sorted(VALID_LEVELS))}")

    date_value = rule.get("date")
    if date_value and not DATE_PATTERN.match(str(date_value)):
        errors.append("date must be in YYYY/MM/DD or YYYY-MM-DD format")

    references = rule.get("references")
    if references is not None and not isinstance(references, list):
        errors.append("references must be a list")

    tags = rule.get("tags")
    if tags is not None:
        if not isinstance(tags, list):
            errors.append("tags must be a list")
        else:
            normalized_tags = [str(tag).lower() for tag in tags]
            if not any(tag.startswith(ATTACK_TACTIC_PREFIX) for tag in normalized_tags):
                errors.append("tags must include at least one attack.* tag")
            if not any(ATTACK_TECHNIQUE_PATTERN.match(tag) for tag in normalized_tags):
                errors.append("tags must include at least one ATT&CK technique tag (attack.t####)")

    falsepositives = rule.get("falsepositives")
    if falsepositives is not None and not isinstance(falsepositives, list):
        errors.append("falsepositives must be a list")

    version = rule.get("version")
    if version and not re.match(r"^\d+\.\d+\.\d+$", str(version)):
        errors.append("version must follow semantic versioning (e.g., 1.2.3)")

    conversion_targets = rule.get("conversion_targets")
    if conversion_targets is not None:
        if not isinstance(conversion_targets, list):
            errors.append("conversion_targets must be a list")
        else:
            invalid = [
                target for target in conversion_targets
                if str(target).lower() not in {"kql", "splunk"}
            ]
            if invalid:
                errors.append("conversion_targets entries must be 'kql' and/or 'splunk'")

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

    print(f"Validating metadata for {len(rule_files)} rule(s)...\n")
    all_valid = True

    for rule_file in rule_files:
        with open(rule_file, "r", encoding="utf-8") as handle:
            rule = yaml.safe_load(handle) or {}

        errors = validate_metadata(rule)
        relative_path = rule_file.relative_to(sigma_rules_dir.parent)

        if errors:
            print(f"✗ {relative_path}")
            for error in errors:
                print(f"  ERROR: {error}")
            all_valid = False
        else:
            print(f"✓ {relative_path}")

    if not all_valid:
        print("\nMetadata validation failed!")
        sys.exit(1)

    print("\nAll metadata validated successfully!")


if __name__ == "__main__":
    main()
