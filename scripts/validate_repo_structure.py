#!/usr/bin/env python3
"""Validate repository structure and required directories."""
import sys
from pathlib import Path

import yaml


def main() -> None:
    repo_root = Path(__file__).parent.parent
    config_path = repo_root / "config" / "required_dirs.yml"
    required = []
    if config_path.exists():
        required = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        required = required.get("required", [])

    missing = [path for path in required if not (repo_root / path).exists()]
    if missing:
        print("Missing required directories:")
        for entry in missing:
            print(f"- {entry}")
        sys.exit(1)

    print("Repository structure validation successful")


if __name__ == "__main__":
    main()
