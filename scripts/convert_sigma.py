#!/usr/bin/env python3
"""
Convert Sigma rules to Splunk or KQL queries.

Key behaviors:
- If a rule has `conversion_targets: [splunk, kql]`, only convert to those targets.
- If `conversion_targets` is missing, convert to the requested backend (default behavior).
- Supports converting a single rule (--rule) or all rules under sigma-rules/.
- Writes outputs to: output/<backend>/<mirrored_path>/<rule_stem>.<backend>
- Writes metadata alongside outputs:
    - .<backend>.meta on success or skip
    - .<backend>.error on failure
- Exits non-zero if any conversion fails.

IMPORTANT:
- sigma-cli expects input files as positional args: `sigma convert -t <target> <rule.yml>`
  (NOT `-f <rule.yml>`). This script uses positional input.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Literal, Tuple

import yaml

Status = Literal["success", "skipped", "failed"]

# Repo-facing backend labels (keep consistent with validate_rule_metadata.py)
SUPPORTED_BACKENDS = {"splunk", "kql"}


def sigma_cli_target(backend: str) -> str:
    """
    Map our backend label to the Sigma CLI target name.

    Sigma CLI uses 'kusto' for KQL (Azure Data Explorer / Sentinel).
    We keep 'kql' as our repo-facing label to preserve output paths/extensions.
    """
    return "kusto" if backend == "kql" else backend


def repo_root() -> Path:
    """
    Find repo root robustly by walking up from this script until we find .git.
    Fallbacks: pyproject.toml / requirements.txt.
    """
    start = Path(__file__).resolve()
    for p in [start.parent, *start.parents]:
        if (p / ".git").exists():
            return p
        if (p / "pyproject.toml").exists():
            return p
        if (p / "requirements.txt").exists():
            return p
    return start.parent.parent


def sigma_rules_dir() -> Path:
    return repo_root() / "sigma-rules"


def _reroot_if_contains_sigma_rules(p: Path) -> Optional[Path]:
    """
    If an absolute path doesn't exist but contains 'sigma-rules/<...>',
    rebuild it under the detected repo root.

    Example:
      /Users/x/Study/sigma-rules/endpoint/a.yml
      -> <repo_root>/sigma-rules/endpoint/a.yml
    """
    parts = list(p.parts)
    if "sigma-rules" not in parts:
        return None
    idx = parts.index("sigma-rules")
    subpath = Path(*parts[idx:])  # sigma-rules/...
    return (repo_root() / subpath).resolve()


def resolve_path(raw: str) -> Path:
    """
    Resolve a user-provided path.

    Rules:
    - If relative:
        - First try resolving relative to the current working directory (CWD). This allows
          calling the script from subdirectories and using paths like ../sigma-rules/...
        - If that doesn't exist, treat as relative to repo root.
    - If absolute and exists: use as-is.
    - If absolute and DOES NOT exist:
        - if it contains 'sigma-rules/...', re-root it under repo_root().
        - otherwise, keep as-is (caller will error).
    """
    p = Path(raw)

    if not p.is_absolute():
        cwd_p = (Path.cwd() / p).resolve()
        if cwd_p.exists():
            return cwd_p
        return (repo_root() / p).resolve()

    if p.exists():
        return p.resolve()

    rerooted = _reroot_if_contains_sigma_rules(p)
    if rerooted is not None:
        return rerooted

    return p.resolve()


def load_yaml(rule_path: Path) -> dict:
    try:
        return yaml.safe_load(rule_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error in {rule_path}: {exc}") from exc


def load_conversion_targets(rule_path: Path) -> Optional[List[str]]:
    data = load_yaml(rule_path)
    targets = data.get("conversion_targets", None)
    if targets is None:
        return None
    if not isinstance(targets, list):
        raise ValueError("conversion_targets must be a list (e.g., ['splunk', 'kql'])")
    return [str(t).strip().lower() for t in targets if str(t).strip()]


def rel_to_sigma_dir(rule_path: Path) -> Path:
    sr = sigma_rules_dir().resolve()
    rp = rule_path.resolve()
    try:
        return rp.relative_to(sr)
    except ValueError as exc:
        raise ValueError(f"Rule path must be under {sr}: {rp}") from exc


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_meta(meta_path: Path, rule_path: Path, backend: str, status: str, extra: str = "") -> None:
    lines = [
        f"Source: {rule_path.as_posix()}",
        f"Backend: {backend}",
        f"Status: {status}",
    ]
    if extra:
        lines.append(extra.rstrip())
    write_text(meta_path, "\n".join(lines) + "\n")


def convert_sigma_rule(rule_path: Path, backend: str, output_base: Path) -> Tuple[Status, Path]:
    relative_path = rel_to_sigma_dir(rule_path)
    output_query = output_base / relative_path.parent / f"{rule_path.stem}.{backend}"
    meta_file = output_query.with_suffix(f".{backend}.meta")
    err_file = output_query.with_suffix(f".{backend}.error")

    targets = load_conversion_targets(rule_path)
    if targets is not None:
        if backend not in targets:
            write_meta(meta_file, rule_path, backend, "Skipped (target not selected)")
            return "skipped", output_query

    # --- UPDATED TO OFFICIAL CLI SYNTAX ---
    # sigma-cli target name mapping (kql -> kusto)
    cli_backend_name = sigma_cli_target(backend)
    
    cmd = [
        "sigma", "convert",
        "--target", cli_backend_name
    ]
    
    # Apply the specific pipeline for Splunk CIM
    if backend == "splunk":
        cmd.extend(["--pipeline", "splunk_windows"])
    
    # Append the rule path as the final positional argument
    cmd.append(str(rule_path))

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        write_text(output_query, result.stdout)
        write_meta(meta_file, rule_path, backend, "Success")
        return "success", output_query

    # Error handling logic remains the same
    details = "\n".join([s for s in [result.stdout.strip(), result.stderr.strip()] if s])
    err_content = f"Source: {rule_path.as_posix()}\nBackend: {backend}\nStatus: Failed\nError:\n{details}\n"
    write_text(err_file, err_content)
    return "failed", output_query

def collect_rule_files(rule_arg: Optional[str]) -> List[Path]:
    sr = sigma_rules_dir()
    rr = repo_root()

    if not sr.exists():
        raise FileNotFoundError(f"{sr} does not exist (repo root detected as {rr})")

    if rule_arg:
        p = resolve_path(rule_arg)
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Sigma rules to queries")
    parser.add_argument(
        "--backend",
        choices=sorted(SUPPORTED_BACKENDS),
        default="splunk",
        help="Backend to convert to",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory (default: output)",
    )
    parser.add_argument(
        "--rule",
        type=str,
        help="Convert a specific rule file OR a directory of rules (relative to repo root or CWD is OK)",
    )
    args = parser.parse_args()

    if shutil.which("sigma") is None:
        print("Error: 'sigma' CLI not found on PATH. Install sigma-cli and ensure 'sigma' is available.")
        print("Tip (venv):   pip install sigma-cli")
        print("Tip (pipx):   pipx install sigma-cli")
        sys.exit(1)

    rr = repo_root()
    sr = sigma_rules_dir()
    out_base = rr / args.output / args.backend

    try:
        rule_files = collect_rule_files(args.rule)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    if not rule_files:
        print("No Sigma rule files found")
        sys.exit(0)

    print(f"Repo root: {rr}")
    print(f"Sigma dir: {sr}")
    print(f"Output   : {out_base}\n")
    print(f"Converting {len(rule_files)} rule(s) to {args.backend}...\n")

    success = 0
    skipped = 0
    failed = 0

    for rule_file in rule_files:
        try:
            status, _ = convert_sigma_rule(rule_file, args.backend, out_base)
        except Exception as exc:
            failed += 1
            print(f"  ✗ {rule_file}: {exc}")
            continue

        rel = rule_file.resolve().relative_to(sr.resolve())

        if status == "success":
            success += 1
            print(f"  ✓ {rel}")
        elif status == "skipped":
            skipped += 1
            print(f"  ↷ {rel} (skipped)")
        else:
            failed += 1
            print(f"  ✗ {rel} (failed)")

    print("\nConversion summary:")
    print(f"  Success: {success}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed : {failed}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
