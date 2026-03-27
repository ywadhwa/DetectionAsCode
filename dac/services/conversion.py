"""Sigma conversion service with structured outputs and manifest emission."""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

import yaml

from dac.schemas.results import build_result
from dac.services.manifest import build_rule_manifest, build_run_manifest, write_manifest
from dac.services.paths import artifacts_dir, repo_root, sigma_rules_dir

Status = Literal["success", "skipped", "failed"]
SUPPORTED_BACKENDS = {"splunk", "kql", "elasticsearch"}


def sigma_cli_target(backend: str) -> str:
    """Map repo backend label to sigma-cli target."""
    if backend == "kql":
        return "kusto"
    if backend == "elasticsearch":
        # sigma-cli v2 exposes Elasticsearch query-string backend as "lucene"
        return "lucene"
    return backend


def resolve_path(raw: str, root: Optional[Path] = None) -> Path:
    """Resolve an input path from CWD, then repo-root fallback."""
    rr = root or repo_root()
    p = Path(raw)

    if not p.is_absolute():
        cwd_candidate = (Path.cwd() / p).resolve()
        if cwd_candidate.exists():
            return cwd_candidate
        return (rr / p).resolve()

    if p.exists():
        return p.resolve()

    parts = list(p.parts)
    if "sigma-rules" in parts:
        idx = parts.index("sigma-rules")
        return (rr / Path(*parts[idx:])).resolve()

    return p.resolve()


