"""Query validation service with backend-aware manifest filtering."""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Dict, List, Tuple

from dac.schemas.results import build_result
from dac.services.artifacts import write_result_artifact
from dac.services.paths import artifacts_dir, repo_root


def validate_splunk_query(query: str) -> Tuple[bool, List[str]]:
    """Basic Splunk syntax checks (lightweight, offline-safe)."""
    errors: List[str] = []
    query_clean = re.sub(r"<!--.*?-->", "", query, flags=re.DOTALL)
    if not query_clean.strip():
        return False, ["Query is empty"]

    if query_clean.count("(") != query_clean.count(")"):
        errors.append("Unbalanced parentheses")
    if query_clean.count("[") != query_clean.count("]"):
        errors.append("Unbalanced brackets")
    if query_clean.count("{") != query_clean.count("}"):
        errors.append("Unbalanced braces")
    return len(errors) == 0, errors


def validate_kql_query(query: str) -> Tuple[bool, List[str]]:
    """Basic KQL syntax checks (lightweight, offline-safe)."""
    errors: List[str] = []
    query_clean = re.sub(r"//.*?$", "", query, flags=re.MULTILINE)
    query_clean = re.sub(r"/\*.*?\*/", "", query_clean, flags=re.DOTALL)
    if not query_clean.strip():
        return False, ["Query is empty"]

    if query_clean.count("(") != query_clean.count(")"):
        errors.append("Unbalanced parentheses")
    if query_clean.count("[") != query_clean.count("]"):
        errors.append("Unbalanced brackets")
    if query_clean.count("{") != query_clean.count("}"):
        errors.append("Unbalanced braces")
    return len(errors) == 0, errors


def validate_elasticsearch_query(query: str) -> Tuple[bool, List[str]]:
    """Basic Elasticsearch/Lucene query syntax checks (lightweight, offline-safe)."""
    errors: List[str] = []
    query_clean = query.strip()
    if not query_clean:
        return False, ["Query is empty"]

    if query_clean.count("(") != query_clean.count(")"):
        errors.append("Unbalanced parentheses")
    if query_clean.count("[") != query_clean.count("]"):
        errors.append("Unbalanced brackets")
    if query_clean.count("{") != query_clean.count("}"):
        errors.append("Unbalanced braces")
    return len(errors) == 0, errors


def validate_query_file(query_file: Path, query_type: str) -> Tuple[bool, List[str]]:
    """Validate a query file for the selected backend."""
    try:
        query = query_file.read_text(encoding="utf-8")
    except Exception as exc:
        return False, [f"Error reading file: {exc}"]

    if query_type == "splunk":
        return validate_splunk_query(query)
    if query_type == "kql":
        return validate_kql_query(query)
    if query_type == "elasticsearch":
        return validate_elasticsearch_query(query)
    return False, [f"Unknown query type: {query_type}"]


def _load_manifest(manifest_path: Path) -> Dict[str, object]:
    import json

    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _files_from_manifest(manifest_path: Path, query_type: str) -> List[Path]:
    payload = _load_manifest(manifest_path)
    files: List[Path] = []
    for rule in payload.get("rules", []):
        outputs = rule.get("outputs", {}) if isinstance(rule, dict) else {}
        candidate = outputs.get(query_type)
        if candidate:
            files.append(Path(candidate))
    return files


def validate_queries(
    *,
    query_type: str,
    directory: str,
    manifest: str | None = None,
    artifact_output: str | None = None,
) -> Dict[str, object]:
    """Validate query files and emit structured artifact output."""
    start = time.monotonic()
    rr = repo_root()
    query_dir = (rr / directory).resolve()

    if manifest:
        manifest_path = (rr / manifest).resolve() if not Path(manifest).is_absolute() else Path(manifest)
        if not manifest_path.exists():
            return build_result(
                status="failure",
                stage="validation",
                backend=query_type,
                errors=[f"Manifest not found: {manifest_path}"],
            )
        query_files = [p for p in _files_from_manifest(manifest_path, query_type) if p.exists()]
    else:
        manifest_path = None
        if not query_dir.exists():
            return build_result(
                status="failure",
                stage="validation",
                backend=query_type,
                errors=[f"Directory not found: {query_dir}"],
            )
        query_files = [
            f
            for f in query_dir.rglob(f"*.{query_type}")
            if not f.name.endswith(".meta") and not f.name.endswith(".error")
        ]

    if not query_files:
        result = build_result(
            status="success",
            stage="validation",
            backend=query_type,
            warnings=[f"No {query_type} query files found"],
            metrics={"duration_ms": int((time.monotonic() - start) * 1000), "files_checked": 0},
            context={"directory": str(query_dir), "manifest": str(manifest_path) if manifest_path else None},
        )
        out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / f"validation-{query_type}.json"
        write_result_artifact(result, out)
        return result

    failures: List[Dict[str, object]] = []
    for query_file in sorted(query_files):
        is_valid, errors = validate_query_file(query_file, query_type)
        if not is_valid:
            failures.append({"file": str(query_file), "errors": errors})

    result = build_result(
        status="failure" if failures else "success",
        stage="validation",
        backend=query_type,
        errors=[f"{f['file']}: {', '.join(f['errors'])}" for f in failures],
        metrics={
            "duration_ms": int((time.monotonic() - start) * 1000),
            "files_checked": len(query_files),
            "failed_files": len(failures),
        },
        artifacts={"manifest_path": str(manifest_path) if manifest_path else None},
        context={"directory": str(query_dir), "manifest": str(manifest_path) if manifest_path else None},
    )

    out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / f"validation-{query_type}.json"
    write_result_artifact(result, out)
    return result
