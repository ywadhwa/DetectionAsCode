#!/usr/bin/env python3
"""Test Elasticsearch queries against a local or remote cluster (wrapper around service layer)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dac.backends.elastic import ElasticConfig
from dac.services.backend_tests import run_elastic_tests


def main() -> None:
    """Parse CLI args and run Elasticsearch-backed compile/execute tests."""
    parser = argparse.ArgumentParser(description="Test Elasticsearch queries")
    parser.add_argument("--directory", type=str, default="output/elasticsearch", help="Directory containing Elasticsearch query files")
    parser.add_argument("--host", type=str, default=os.getenv("ELASTIC_HOST", "http://localhost:9200"), help="Elasticsearch host URL")
    parser.add_argument("--index", type=str, default=os.getenv("ELASTIC_INDEX", "dfir-json-*"), help="Elasticsearch index pattern")
    parser.add_argument("--timeout", type=int, default=int(os.getenv("ELASTIC_TIMEOUT", "30")), help="Query timeout in seconds")
    parser.add_argument("--row-limit", type=int, default=int(os.getenv("ELASTIC_ROW_LIMIT", "1000")), help="Max rows returned per query")
    parser.add_argument("--sample-row-limit", type=int, default=int(os.getenv("ELASTIC_SAMPLE_ROWS", "5")), help="Sample rows to include in results")
    parser.add_argument("--api-key", type=str, default=os.getenv("ELASTIC_API_KEY", ""), help="Optional API key for Elastic Cloud")
    parser.add_argument(
        "--mode",
        choices=["compile", "execute", "both"],
        default="execute",
        help="Run mode: compile-only, execute-only, or both (compile then execute)",
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

    config = ElasticConfig(
        host=args.host,
        index=args.index,
        timeout_seconds=args.timeout,
        row_limit=args.row_limit,
        sample_row_limit=args.sample_row_limit,
        api_key=args.api_key or None,
    )

    result = run_elastic_tests(
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

    if args.mode in {"execute", "both"}:
        per_file = result.get("artifacts", {}).get("results", [])
        if per_file:
            print("\nMatch summary (row counts):")
            for entry in per_file:
                query_file = entry.get("query_file", "<unknown>")
                execution = entry.get("stages", {}).get("execution", {})
                row_count = execution.get("row_count", 0)
                status = execution.get("status", "unknown")
                print(f"  - {query_file}: matches={row_count}, status={status}")

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
