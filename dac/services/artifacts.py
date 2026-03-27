"""Artifact helpers for predictable JSON outputs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_json(path: Path, payload: Dict[str, Any]) -> Path:
    """Write JSON artifact to disk with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_result_artifact(result: Dict[str, Any], output_path: str | Path) -> Path:
    """Write an operation result artifact to a target path."""
    return write_json(Path(output_path), result)
