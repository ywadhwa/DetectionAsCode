#!/usr/bin/env python3
"""
Validate Sigma rule file naming conventions.

Naming convention: <category>_<descriptive_name>.yml
Examples:
  - endpoint_suspicious_powershell.yml
  - cloud_aws_suspicious_api_activity.yml
  - macos_suspicious_process_execution.yml
"""
import os
import sys
import re
from pathlib import Path
from typing import List, Tuple

# Valid categories
VALID_CATEGORIES = ['endpoint', 'cloud', 'macos', 'network', 'web']

# Naming pattern: category_descriptive_name.yml
# - Must start with category name
# - Followed by underscore
# - Descriptive name (lowercase, underscores, numbers)
# - Ends with .yml or .yaml
NAMING_PATTERN = re.compile(r'^([a-z]+)_([a-z0-9_]+)\.(yml|yaml)$')

def validate_filename(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate a single file's naming convention.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    filename = file_path.name
    
    # Check if matches pattern
    match = NAMING_PATTERN.match(filename)
    if not match:
        errors.append(
            f"Filename '{filename}' does not match pattern: <category>_<descriptive_name>.yml\n"
            f"  Example: endpoint_suspicious_powershell.yml"
        )
        return False, errors
    
    category = match.group(1)
    descriptive_name = match.group(2)
    
    # Validate category matches directory
    parent_dir = file_path.parent.name
    if category != parent_dir:
        errors.append(
            f"Category '{category}' in filename does not match directory '{parent_dir}'"
        )
    
    # Validate category is valid
    if category not in VALID_CATEGORIES:
        errors.append(
            f"Category '{category}' is not valid. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )
    
    # Validate descriptive name
    if len(descriptive_name) < 3:
        errors.append("Descriptive name must be at least 3 characters long")
    
    if descriptive_name.startswith('_') or descriptive_name.endswith('_'):
        errors.append("Descriptive name cannot start or end with underscore")
    
    if '__' in descriptive_name:
        errors.append("Descriptive name cannot contain consecutive underscores")
    
    return len(errors) == 0, errors

def main():
    """Main validation function."""
    sigma_rules_dir = Path(__file__).parent.parent / "sigma-rules"
    
    if not sigma_rules_dir.exists():
        print(f"Error: {sigma_rules_dir} does not exist")
        sys.exit(1)
    
    rule_files = list(sigma_rules_dir.rglob("*.yml")) + list(sigma_rules_dir.rglob("*.yaml"))
    
    if not rule_files:
        print("No Sigma rule files found")
        sys.exit(0)
    
    print(f"Validating file naming for {len(rule_files)} file(s)...\n")
    
    all_valid = True
    for rule_file in rule_files:
        is_valid, errors = validate_filename(rule_file)
        relative_path = rule_file.relative_to(sigma_rules_dir.parent)
        
        if is_valid:
            print(f"✓ {relative_path}")
        else:
            print(f"✗ {relative_path}")
            for error in errors:
                print(f"  ERROR: {error}")
            all_valid = False
    
    if not all_valid:
        print("\n" + "="*60)
        print("Naming Convention:")
        print("  Format: <category>_<descriptive_name>.yml")
        print("  Examples:")
        print("    - endpoint_suspicious_powershell.yml")
        print("    - cloud_aws_suspicious_api_activity.yml")
        print("    - macos_suspicious_process_execution.yml")
        print("    - network_suspicious_dns_queries.yml")
        print("    - web_webshell_upload_detection.yml")
        print("\nValidation failed!")
        sys.exit(1)
    else:
        print("\nAll file names validated successfully!")

if __name__ == "__main__":
    main()
