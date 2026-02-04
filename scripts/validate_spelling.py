#!/usr/bin/env python3
"""
Validate that rule version numbers are bumped when rules change compared to a base git ref.

Usage:
  BASE_REF=origin/main python scripts/validate_versions.py
  python scripts/validate_versions.py sigma-rules/endpoint/some_rule.yml
  python scripts/validate_versions.py sigma-rules/endpoint/  # directory
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import yaml

# ---------------------------------------------------------------------------
# Ensure scripts/ is on sys.path so we can import lib.versioning reliably
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.versioning import is_version_bumped  # type: ignore

REPO_ROOT = SCRIPTS_DIR.parent


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------
def run_git(args: List[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def git_exists(ref: str) -> bool:
    try:
        run_git(["rev-parse", "--verify", ref])
        return True
    except Exception:
        return False


def file_in_ref(ref: str, rel_path: str) -> bool:
    try:
        run_git(["cat-file", "-e", f"{ref}:{rel_path}"])
        return True
    except Exception:
        return False


def read_file_from_ref(ref: str, rel_path: str) -> Optional[str]:
    try:
        return run_git(["show", f"{ref}:{rel_path}"])
    except Exception:
        return None


def is_file_modified_vs_ref(ref: str, rel_path: str) -> bool:
    proc = subprocess.run(
        ["git", "diff", "--quiet", ref, "--", rel_path],
        cwd=str(REPO_ROOT),
    )
    if proc.returncode == 0:
        return False
    if proc.returncode == 1:
        return True
    raise RuntimeError(f"git diff failed for {rel_path} vs {ref}")


# ---------------------------------------------------------------------------
# Rule helpers
# ---------------------------------------------------------------------------
def collect_rule_files(repo_root: Path, paths: List[str]) -> List[Path]:
    sigma_rules_dir = repo_root / "sigma-rules"

    if not paths:
        return list(sigma_rules_dir.rglob("*.yml")) + list(sigma_rules_dir.rglob("*.yaml"))

    files: List[Path] = []
    for raw in paths:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()

        if candidate.is_dir():
            files.extend(candidate.rglob("*.yml"))
            files.extend(candidate.rglob("*.yaml"))
        elif candidate.is_file() and candidate.suffix.lower() in {".yml", ".yaml"}:
            files.append(candidate)
        else:
            raise FileNotFoundError(raw)

    return sorted(set(files))


def parse_version(yaml_text: str) -> Optional[str]:
    data = yaml.safe_load(yaml_text) or {}
    v = data.get("version")
    return str(v) if v is not None else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Validate rule version bumps vs base ref")
    parser.add_argument("paths", nargs="*", help="Optional rule files or directories to check")
    args = parser.parse_args()

    base_ref = os.environ.get("BASE_REF", "origin/main")

    if not git_exists(base_ref):
        print(f"Skipping versioning validation: base ref '{base_ref}' not found.")
        sys.exit(0)

    try:
        rule_files = collect_rule_files(REPO_ROOT, args.paths)
    except FileNotFoundError as exc:
        print(f"Error: file or directory not found: {exc}")
        sys.exit(1)

    if not rule_files:
        print("No Sigma rule files found to version-check.")
        sys.exit(0)

    print(f"Validating version bumps against {base_ref} for {len(rule_files)} rule(s)...\n")

    all_valid = True

    for rule_file in rule_files:
        rel_path = str(rule_file.relative_to(REPO_ROOT))

        # New file → no bump required
        if not file_in_ref(base_ref, rel_path):
            print(f"✓ {rel_path} (new file; no bump required)")
            continue

        # Unchanged → no bump required
        try:
            changed = is_file_modified_vs_ref(base_ref, rel_path)
        except Exception as exc:
            all_valid = False
            print(f"✗ {rel_path} -> error checking diff: {exc}")
            continue

        if not changed:
            print(f"✓ {rel_path} (no changes vs {base_ref})")
            continue

        current_text = rule_file.read_text(encoding="utf-8")
        base_text = read_file_from_ref(base_ref, rel_path)

        if base_text is None:
            print(f"! {rel_path} (base content unavailable; skipping)")
            continue

        current_version = parse_version(current_text)
        base_version = parse_version(base_text)

        if current_version is None:
            all_valid = False
            print(f"✗ {rel_path}")
            print("  ERROR: version is missing in current file (required when file changes)")
            continue

        if base_version is None:
            print(f"! {rel_path} (base had no version; current has {current_version})")
            continue

        if not is_version_bumped(base_version, current_version):
            all_valid = False
            print(f"✗ {rel_path}")
            print(
                f"  ERROR: version not bumped "
                f"(base={base_version}, current={current_version})"
            )
        else:
            print(f"✓ {rel_path} (bumped {base_version} -> {current_version})")

    if not all_valid:
        print("\nVersioning validation failed!")
        sys.exit(1)

    print("\nAll versioning checks passed!")


if __name__ == "__main__":
    main()
