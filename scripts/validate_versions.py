#!/usr/bin/env python3
"""Validate semantic version bumps for Sigma detections (no .meta.yml support)."""
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Repo root is one level up from 'scripts'
repo_root = Path(__file__).resolve().parent.parent

# Ensure repo root is on sys.path so local imports work
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from scripts.lib.versioning import is_version_bumped  # type: ignore


def git_show(path: Path, ref: str) -> Optional[str]:
    """Return file content from git ref:path, or None if it doesn't exist."""
    try:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{path.as_posix()}"],
            cwd=str(repo_root),
            text=True,
        )
    except subprocess.CalledProcessError:
        return None


def load_yaml_text(text: Optional[str]) -> Dict:
    if not text:
        return {}
    return yaml.safe_load(text) or {}


def get_changed_files(base_ref: str) -> List[Path]:
    """List files changed vs base_ref."""
    output = subprocess.check_output(
        ["git", "diff", "--name-only", base_ref],
        cwd=str(repo_root),
        text=True,
    )
    return [Path(line.strip()) for line in output.splitlines() if line.strip()]


def main() -> None:
    base_ref = os.getenv("BASE_REF", "origin/main")

    # If base ref doesn't exist locally, skip cleanly (matches your validate.sh behavior)
    try:
        subprocess.check_output(
            ["git", "rev-parse", "--verify", base_ref],
            cwd=str(repo_root),
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print(f"Skipping versioning validation (base ref not available): {base_ref}")
        return

    changed_files = get_changed_files(base_ref)

    # Only consider Sigma rule YAML files under sigma-rules/ (ignore meta files)
    detection_changes = [
        p for p in changed_files
        if p.as_posix().startswith("sigma-rules/")
        and p.suffix.lower() in {".yml", ".yaml"}
        and not p.name.endswith(".meta.yml")
    ]

    if not detection_changes:
        print("No detection changes detected")
        return

    all_valid = True

    for detection_file in detection_changes:
        abs_path = repo_root / detection_file

        # If the file was deleted in working tree, skip (no version to check)
        if not abs_path.exists():
            print(f"! {detection_file}: file missing in working tree (deleted?) — skipping")
            continue

        current_text = abs_path.read_text(encoding="utf-8")
        current_rule = load_yaml_text(current_text)
        current_version = str(current_rule.get("version", "0.0.0"))

        base_text = git_show(detection_file, base_ref)
        base_rule = load_yaml_text(base_text)
        base_version = str(base_rule.get("version", "0.0.0"))

        # Only enforce bump if file existed in base ref
        if base_text and not is_version_bumped(base_version, current_version):
            all_valid = False
            print(f"✗ {detection_file}: version not bumped ({base_version} -> {current_version})")
        else:
            if base_text:
                print(f"✓ {detection_file}: version bumped ({base_version} -> {current_version})")
            else:
                print(f"✓ {detection_file}: new file (no bump required)")

    if not all_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
