#!/usr/bin/env python3
"""Convert Sigma rules to backend queries (CLI wrapper around service layer)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dac.services.conversion import SUPPORTED_BACKENDS, run_conversion


def main() -> None:
    """Parse CLI args and delegate conversion to service function."""
    parser = argparse.ArgumentParser(description="Convert Sigma rules to queries")
    parser.add_argument("--backend", choices=sorted(SUPPORTED_BACKENDS), default="splunk", help="Backend to convert to")
    parser.add_argument("--output", type=str, default="output", help="Output directory (default: output)")
    parser.add_argument(
        "--rule",
        type=str,
        help="Convert a specific rule file OR a directory of rules (relative to repo root or CWD is OK)",
    )
    parser.add_argument(
        "--artifact-output",
        type=str,
        help="Optional path for structured JSON artifact",
    )
    parser.add_argument(
        "--bundle-output",
        type=str,
        help="Optional path for a single conversion bundle (JSON) containing query text and status per rule; suppresses .meta/.error sidecars",
    )
    args = parser.parse_args()

    result = run_conversion(
        backend=args.backend,
        output=args.output,
        rule=args.rule,
        artifact_output=args.artifact_output,
        bundle_output=args.bundle_output,
    )

    metrics = result.get("metrics", {})
    print(f"Backend: {args.backend}")
    print(f"Status : {result.get('status')}")
    print(f"Rules  : {metrics.get('processed_rules', 0)}")
    print(f"Gen    : {metrics.get('generated_count', 0)}")
    print(f"Skip   : {metrics.get('skipped_count', 0)}")
    print(f"Fail   : {metrics.get('failed_count', 0)}")

    if result.get("errors"):
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  - {error}")

    if args.artifact_output:
        print(f"\nResult artifact: {args.artifact_output}")
    elif result.get("artifacts", {}).get("conversion_manifest_path"):
        print(f"\nConversion manifest: {result['artifacts']['conversion_manifest_path']}")
    if args.bundle_output:
        print(f"Conversion bundle: {args.bundle_output}")

    if result.get("status") == "failure":
        sys.exit(1)


if __name__ == "__main__":
    main()
