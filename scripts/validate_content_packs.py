#!/usr/bin/env python3
"""Validate content packs and referenced detections."""
import sys
from pathlib import Path

import yaml


def main() -> None:
    repo_root = Path(__file__).parent.parent
    pack_dir = repo_root / "content-packs"
    if not pack_dir.exists():
        print("content-packs directory missing")
        sys.exit(1)

    all_valid = True
    for pack_file in pack_dir.glob("*.yml"):
        pack = yaml.safe_load(pack_file.read_text(encoding="utf-8")) or {}
        detections = pack.get("detections", []) or []
        missing = [det for det in detections if not (repo_root / det).exists()]
        mismatched = []
        for det in detections:
            det_path = repo_root / det
            if det_path.exists():
                data = yaml.safe_load(det_path.read_text(encoding="utf-8")) or {}
                if data.get("content_pack") != pack.get("name"):
                    mismatched.append(det)
        if missing or mismatched:
            all_valid = False
            print(f"✗ {pack_file}")
            for det in missing:
                print(f"  Missing detection: {det}")
            for det in mismatched:
                print(f"  Detection not mapped to pack: {det}")
        else:
            print(f"✓ {pack_file}")

    if not all_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
