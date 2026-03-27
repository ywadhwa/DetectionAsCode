#!/usr/bin/env python3
"""Generate DaC report (wrapper around service layer)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dac.services.reporting import generate_report


def main() -> None:
    """Parse CLI args and generate report artifact."""
    parser = argparse.ArgumentParser(description="Generate a Detection-as-Code report")
    parser.add_argument("--report-path", type=str, default="output/report.md", help="Output markdown report path")
    parser.add_argument("--artifact-output", type=str, help="Optional JSON artifact output path")
    args = parser.parse_args()

    result = generate_report(report_path=args.report_path, artifact_output=args.artifact_output)
    print(f"Status       : {result.get('status')}")
    print(f"Total rules  : {result.get('metrics', {}).get('total_rules', 0)}")
    print(f"Splunk count : {result.get('metrics', {}).get('splunk_queries', 0)}")
    print(f"KQL count    : {result.get('metrics', {}).get('kql_queries', 0)}")
    print(f"Report path  : {result.get('artifacts', {}).get('report_path')}")

    if result.get("status") == "failure":
        sys.exit(1)


if __name__ == "__main__":
    main()
