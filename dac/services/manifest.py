"""Conversion manifest utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from dac.services.artifacts import write_json


def build_rule_manifest(
    *,
    rule_id: str,
    outputs: Dict[str, str],
    generated: List[str],
    skipped: List[str],
    errors: List[str],
) -> Dict[str, Any]:
    """Create a per-rule conversion manifest payload."""
    return {
        "rule_id": rule_id,
        "outputs": outputs,
        "generated": generated,
        "skipped": skipped,
        "errors": errors,
    }


def build_run_manifest(
    *,
    backend: str,
    generated_count: int,
    skipped_count: int,
    failed_count: int,
    rules: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Create a run-level conversion manifest payload."""
    return {
        "backend": backend,
        "status": "failure" if failed_count else "success",
        "generated_count": generated_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "rules": rules,
    }


def write_manifest(payload: Dict[str, Any], output_path: Path) -> Path:
    """Persist manifest JSON to disk."""
    return write_json(output_path, payload)
