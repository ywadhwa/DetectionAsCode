#!/usr/bin/env python3
"""Validate YAML/JSON files against JSON Schemas."""
import json
import sys
from pathlib import Path
from typing import Iterable, List

import yaml
from jsonschema import Draft202012Validator


def load_schema(schema_path: Path) -> Draft202012Validator:
    with open(schema_path, "r", encoding="utf-8") as handle:
        schema = json.load(handle)
    return Draft202012Validator(schema)


def iter_files(patterns: Iterable[str]) -> List[Path]:
    files: List[Path] = []
    repo_root = Path(__file__).parent.parent
    for pattern in patterns:
        files.extend(repo_root.glob(pattern))
    return sorted(set(files))


def load_data(file_path: Path):
    if file_path.suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    with open(file_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main() -> None:
    config_path = Path(__file__).parent.parent / "config" / "schema_map.yml"
    if not config_path.exists():
        print("schema_map.yml not found")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as handle:
        schema_map = yaml.safe_load(handle) or []

    all_valid = True
    for entry in schema_map:
        schema_path = Path(__file__).parent.parent / entry["schema"]
        validator = load_schema(schema_path)
        files = iter_files(entry.get("paths", []))
        if not files:
            continue
        print(f"Validating {entry['name']} ({len(files)} files)")
        for file_path in files:
            data = load_data(file_path)
            errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
            if errors:
                all_valid = False
                print(f"✗ {file_path}")
                for error in errors:
                    print(f"  ERROR: {error.message}")
            else:
                print(f"✓ {file_path}")

    if not all_valid:
        print("Schema validation failed")
        sys.exit(1)

    print("Schema validation successful")


if __name__ == "__main__":
    main()
