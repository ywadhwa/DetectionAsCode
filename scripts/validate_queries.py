#!/usr/bin/env python3
"""Validate Splunk, KQL, and Elasticsearch query syntax (CLI wrapper around service layer)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dac.services.query_validation import validate_queries


def main() -> None:
    """Parse CLI args and run query validation."""
    parser = argparse.ArgumentParser(description="Validate query syntax")
    parser.add_argument(
        "--type",
        choices=["splunk", "kql", "elasticsearch"],
        required=True,
        help="Type of queries to validate",
    )
    parser.add_argument("--directory", type=str, required=True, help="Directory containing query files")
    parser.add_argument(
        "--manifest",
        type=str,
        help="Optional conversion manifest path; validates only generated outputs for this backend",
    )
    parser.add_argument("--artifact-output", type=str, help="Optional path for structured JSON artifact")
    args = parser.parse_args()

    result = validate_queries(
        query_type=args.type,
        directory=args.directory,
        manifest=args.manifest,
        artifact_output=args.artifact_output,
    )

    print(f"Validation type : {args.type}")
    print(f"Status          : {result.get('status')}")
    print(f"Files checked   : {result.get('metrics', {}).get('files_checked', 0)}")
    print(f"Failed files    : {result.get('metrics', {}).get('failed_files', 0)}")

    if result.get("warnings"):
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")

    if result.get("errors"):
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  - {error}")

    if result.get("status") == "failure":
        sys.exit(1)


if __name__ == "__main__":
    main()
