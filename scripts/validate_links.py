#!/usr/bin/env python3
"""Validate references URLs in Sigma rules."""
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


def main() -> None:
    repo_root = Path(__file__).parent.parent
    rule_files = list((repo_root / "sigma-rules").rglob("*.yml"))
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
    headers = {"User-Agent": "DetectionAsCode Link Validator"}
    transient_statuses = {429, 503}
    for link in unique_links:
        try:
            response = requests.head(
                link,
                allow_redirects=True,
                timeout=10,
                headers=headers,
            )
            if response.status_code == 405:
                response = requests.get(
                    link,
                    allow_redirects=True,
                    timeout=10,
                    headers=headers,
                )
            if response.status_code in transient_statuses:
                print(f"⚠ {link} -> {response.status_code} (transient)")
                continue
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
