#!/usr/bin/env python3
"""Deploy content packs to supported platforms."""
import argparse
import json
import os
import time
from pathlib import Path
from typing import Dict, List

import requests


def request_with_retry(method: str, url: str, headers: Dict[str, str], payload: Dict, retries: int = 3) -> None:
    for attempt in range(1, retries + 1):
        try:
            response = requests.request(method, url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return
        except requests.RequestException as exc:
            if attempt == retries:
                raise
            wait = 2 ** attempt
            print(f"Retrying after error: {exc} (attempt {attempt}/{retries})")
            time.sleep(wait)


def deploy_sentinel(content_pack: str, action: str, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY-RUN] Sentinel {action} for {content_pack}")
        return
    workspace_id = os.getenv("SENTINEL_WORKSPACE_ID")
    token = os.getenv("SENTINEL_TOKEN")
    if not workspace_id or not token:
        raise RuntimeError("SENTINEL_TOKEN and SENTINEL_WORKSPACE_ID are required")
    url = f"https://management.azure.com/{workspace_id}/providers/Microsoft.SecurityInsights/alertRules?api-version=2023-11-01"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"contentPack": content_pack, "action": action}
    request_with_retry("POST", url, headers, payload)


def deploy_splunk(content_pack: str, action: str, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY-RUN] Splunk {action} for {content_pack}")
        return
    host = os.getenv("SPLUNK_HOST")
    token = os.getenv("SPLUNK_TOKEN")
    if not host or not token:
        raise RuntimeError("SPLUNK_HOST and SPLUNK_TOKEN are required")
    url = f"{host}/services/apps/local"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"name": content_pack, "action": action}
    request_with_retry("POST", url, headers, payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy content packs")
    parser.add_argument("--platform", choices=["sentinel", "splunk"])
    parser.add_argument("--content-pack")
    parser.add_argument("--action", choices=["deploy", "remove"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mapping_path = Path(__file__).parent.parent / "deployments" / "mapping.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    deployments: List[Dict] = mapping.get("deployments", [])

    if args.platform and args.content_pack and args.action:
        deployments = [{
            "platform": args.platform,
            "content_pack": args.content_pack,
            "action": args.action,
            "dry_run": args.dry_run
        }]

    if not deployments:
        print("No deployments defined")
        return

    for item in deployments:
        platform = item["platform"]
        action = item["action"]
        content_pack = item["content_pack"]
        dry_run = item.get("dry_run", False)
        print(f"Deploying {content_pack} to {platform} ({action})")
        if platform == "sentinel":
            deploy_sentinel(content_pack, action, dry_run)
        elif platform == "splunk":
            deploy_splunk(content_pack, action, dry_run)
        else:
            raise ValueError(f"Unsupported platform: {platform}")


if __name__ == "__main__":
    main()
