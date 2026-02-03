#!/usr/bin/env python3
"""Validate references URLs in Sigma rules."""
import argparse
import sys
from pathlib import Path
from typing import List

import requests
import yaml


def extract_links(rule: dict) -> List[str]:
    links = []
    for ref in rule.get("references", []) or []:
        if isinstance(ref, str):
            links.append(ref)
    return links


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
        elif candidate.is_file():
            if candidate.suffix.lower() in {".yml", ".yaml"}:
                files.append(candidate)
        else:
            raise FileNotFoundError(raw)
    return sorted(set(files))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate reference URLs in Sigma rules")
    parser.add_argument("files", nargs="*", help="Optional Sigma rule files or directories")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    try:
        rule_files = collect_rule_files(repo_root, args.files)
    except FileNotFoundError as exc:
        print(f"Error: file or directory not found: {exc}")
        sys.exit(1)
    links: List[str] = []
    for rule_file in rule_files:
        data = yaml.safe_load(rule_file.read_text(encoding="utf-8")) or {}
        links.extend(extract_links(data))

    unique_links = sorted(set(link for link in links if link.startswith("http")))
    if not unique_links:
        print("No links to validate")
        return

    print(f"Validating {len(unique_links)} links...")
    all_valid = True
    for link in unique_links:
        try:
            response = requests.head(link, allow_redirects=True, timeout=10)
            if response.status_code == 405:
                response = requests.get(link, allow_redirects=True, timeout=10)
            if response.status_code >= 400:
                all_valid = False
                print(f"✗ {link} -> {response.status_code}")
            else:
                print(f"✓ {link}")
        except requests.RequestException as exc:
            all_valid = False
            print(f"✗ {link} -> {exc}")

    if not all_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
