#!/usr/bin/env python3
"""Validate YAML/JSON files against JSON Schemas."""
import argparse
import fnmatch
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


def filter_files_by_patterns(files: List[Path], patterns: Iterable[str], repo_root: Path) -> List[Path]:
    matched: List[Path] = []
    for file_path in files:
        try:
            relative = file_path.relative_to(repo_root).as_posix()
        except ValueError:
            continue
        if any(fnmatch.fnmatch(relative, pattern) for pattern in patterns):
            matched.append(file_path)
    return matched


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate files against JSON schemas")
    parser.add_argument("files", nargs="*", help="Optional YAML/JSON files or directories")
    args = parser.parse_args()

    config_path = Path(__file__).parent.parent / "config" / "schema_map.yml"
    if not config_path.exists():
        print("schema_map.yml not found")
        sys.exit(1)

    repo_root = Path(__file__).parent.parent
    provided_files: List[Path] = []
    if args.files:
        for raw in args.files:
            candidate = Path(raw)
            if not candidate.is_absolute():
                candidate = (repo_root / candidate).resolve()
            if candidate.is_dir():
                provided_files.extend(candidate.rglob("*.yml"))
                provided_files.extend(candidate.rglob("*.yaml"))
                provided_files.extend(candidate.rglob("*.json"))
            elif candidate.is_file():
                if candidate.suffix.lower() in {".yml", ".yaml", ".json"}:
                    provided_files.append(candidate)
            else:
                print(f"Error: file or directory not found: {raw}")
                sys.exit(1)
        provided_files = sorted(set(provided_files))

    with open(config_path, "r", encoding="utf-8") as handle:
        schema_map = yaml.safe_load(handle) or []

    all_valid = True
    for entry in schema_map:
        schema_path = Path(__file__).parent.parent / entry["schema"]
        validator = load_schema(schema_path)
        patterns = entry.get("paths", [])
        if provided_files:
            files = filter_files_by_patterns(provided_files, patterns, repo_root)
        else:
            files = iter_files(patterns)
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
