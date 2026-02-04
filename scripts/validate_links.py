#!/usr/bin/env python3
"""Validate references URLs in Sigma rules."""
import argparse
import sys
import time
from pathlib import Path
from typing import List, Tuple

import requests
import yaml

# Treat these as "transient" / likely WAF / rate-limit issues
TRANSIENT_STATUSES = {403, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524}

DEFAULT_HEADERS = {
    # Browser-ish UA to avoid simplistic bot blocks
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


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


def check_link(session: requests.Session, url: str, timeout: int, retries: int) -> Tuple[bool, str]:
    """
    Returns (ok, message). message is either status code string or error.
    """
    last_msg = ""
    for attempt in range(retries + 1):
        try:
            # HEAD first (cheap)
            r = session.head(url, allow_redirects=True, timeout=timeout)
            # If HEAD is blocked or transient, try GET
            if r.status_code in TRANSIENT_STATUSES or r.status_code == 405:
                r = session.get(url, allow_redirects=True, timeout=timeout)

            if r.status_code < 400:
                return True, str(r.status_code)

            last_msg = str(r.status_code)
        except requests.RequestException as exc:
            last_msg = str(exc)

        # backoff before retry
        if attempt < retries:
            time.sleep(0.8 * (attempt + 1))

    return False, last_msg


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate reference URLs in Sigma rules")
    parser.add_argument("files", nargs="*", help="Optional Sigma rule files or directories")
    parser.add_argument("--timeout", type=int, default=12, help="Request timeout in seconds (default: 12)")
    parser.add_argument("--retries", type=int, default=1, help="Retries for transient failures (default: 1)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on transient statuses (403/429/503/etc). By default these are warnings.",
    )
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
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    all_valid = True
    for link in unique_links:
        ok, msg = check_link(session, link, timeout=args.timeout, retries=args.retries)

        if ok:
            print(f"✓ {link}")
            continue

        # msg might be a status code or exception text
        try:
            status = int(msg)
        except ValueError:
            status = None

        if (status in TRANSIENT_STATUSES) and not args.strict:
            # Warn only (do not fail the run)
            print(f"! {link} -> {msg} (warning: likely transient/WAF/rate-limit)")
            continue

        all_valid = False
        print(f"✗ {link} -> {msg}")

    if not all_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
