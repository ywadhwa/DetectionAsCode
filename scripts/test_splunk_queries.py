#!/usr/bin/env python3
"""Test Splunk queries against a Splunk instance (wrapper around service layer)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import urllib3

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dac.services.backend_tests import run_splunk_tests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main() -> None:
    """Parse CLI args and execute Splunk tests."""
    parser = argparse.ArgumentParser(description="Test Splunk queries")
    parser.add_argument("--directory", type=str, default="output/splunk", help="Directory containing Splunk query files")
    parser.add_argument("--host", type=str, default=os.getenv("SPLUNK_HOST", "localhost"), help="Splunk host")
    parser.add_argument("--port", type=int, default=int(os.getenv("SPLUNK_PORT", "8089")), help="Splunk management port")
    parser.add_argument("--username", type=str, default=os.getenv("SPLUNK_USERNAME", "admin"), help="Splunk username")
    parser.add_argument(
        "--password",
        type=str,
        default=os.getenv("SPLUNK_PASSWORD"),
        help="Splunk password",
    )
    parser.add_argument("--index", type=str, default=os.getenv("SPLUNK_INDEX", "test_data"), help="Splunk index to query")
    parser.add_argument("--query", type=str, help="Test a specific query file")
    parser.add_argument(
        "--expectations",
        type=str,
        default="tests/expected_matches.yml",
        help="Expectations file for result counts",
    )
    parser.add_argument("--manifest", type=str, help="Optional conversion manifest path")
    parser.add_argument("--artifact-output", type=str, help="Optional path for structured JSON artifact")
    args = parser.parse_args()

    result = run_splunk_tests(
        directory=args.directory,
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        index=args.index,
        expectations_path=args.expectations,
        query=args.query,
        manifest=args.manifest,
        artifact_output=args.artifact_output,
    )

    print(f"Status       : {result.get('status')}")
    print(f"Files checked: {result.get('metrics', {}).get('files_checked', 0)}")
    print(f"Passed       : {result.get('metrics', {}).get('passed', 0)}")
    print(f"Failed       : {result.get('metrics', {}).get('failed', 0)}")

    if result.get("errors"):
        print("\nFailed queries:")
        for error in result["errors"]:
            print(f"  - {error}")

    if result.get("status") == "failure":
        sys.exit(1)


if __name__ == "__main__":
    main()
