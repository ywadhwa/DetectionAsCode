#!/usr/bin/env python3
"""Validate semantic version bumps for detections and content packs."""
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from scripts.lib.versioning import is_version_bumped


def git_show(path: Path, ref: str) -> Optional[str]:
    try:
        return subprocess.check_output(["git", "show", f"{ref}:{path}"], text=True).strip()
    except subprocess.CalledProcessError:
        return None


def load_yaml_text(text: Optional[str]) -> Dict:
    if not text:
        return {}
    return yaml.safe_load(text) or {}


def get_changed_files(base_ref: str) -> List[Path]:
    output = subprocess.check_output(["git", "diff", "--name-only", base_ref], text=True)
    return [Path(line.strip()) for line in output.splitlines() if line.strip()]


def main() -> None:
    base_ref = os.getenv("BASE_REF", "origin/main")
    repo_root = Path(__file__).parent.parent
    changed_files = get_changed_files(base_ref)

    detection_changes = [
        file_path for file_path in changed_files
        if file_path.as_posix().startswith("sigma-rules/") and file_path.suffix in {".yml", ".yaml"} and not file_path.name.endswith(".meta.yml")
    ]

    if not detection_changes:
        print("No detection changes detected")
        return

    all_valid = True
    pack_versions_to_check = set()

    for detection_file in detection_changes:
        current_text = (repo_root / detection_file).read_text(encoding="utf-8")
        current_rule = load_yaml_text(current_text)
        current_version = str(current_rule.get("version", "0.0.0"))

        base_text = git_show(detection_file, base_ref)
        base_rule = load_yaml_text(base_text)
        base_version = str(base_rule.get("version", "0.0.0"))

        if base_text and not is_version_bumped(base_version, current_version):
            all_valid = False
            print(f"✗ {detection_file}: version not bumped ({base_version} -> {current_version})")
        else:
            print(f"✓ {detection_file}: version bumped")

        meta_path = detection_file.with_suffix(".meta.yml")
        if not (repo_root / meta_path).exists():
            all_valid = False
            print(f"✗ {meta_path}: metadata file missing")
            continue
        current_meta_text = (repo_root / meta_path).read_text(encoding="utf-8")
        base_meta_text = git_show(meta_path, base_ref)
        current_meta = load_yaml_text(current_meta_text)
        base_meta = load_yaml_text(base_meta_text)
        current_meta_version = str(current_meta.get("version", "0.0.0"))
        base_meta_version = str(base_meta.get("version", "0.0.0"))

        if base_meta_text and not is_version_bumped(base_meta_version, current_meta_version):
            all_valid = False
            print(f"✗ {meta_path}: version not bumped ({base_meta_version} -> {current_meta_version})")
        else:
            print(f"✓ {meta_path}: version bumped")

        content_pack = current_rule.get("content_pack")
        if content_pack:
            pack_versions_to_check.add(content_pack)

    for pack_name in pack_versions_to_check:
        pack_path = Path("content-packs") / f"{pack_name}.yml"
        if not (repo_root / pack_path).exists():
            all_valid = False
            print(f"✗ {pack_path}: content pack file missing")
            continue
        current_text = (repo_root / pack_path).read_text(encoding="utf-8")
        base_text = git_show(pack_path, base_ref)
        current_pack = load_yaml_text(current_text)
        base_pack = load_yaml_text(base_text)
        current_version = str(current_pack.get("version", "0.0.0"))
        base_version = str(base_pack.get("version", "0.0.0"))

        if base_text and not is_version_bumped(base_version, current_version):
            all_valid = False
            print(f"✗ {pack_path}: version not bumped ({base_version} -> {current_version})")
        else:
            print(f"✓ {pack_path}: version bumped")

    if not all_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
