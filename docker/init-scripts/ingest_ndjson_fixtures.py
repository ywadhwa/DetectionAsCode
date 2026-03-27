#!/usr/bin/env python3
"""Bulk-ingest ECS/Beats-style NDJSON lines into Elasticsearch (stdlib only)."""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import urllib.error
import urllib.request


def bulk_post(es_url: str, index: str, lines: list[str]) -> dict:
    body_parts: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        body_parts.append(json.dumps({"create": {"_index": index}}))
        body_parts.append(line)
    if not body_parts:
        return {"items": []}
    payload = "\n".join(body_parts) + "\n"
    url = f"{es_url.rstrip('/')}/_bulk"
    req = urllib.request.Request(
        url,
        data=payload.encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/x-ndjson"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest NDJSON fixture files into Elasticsearch")
    parser.add_argument("--es-url", default=os.environ.get("ES_URL", "http://localhost:9200"))
    parser.add_argument("--fixtures-dir", default=os.environ.get("FIXTURES_DIR", "/fixtures"))
    parser.add_argument("--index", default=os.environ.get("ELASTIC_INDEX", "security-events"))
    parser.add_argument("--batch-size", type=int, default=80)
    args = parser.parse_args()

    pattern = os.path.join(args.fixtures_dir, "*.ndjson")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"No *.ndjson files under {args.fixtures_dir!r}; skipping fixture ingest.")
        return 0

    total_ok = 0
    total_err = 0
    for path in files:
        print(f"Ingesting {path} ...")
        batch: list[str] = []
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                batch.append(line)
                if len(batch) >= args.batch_size:
                    try:
                        result = bulk_post(args.es_url, args.index, batch)
                    except urllib.error.HTTPError as e:
                        print(f"HTTP error bulk posting {path}: {e}", file=sys.stderr)
                        try:
                            print(e.read().decode("utf-8", errors="replace")[:2000], file=sys.stderr)
                        except Exception:
                            pass
                        return 1
                    for item in result.get("items", []):
                        op = item.get("create") or item.get("index") or {}
                        st = op.get("status", 0)
                        if st >= 300:
                            total_err += 1
                            err = op.get("error", op)
                            print(f"  bulk item error: {err}", file=sys.stderr)
                        else:
                            total_ok += 1
                    if result.get("errors"):
                        print(f"  bulk reported errors=true for chunk in {path}", file=sys.stderr)
                    batch = []
            if batch:
                try:
                    result = bulk_post(args.es_url, args.index, batch)
                except urllib.error.HTTPError as e:
                    print(f"HTTP error bulk posting final chunk of {path}: {e}", file=sys.stderr)
                    return 1
                for item in result.get("items", []):
                    op = item.get("create") or item.get("index") or {}
                    st = op.get("status", 0)
                    if st >= 300:
                        total_err += 1
                        err = op.get("error", op)
                        print(f"  bulk item error: {err}", file=sys.stderr)
                    else:
                        total_ok += 1

    print(f"Fixture ingest finished: {total_ok} documents indexed, {total_err} errors.")
    return 1 if total_err > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
