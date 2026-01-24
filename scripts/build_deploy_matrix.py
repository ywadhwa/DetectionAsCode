#!/usr/bin/env python3
"""Build a deployment matrix from mapping.json."""
import json
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).parent.parent
    mapping_path = repo_root / "deployments" / "mapping.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    matrix = {"include": mapping.get("deployments", [])}
    print(json.dumps(matrix))


if __name__ == "__main__":
    main()
