"""Backend test execution services for Splunk, ADX, and Elasticsearch."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml

from dac.backends.adx import AdxConfig, run_kql_query, summarize_kql_results, validate_kql_query
from dac.backends.elastic import (
    ElasticConfig,
    run_elastic_query,
    summarize_elastic_results,
    validate_elastic_query,
)
from dac.schemas.results import build_result
from dac.services.artifacts import write_result_artifact
from dac.services.paths import artifacts_dir, repo_root


def load_expectations(expectations_file: Path, query_type: str) -> Dict[str, Dict[str, int]]:
    """Load optional min/max result expectations for backend tests."""
    if not expectations_file.exists():
        return {}
    data = yaml.safe_load(expectations_file.read_text(encoding="utf-8")) or {}
    return data.get(query_type, {}) if isinstance(data, dict) else {}


def _match_expectation(expectations: Dict[str, Dict[str, int]], query_file: Path) -> Optional[Dict[str, int]]:
    return expectations.get(str(query_file)) or expectations.get(query_file.name)


def _expectation_error(expectation: Optional[Dict[str, int]], row_count: int) -> Optional[str]:
    """Return an expectation mismatch message, or None when row_count is acceptable."""
    if not expectation:
        return None
    min_expected = expectation.get("min", 0)
    max_expected = expectation.get("max")
    if row_count < min_expected:
        return f"expected >= {min_expected}, got {row_count}"
    if max_expected is not None and row_count > max_expected:
        return f"expected <= {max_expected}, got {row_count}"
    return None


def _load_query_files(directory: Path, suffix: str) -> List[Path]:
    return [
        f
        for f in directory.rglob(f"*.{suffix}")
        if not f.name.endswith(".meta") and not f.name.endswith(".error")
    ]


def _read_manifest_query_files(manifest_path: Path, backend: str) -> List[Path]:
    import json

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    files: List[Path] = []
    for rule in payload.get("rules", []):
        if isinstance(rule, dict):
            query_path = (rule.get("outputs") or {}).get(backend)
            if query_path:
                files.append(Path(query_path))
    return files


def execute_splunk_query(
    query: str,
    host: str,
    port: int,
    username: str,
    password: str,
    index: str,
    timeout: int,
) -> Tuple[bool, Dict[str, Any]]:
    """Execute one Splunk query using REST API."""
    try:
        search_url = f"https://{host}:{port}/services/search/jobs"
        response = requests.post(
            search_url,
            auth=(username, password),
            data={"search": f"search index={index} {query}", "output_mode": "json"},
            verify=False,
            timeout=timeout,
        )
        response.raise_for_status()

        import xml.etree.ElementTree as ET

        root = ET.fromstring(response.text)
        job_id = root.find(".//sid").text if root.find(".//sid") is not None else None
        if not job_id:
            return False, {"error": "Failed to create search job"}

        waited = 0
        while waited < 60:
            status_resp = requests.get(
                f"https://{host}:{port}/services/search/jobs/{job_id}",
                auth=(username, password),
                verify=False,
                timeout=timeout,
            )
            status_resp.raise_for_status()
            status_root = ET.fromstring(status_resp.text)
            state = status_root.find(".//dispatchState")
            dispatch_state = state.text if state is not None else ""
            if dispatch_state == "DONE":
                result_resp = requests.get(
                    f"https://{host}:{port}/services/search/jobs/{job_id}/results",
                    auth=(username, password),
                    params={"output_mode": "json"},
                    verify=False,
                    timeout=timeout,
                )
                result_resp.raise_for_status()
                payload = result_resp.json()
                return True, {
                    "job_id": job_id,
                    "result_count": len(payload.get("results", [])),
                    "raw": payload,
                }
            if dispatch_state in {"FAILED", "FATAL"}:
                return False, {"error": f"Search job failed with state: {dispatch_state}"}

            time.sleep(2)
            waited += 2

        return False, {"error": "Search job timed out"}
    except Exception as exc:
        return False, {"error": str(exc)}


def _normalize_query(query: str) -> str:
    lines = []
    for line in query.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return " ".join(lines)


def test_rule(rule_path: Path, backend: str, dataset: Optional[str] = None, mode: Optional[str] = None) -> Dict[str, Any]:
    """Minimal tool-like per-rule test entrypoint for future orchestrators."""
    if backend == "kql":
        cfg = AdxConfig.from_env()
        query_text = rule_path.read_text(encoding="utf-8")
        if mode == "compile":
            return validate_kql_query(query_text, cfg, mode="compile")
        return run_kql_query(query_text, cfg)
    elif backend == "elasticsearch":
        es_cfg = ElasticConfig.from_env()
        query_text = rule_path.read_text(encoding="utf-8")
        if mode == "compile":
            return validate_elastic_query(query_text, es_cfg, mode="compile")
        return run_elastic_query(query_text, es_cfg)
    return {"status": "failure", "errors": [f"Unsupported backend for test_rule: {backend}"]}


def run_splunk_tests(
    *,
    directory: str,
    host: str,
    port: int,
    username: str,
    password: str,
    index: str,
    expectations_path: str,
    query: Optional[str] = None,
    manifest: Optional[str] = None,
    artifact_output: Optional[str] = None,
) -> Dict[str, Any]:
    """Run Splunk query tests and emit structured result."""
    start = time.monotonic()
    rr = repo_root()
    query_dir = (rr / directory).resolve()
    expectations = load_expectations((rr / expectations_path).resolve(), "splunk")

    if query:
        query_files = [Path(query)]
    elif manifest:
        manifest_path = (rr / manifest).resolve() if not Path(manifest).is_absolute() else Path(manifest)
        query_files = [p for p in _read_manifest_query_files(manifest_path, "splunk") if p.exists()]
    else:
        if not query_dir.exists():
            return build_result(status="failure", stage="testing", backend="splunk", errors=[f"Directory not found: {query_dir}"])
        query_files = _load_query_files(query_dir, "splunk")

    if not query_files:
        result = build_result(
            status="success",
            stage="testing",
            backend="splunk",
            warnings=["No Splunk query files found"],
            metrics={"duration_ms": int((time.monotonic() - start) * 1000), "files_checked": 0},
        )
        out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / "splunk-testing.json"
        write_result_artifact(result, out)
        return result

    failures: List[str] = []
    passed = 0

    for query_file in sorted(query_files):
        query_text = _normalize_query(query_file.read_text(encoding="utf-8"))
        if not query_text:
            failures.append(f"{query_file}: Query file is empty")
            continue

        ok, payload = execute_splunk_query(query_text, host, port, username, password, index, timeout=30)
        if not ok:
            failures.append(f"{query_file}: {payload.get('error', 'Unknown error')}")
            continue

        result_count = int(payload.get("result_count", 0))
        expectation = _match_expectation(expectations, query_file)
        mismatch = _expectation_error(expectation, result_count)
        if mismatch:
            failures.append(f"{query_file}: {mismatch}")
            continue

        passed += 1

    result = build_result(
        status="failure" if failures else "success",
        stage="testing",
        backend="splunk",
        errors=failures,
        metrics={
            "duration_ms": int((time.monotonic() - start) * 1000),
            "files_checked": len(query_files),
            "passed": passed,
            "failed": len(failures),
        },
        context={"host": host, "port": port, "index": index},
    )

    out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / "splunk-testing.json"
    write_result_artifact(result, out)
    return result


def run_kql_tests(
    *,
    directory: str,
    expectations_path: str,
    mode: str = "execute",
    query: Optional[str] = None,
    manifest: Optional[str] = None,
    artifact_output: Optional[str] = None,
    config: Optional[AdxConfig] = None,
) -> Dict[str, Any]:
    """Run KQL compile/execute tests using ADX backend adapter and emit structured outputs."""
    start = time.monotonic()
    rr = repo_root()
    query_dir = (rr / directory).resolve()
    expectations = load_expectations((rr / expectations_path).resolve(), "kql")
    adx = config or AdxConfig.from_env()

    if not adx.cluster_uri or not adx.database:
        return build_result(
            status="failure",
            stage="testing",
            backend="adx",
            errors=["KUSTO_CLUSTER/ADX_CLUSTER_URI and KUSTO_DATABASE/ADX_DATABASE are required"],
        )

    if query:
        query_files = [Path(query)]
    elif manifest:
        manifest_path = (rr / manifest).resolve() if not Path(manifest).is_absolute() else Path(manifest)
        query_files = [p for p in _read_manifest_query_files(manifest_path, "kql") if p.exists()]
    else:
        if not query_dir.exists():
            return build_result(status="failure", stage="testing", backend="adx", errors=[f"Directory not found: {query_dir}"])
        query_files = _load_query_files(query_dir, "kql")

    if not query_files:
        result = build_result(
            status="success",
            stage="testing",
            backend="adx",
            warnings=["No KQL query files found"],
            metrics={"duration_ms": int((time.monotonic() - start) * 1000), "files_checked": 0},
        )
        out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / "kql-testing.json"
        write_result_artifact(result, out)
        return result

    failures: List[str] = []
    warnings: List[str] = []
    passed = 0
    compile_failures = 0
    execution_failures = 0
    results_by_file: List[Dict[str, Any]] = []

    for query_file in sorted(query_files):
        query_text = query_file.read_text(encoding="utf-8").strip()
        if not query_text:
            failures.append(f"{query_file}: Query file is empty")
            continue

        file_result: Dict[str, Any] = {"query_file": str(query_file), "stages": {}}

        should_compile = mode in {"compile", "both"}
        should_execute = mode in {"execute", "both"}

        if should_compile:
            compile_result = validate_kql_query(query_text, adx, mode="compile")
            file_result["stages"]["compile"] = summarize_kql_results(compile_result)
            if compile_result.get("status") != "success":
                compile_failures += 1
                failures.append(f"{query_file}: compile failed: {', '.join(compile_result.get('errors', []))}")
                if mode == "compile":
                    results_by_file.append(file_result)
                    continue

        if should_execute:
            execute_result = run_kql_query(query_text, adx)
            file_result["stages"]["execution"] = summarize_kql_results(execute_result)
            if execute_result.get("status") != "success":
                execution_failures += 1
                failures.append(f"{query_file}: execution failed: {', '.join(execute_result.get('errors', []))}")
                results_by_file.append(file_result)
                continue

            row_count = int(execute_result.get("metrics", {}).get("row_count", 0))
            expectation = _match_expectation(expectations, query_file)
            mismatch = _expectation_error(expectation, row_count)
            if mismatch:
                execution_failures += 1
                failures.append(f"{query_file}: {mismatch}")
                results_by_file.append(file_result)
                continue

        if not should_execute and should_compile and file_result["stages"].get("compile", {}).get("status") == "success":
            warnings.append(f"{query_file}: compile passed; execution not requested")

        passed += 1
        results_by_file.append(file_result)

    result = build_result(
        status="failure" if failures else "success",
        stage="testing",
        backend="adx",
        errors=failures,
        warnings=warnings,
        metrics={
            "duration_ms": int((time.monotonic() - start) * 1000),
            "files_checked": len(query_files),
            "passed": passed,
            "failed": len(failures),
            "compile_failures": compile_failures,
            "execution_failures": execution_failures,
        },
        context={
            "cluster_uri": adx.cluster_uri,
            "database": adx.database,
            "mode": mode,
            "row_limit": adx.row_limit,
            "timeout_seconds": adx.timeout_seconds,
        },
        artifacts={"results": results_by_file},
    )

    out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / "kql-testing.json"
    write_result_artifact(result, out)
    return result


def run_elastic_tests(
    *,
    directory: str,
    expectations_path: str,
    mode: str = "execute",
    query: Optional[str] = None,
    manifest: Optional[str] = None,
    artifact_output: Optional[str] = None,
    config: Optional[ElasticConfig] = None,
) -> Dict[str, Any]:
    """Run Elasticsearch compile/execute tests and emit structured outputs."""
    start = time.monotonic()
    rr = repo_root()
    query_dir = (rr / directory).resolve()
    expectations = load_expectations((rr / expectations_path).resolve(), "elasticsearch")
    es = config or ElasticConfig.from_env()

    if not es.host:
        return build_result(
            status="failure",
            stage="testing",
            backend="elasticsearch",
            errors=["ELASTIC_HOST is required"],
        )

    if query:
        query_files = [Path(query)]
    elif manifest:
        manifest_path = (rr / manifest).resolve() if not Path(manifest).is_absolute() else Path(manifest)
        query_files = [p for p in _read_manifest_query_files(manifest_path, "elasticsearch") if p.exists()]
    else:
        if not query_dir.exists():
            return build_result(status="failure", stage="testing", backend="elasticsearch", errors=[f"Directory not found: {query_dir}"])
        query_files = _load_query_files(query_dir, "elasticsearch")

    if not query_files:
        result = build_result(
            status="success",
            stage="testing",
            backend="elasticsearch",
            warnings=["No Elasticsearch query files found"],
            metrics={"duration_ms": int((time.monotonic() - start) * 1000), "files_checked": 0},
        )
        out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / "elastic-testing.json"
        write_result_artifact(result, out)
        return result

    failures: List[str] = []
    warnings: List[str] = []
    passed = 0
    compile_failures = 0
    execution_failures = 0
    results_by_file: List[Dict[str, Any]] = []

    for query_file in sorted(query_files):
        query_text = query_file.read_text(encoding="utf-8").strip()
        if not query_text:
            failures.append(f"{query_file}: Query file is empty")
            continue

        file_result: Dict[str, Any] = {"query_file": str(query_file), "stages": {}}

        should_compile = mode in {"compile", "both"}
        should_execute = mode in {"execute", "both"}

        if should_compile:
            compile_result = validate_elastic_query(query_text, es, mode="compile")
            file_result["stages"]["compile"] = summarize_elastic_results(compile_result)
            if compile_result.get("status") != "success":
                compile_failures += 1
                failures.append(f"{query_file}: compile failed: {', '.join(compile_result.get('errors', []))}")
                if mode == "compile":
                    results_by_file.append(file_result)
                    continue

        if should_execute:
            execute_result = run_elastic_query(query_text, es)
            file_result["stages"]["execution"] = summarize_elastic_results(execute_result)
            if execute_result.get("status") != "success":
                execution_failures += 1
                failures.append(f"{query_file}: execution failed: {', '.join(execute_result.get('errors', []))}")
                results_by_file.append(file_result)
                continue

            row_count = int(execute_result.get("metrics", {}).get("row_count", 0))
            expectation = _match_expectation(expectations, query_file)
            mismatch = _expectation_error(expectation, row_count)
            if mismatch:
                execution_failures += 1
                failures.append(f"{query_file}: {mismatch}")
                results_by_file.append(file_result)
                continue

        if not should_execute and should_compile and file_result["stages"].get("compile", {}).get("status") == "success":
            warnings.append(f"{query_file}: compile passed; execution not requested")

        passed += 1
        results_by_file.append(file_result)

    result = build_result(
        status="failure" if failures else "success",
        stage="testing",
        backend="elasticsearch",
        errors=failures,
        warnings=warnings,
        metrics={
            "duration_ms": int((time.monotonic() - start) * 1000),
            "files_checked": len(query_files),
            "passed": passed,
            "failed": len(failures),
            "compile_failures": compile_failures,
            "execution_failures": execution_failures,
        },
        context={
            "host": es.host,
            "index": es.index,
            "mode": mode,
            "row_limit": es.row_limit,
            "timeout_seconds": es.timeout_seconds,
        },
        artifacts={"results": results_by_file},
    )

    out = Path(artifact_output) if artifact_output else artifacts_dir(rr) / "elastic-testing.json"
    write_result_artifact(result, out)
    return result
