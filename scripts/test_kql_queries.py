#!/usr/bin/env python3
"""
Test KQL queries against an Azure Data Explorer (Kusto) cluster.
"""
import argparse
import os
import sys
import time
import yaml
import requests
from pathlib import Path
from typing import Dict, Tuple, Any, Optional


def load_expectations(expectations_file: Path, query_type: str) -> Dict[str, Dict[str, int]]:
    if not expectations_file.exists():
        return {}
    with open(expectations_file, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get(query_type, {}) if isinstance(data, dict) else {}


def execute_kql_query(
    query: str,
    cluster_url: str,
    database: str,
    token: str,
    timeout: int = 30,
) -> Tuple[bool, Dict[str, Any]]:
    try:
        url = f"{cluster_url.rstrip('/')}/v1/rest/query"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "db": database,
            "csl": query,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        primary_results = next(
            (table for table in data.get("tables", []) if table.get("name") == "PrimaryResult"),
            None,
        )
        row_count = len(primary_results.get("rows", [])) if primary_results else 0
        return True, {"rows": row_count, "raw": data}
    except requests.RequestException as exc:
        return False, {"error": str(exc)}


def test_query_file(
    query_file: Path,
    cluster_url: str,
    database: str,
    token: str,
    expectations: Dict[str, Dict[str, int]],
) -> Tuple[bool, Dict[str, Any]]:
    with open(query_file, "r", encoding="utf-8") as handle:
        query = handle.read().strip()
    if not query:
        return False, {"error": "Query file is empty"}

    success, result = execute_kql_query(query, cluster_url, database, token)
    if not success:
        return False, result

    expected = expectations.get(str(query_file)) or expectations.get(query_file.name)
    if expected:
        row_count = result.get("rows", 0)
        min_results = expected.get("min", 0)
        max_results = expected.get("max")
        if row_count < min_results:
            return False, {"error": f"Expected at least {min_results} results, got {row_count}"}
        if max_results is not None and row_count > max_results:
            return False, {"error": f"Expected at most {max_results} results, got {row_count}"}

    return True, result


def main() -> None:
    parser = argparse.ArgumentParser(description="Test KQL queries against ADX")
    parser.add_argument(
        "--directory",
        type=str,
        default="output/kql",
        help="Directory containing KQL query files",
    )
    parser.add_argument(
        "--cluster",
        type=str,
        default=os.getenv("KUSTO_CLUSTER", ""),
        help="Kusto cluster URL (e.g., https://cluster.kusto.windows.net)",
    )
    parser.add_argument(
        "--database",
        type=str,
        default=os.getenv("KUSTO_DATABASE", ""),
        help="Kusto database name",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=os.getenv("KUSTO_TOKEN", ""),
        help="AAD token for Kusto",
    )
    parser.add_argument(
        "--expectations",
        type=str,
        default="tests/expected_matches.yml",
        help="Expectations file for result counts",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Test a specific query file",
    )

    args = parser.parse_args()

    if not args.cluster or not args.database or not args.token:
        print("Error: KUSTO_CLUSTER, KUSTO_DATABASE, and KUSTO_TOKEN are required")
        sys.exit(1)

    query_dir = Path(__file__).parent.parent / args.directory
    expectations_file = Path(__file__).parent.parent / args.expectations
    expectations = load_expectations(expectations_file, "kql")

    if args.query:
        query_files = [Path(args.query)]
    else:
        if not query_dir.exists():
            print(f"Error: {query_dir} does not exist")
            sys.exit(1)
        query_files = [
            f for f in query_dir.rglob("*.kql")
            if not f.name.endswith('.meta') and not f.name.endswith('.error')
        ]

    if not query_files:
        print("No KQL query files found")
        sys.exit(0)

    print(f"Testing {len(query_files)} KQL query file(s) against ADX...\n")
    print(f"Cluster: {args.cluster}")
    print(f"Database: {args.database}\n")

    success_count = 0
    failed_queries = []

    for query_file in query_files:
        relative_path = query_file.relative_to(query_dir) if query_dir.exists() else query_file
        print(f"Testing: {relative_path}...", end=" ")

        success, result = test_query_file(
            query_file,
            args.cluster,
            args.database,
            args.token,
            expectations,
        )

        if success:
            row_count = result.get("rows", 0)
            print(f"✓ (Returned {row_count} rows)")
            success_count += 1
        else:
            error = result.get("error", "Unknown error")
            print(f"✗ ({error})")
            failed_queries.append((relative_path, error))

        time.sleep(0.2)

    print(f"\n{'='*60}")
    print(f"Results: {success_count}/{len(query_files)} queries executed successfully")

    if failed_queries:
        print("\nFailed queries:")
        for query_path, error in failed_queries:
            print(f"  - {query_path}: {error}")
        sys.exit(1)

    print("\nAll queries executed successfully!")


if __name__ == "__main__":
    main()
