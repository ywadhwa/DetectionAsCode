#!/usr/bin/env python3
"""Test KQL queries against Azure Data Explorer (wrapper around service layer)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dac.backends.adx import AdxConfig
from dac.services.backend_tests import run_kql_tests


def main() -> None:
    """Parse CLI args and run ADX-backed KQL compile/execute tests."""
    parser = argparse.ArgumentParser(description="Test KQL queries against ADX")
    parser.add_argument("--directory", type=str, default="output/kql", help="Directory containing KQL query files")
    parser.add_argument("--cluster", type=str, default=os.getenv("KUSTO_CLUSTER", os.getenv("ADX_CLUSTER_URI", "")))
    parser.add_argument("--database", type=str, default=os.getenv("KUSTO_DATABASE", os.getenv("ADX_DATABASE", "")))
    parser.add_argument("--token", type=str, default=os.getenv("KUSTO_TOKEN", os.getenv("ADX_TOKEN", "")))
    parser.add_argument("--tenant-id", type=str, default=os.getenv("KUSTO_TENANT_ID", os.getenv("AZURE_TENANT_ID", "")))
    parser.add_argument("--client-id", type=str, default=os.getenv("KUSTO_CLIENT_ID", os.getenv("AZURE_CLIENT_ID", "")))
    parser.add_argument(
        "--client-secret",
        type=str,
        default=os.getenv("KUSTO_CLIENT_SECRET", os.getenv("AZURE_CLIENT_SECRET", "")),
    )
    parser.add_argument(
        "--use-managed-identity",
        action="store_true",
        default=os.getenv("KUSTO_USE_MANAGED_IDENTITY", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument("--timeout", type=int, default=int(os.getenv("KUSTO_QUERY_TIMEOUT", "30")))
    parser.add_argument("--row-limit", type=int, default=int(os.getenv("KUSTO_ROW_LIMIT", "1000")))
    parser.add_argument("--sample-row-limit", type=int, default=int(os.getenv("KUSTO_SAMPLE_ROWS", "5")))
    parser.add_argument(
        "--mode",
        choices=["compile", "execute", "both"],
        default="execute",
        help="KQL run mode: compile-only, execute-only, or both (compile then execute)",
    )
    parser.add_argument(
        "--expectations",
        type=str,
        default="tests/expected_matches.yml",
        help="Expectations file for result counts",
    )
    parser.add_argument("--query", type=str, help="Test a specific query file")
    parser.add_argument("--manifest", type=str, help="Optional conversion manifest path")
    parser.add_argument("--artifact-output", type=str, help="Optional path for structured JSON artifact")
    args = parser.parse_args()

    config = AdxConfig(
        cluster_uri=args.cluster,
        database=args.database,
        tenant_id=args.tenant_id or None,
        client_id=args.client_id or None,
        client_secret=args.client_secret or None,
        token=args.token or None,
        use_managed_identity=bool(args.use_managed_identity),
        timeout_seconds=args.timeout,
        row_limit=args.row_limit,
        sample_row_limit=args.sample_row_limit,
    )

    result = run_kql_tests(
        directory=args.directory,
        expectations_path=args.expectations,
        mode=args.mode,
        query=args.query,
        manifest=args.manifest,
        artifact_output=args.artifact_output,
        config=config,
    )

    print(f"Mode         : {args.mode}")
    print(f"Status       : {result.get('status')}")
    print(f"Files checked: {result.get('metrics', {}).get('files_checked', 0)}")
    print(f"Passed       : {result.get('metrics', {}).get('passed', 0)}")
    print(f"Failed       : {result.get('metrics', {}).get('failed', 0)}")

    if result.get("errors"):
        print("\nFailed queries:")
        for error in result["errors"]:
            print(f"  - {error}")

    if result.get("warnings"):
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")

    if result.get("status") == "failure":
        sys.exit(1)


if __name__ == "__main__":
    main()