def load_yaml(rule_path: Path) -> dict:
    """Load a Sigma rule as dict."""
    try:
        return yaml.safe_load(rule_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error in {rule_path}: {exc}") from exc


def load_conversion_targets(rule_path: Path) -> Optional[List[str]]:
    """Load optional per-rule conversion_targets override."""
    data = load_yaml(rule_path)
    targets = data.get("conversion_targets")
    if targets is None:
        return None
    if not isinstance(targets, list):
        raise ValueError("conversion_targets must be a list (e.g., ['splunk', 'kql'])")
    return [str(t).strip().lower() for t in targets if str(t).strip()]


def rule_identifier(rule_path: Path) -> str:
    """Derive stable rule identifier from YAML id or filename stem."""
    try:
        parsed = load_yaml(rule_path)
        rule_id = parsed.get("id") if isinstance(parsed, dict) else None
        if rule_id:
            return str(rule_id)
    except Exception:
        pass
    return rule_path.stem


def rel_to_sigma_dir(rule_path: Path, root: Optional[Path] = None) -> Path:
    """Return path relative to sigma-rules directory."""
    sr = sigma_rules_dir(root).resolve()
    rp = rule_path.resolve()
    try:
        return rp.relative_to(sr)
    except ValueError as exc:
        raise ValueError(f"Rule path must be under {sr}: {rp}") from exc


def write_text(path: Path, content: str) -> None:
    """Write text with parent directory creation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_meta(meta_path: Path, rule_path: Path, backend: str, status: str, extra: str = "") -> None:
    """Write legacy sidecar meta file (backward compatibility)."""
    lines = [
        f"Source: {rule_path.as_posix()}",
        f"Backend: {backend}",
        f"Status: {status}",
    ]
    if extra:
        lines.append(extra.rstrip())
    write_text(meta_path, "\n".join(lines) + "\n")


def convert_sigma_rule(
    rule_path: Path,
    backend: str,
    output_base: Path,
    timeout: int = 120,
    emit_sidecars: bool = True,
) -> Tuple[Status, Path, str, str]:
    """Convert one Sigma rule into one backend query."""
    relative_path = rel_to_sigma_dir(rule_path)
    output_query = output_base / relative_path.parent / f"{rule_path.stem}.{backend}"
    meta_file = output_query.with_suffix(f".{backend}.meta")
    err_file = output_query.with_suffix(f".{backend}.error")

    targets = load_conversion_targets(rule_path)
    if targets is not None and backend not in targets:
        if emit_sidecars:
            write_meta(meta_file, rule_path, backend, "Skipped (target not selected)")
        return "skipped", output_query, "target not selected", ""

    cmd = ["sigma", "convert", "--target", sigma_cli_target(backend)]
    if backend == "splunk":
        cmd.extend(["--pipeline", "splunk_windows"])
    elif backend == "elasticsearch":
        # sigma-cli v2 lucene backend requires a pipeline unless this flag is set.
        cmd.append("--without-pipeline")
    cmd.append(str(rule_path))

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode == 0:
        write_text(output_query, result.stdout)
        if emit_sidecars:
            write_meta(meta_file, rule_path, backend, "Success")
        return "success", output_query, "", result.stdout

    details = "\n".join([s for s in [result.stdout.strip(), result.stderr.strip()] if s])
    if emit_sidecars:
        err_content = (
            f"Source: {rule_path.as_posix()}\n"
            f"Backend: {backend}\n"
            "Status: Failed\n"
            f"Error:\n{details}\n"
        )
        write_text(err_file, err_content)
    return "failed", output_query, details or "sigma convert failed", ""


def collect_rule_files(rule_arg: Optional[str], root: Optional[Path] = None) -> List[Path]:
    """Collect rule files from --rule path or full sigma-rules tree."""
    rr = root or repo_root()
    sr = sigma_rules_dir(rr)
    if not sr.exists():
        raise FileNotFoundError(f"{sr} does not exist (repo root detected as {rr})")

    if rule_arg:
        p = resolve_path(rule_arg, rr)
        if not p.exists():
            raise FileNotFoundError(f"Rule not found: {p} (repo root detected as {rr})")
        if p.is_dir():
            files = list(p.rglob("*.yml")) + list(p.rglob("*.yaml"))
        else:
            if p.suffix.lower() not in {".yml", ".yaml"}:
                raise ValueError(f"--rule must be a .yml/.yaml file or directory: {p}")
            files = [p]
        return sorted(set(files))

    return sorted(set(list(sr.rglob("*.yml")) + list(sr.rglob("*.yaml"))))


def convert_rule(rule_path: Path, targets: Optional[List[str]] = None, output_dir: str = "output") -> Dict[str, object]:
    """Programmatic conversion entrypoint for one rule across selected targets."""
    selected_targets = targets or sorted(SUPPORTED_BACKENDS)
    results = run_conversion(backend=selected_targets[0], output=output_dir, rule=str(rule_path))
    return results


def run_conversion(
    *,
    backend: str,
    output: str = "output",
    rule: Optional[str] = None,
    artifact_output: Optional[str] = None,
    bundle_output: Optional[str] = None,
) -> Dict[str, object]:
    """Convert Sigma rules for one backend and emit structured artifacts/manifests."""
    start = time.monotonic()
    rr = repo_root()
    sr = sigma_rules_dir(rr)

    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported backend: {backend}. Supported: {sorted(SUPPORTED_BACKENDS)}")
    if shutil.which("sigma") is None:
        return build_result(
            status="failure",
            stage="conversion",
            backend=backend,
            errors=["'sigma' CLI not found on PATH"],
            context={"repo_root": str(rr)},
        )

    try:
        rule_files = collect_rule_files(rule, rr)
    except (FileNotFoundError, ValueError) as exc:
        return build_result(
            status="failure",
            stage="conversion",
            backend=backend,
            errors=[str(exc)],
            context={"repo_root": str(rr)},
        )

    if not rule_files:
        result = build_result(
            status="success",
            stage="conversion",
            backend=backend,
            warnings=["No Sigma rule files found"],
            metrics={"duration_ms": int((time.monotonic() - start) * 1000), "processed_rules": 0},
            context={"repo_root": str(rr), "sigma_dir": str(sr)},
        )
        output_path = Path(artifact_output) if artifact_output else artifacts_dir(rr) / f"conversion-{backend}.json"
        write_manifest(result, output_path)
        return result

    out_base = rr / output / backend
    emit_sidecars = bundle_output is None

    success = 0
    skipped = 0
    failed = 0
    rules_manifest: List[Dict[str, object]] = []
    errors: List[str] = []
    bundle_rules: List[Dict[str, object]] = []

    for rule_file in rule_files:
        rule_id = rule_identifier(rule_file)
        try:
            status, query_path, error_message, query_text = convert_sigma_rule(
                rule_file,
                backend,
                out_base,
                emit_sidecars=emit_sidecars,
            )
        except Exception as exc:
            status = "failed"
            query_path = out_base / rule_file.name
            error_message = str(exc)
            query_text = ""

        outputs: Dict[str, str] = {}
        generated: List[str] = []
        skipped_targets: List[str] = []
        rule_errors: List[str] = []

        if status == "success":
            success += 1
            outputs[backend] = str(query_path)
            generated.append(backend)
        elif status == "skipped":
            skipped += 1
            skipped_targets.append(backend)
        else:
            failed += 1
            msg = f"{rule_file}: {error_message or 'conversion failed'}"
            errors.append(msg)
            rule_errors.append(error_message or "conversion failed")

        rule_manifest = build_rule_manifest(
            rule_id=rule_id,
            outputs=outputs,
            generated=generated,
            skipped=skipped_targets,
            errors=rule_errors,
        )

        per_rule_manifest_path = query_path.with_suffix(".manifest.json")
        write_manifest(rule_manifest, per_rule_manifest_path)
        rule_manifest["manifest_path"] = str(per_rule_manifest_path)
        rules_manifest.append(rule_manifest)
        bundle_rules.append(
            {
                "rule_id": rule_id,
                "rule_path": str(rule_file),
                "status": status,
                "backend": backend,
                "query_path": str(query_path),
                "query": query_text if status == "success" else "",
                "error": error_message if status == "failed" else "",
                "skipped_reason": error_message if status == "skipped" else "",
            }
        )

    run_manifest = build_run_manifest(
        backend=backend,
        generated_count=success,
        skipped_count=skipped,
        failed_count=failed,
        rules=rules_manifest,
    )

    run_manifest_path = out_base / f"conversion_manifest.{backend}.json"
    write_manifest(run_manifest, run_manifest_path)

    duration_ms = int((time.monotonic() - start) * 1000)
    result = build_result(
        status="failure" if failed else "success",
        stage="conversion",
        backend=backend,
        errors=errors,
        metrics={
            "duration_ms": duration_ms,
            "processed_rules": len(rule_files),
            "generated_count": success,
            "skipped_count": skipped,
            "failed_count": failed,
        },
        artifacts={
            "conversion_manifest_path": str(run_manifest_path),
            "output_directory": str(out_base),
        },
        context={
            "repo_root": str(rr),
            "sigma_dir": str(sr),
            "output_arg": output,
            # NOTE: keep this context stable for pipeline artifact consumers.
        },
    )

    output_path = Path(artifact_output) if artifact_output else artifacts_dir(rr) / f"conversion-{backend}.json"
    write_manifest(result, output_path)
    if bundle_output:
        bundle_path = Path(bundle_output)
        bundle_payload = {
            "backend": backend,
            "status": result.get("status"),
            "metrics": result.get("metrics", {}),
            "rules": bundle_rules,
        }
        write_manifest(bundle_payload, bundle_path)
    return result
