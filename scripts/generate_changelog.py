#!/usr/bin/env python3
"""Generate a Sigma rule changelog from git history."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Tuple


RULE_PATTERNS = ("sigma-rules/**/*.yml", "sigma-rules/**/*.yaml")
STATUS_LABELS = {
    "A": "Created",
    "M": "Modified",
    "D": "Deleted",
    "R": "Renamed",
}
CHANGE_PATTERNS = [
    (re.compile(r"^\s*[+-]\s*title\s*:", re.MULTILINE), "Title updated"),
    (re.compile(r"^\s*[+-]\s*description\s*:", re.MULTILINE), "Description updated"),
    (re.compile(r"^\s*[+-]\s*status\s*:", re.MULTILINE), "Status changed"),
    (re.compile(r"^\s*[+-]\s*level\s*:", re.MULTILINE), "Severity changed"),
    (re.compile(r"^\s*[+-]\s*version\s*:", re.MULTILINE), "Version updated"),
    (re.compile(r"^\s*[+-]\s*references\s*:", re.MULTILINE), "References updated"),
    (re.compile(r"^\s*[+-]\s*tags\s*:", re.MULTILINE), "ATT&CK/context tags updated"),
    (re.compile(r"^\s*[+-]\s*falsepositives\s*:", re.MULTILINE), "False positive guidance updated"),
    (re.compile(r"^\s*[+-]\s*logsource\s*:", re.MULTILINE), "Logsource updated"),
    (re.compile(r"^\s*[+-]\s*detection\s*:", re.MULTILINE), "Detection logic updated"),
    (re.compile(r"^\s*[+-]\s*related\s*:", re.MULTILINE), "Related rule mapping updated"),
]


def run_git(args: List[str]) -> str:
    """Run a git command and return normalized stdout."""
    return subprocess.check_output(["git", *args], text=True, encoding="utf-8", errors="replace").strip()


def resolve_repo_url() -> str:
    """Resolve a browser-friendly repository URL from git config."""
    repo_url = os.getenv("REPO_URL", "").strip()
    if repo_url:
        return repo_url.rstrip("/")

    try:
        remote = run_git(["config", "--get", "remote.origin.url"])
    except subprocess.CalledProcessError:
        return ""

    if remote.startswith("git@github.com:"):
        remote = remote.replace("git@github.com:", "https://github.com/")
    return remote.removesuffix(".git").rstrip("/")


def rule_pathspec() -> List[str]:
    """Return git pathspecs covering all Sigma rule YAML files."""
    return list(RULE_PATTERNS)


def iter_commits(start_date: str | None, end_date: str | None) -> List[str]:
    """Return commit hashes touching Sigma rules within the optional date range."""
    args = ["log", "--pretty=format:%H", "--date=iso-strict"]
    if start_date:
        args.append(f"--since={start_date}")
    if end_date:
        args.append(f"--until={end_date}")
    args.extend(["--", *rule_pathspec()])
    output = run_git(args)
    return [line for line in output.splitlines() if line]


def get_commit_meta(commit_hash: str) -> Dict[str, str]:
    """Return core commit metadata for one commit."""
    raw = run_git(
        [
            "show",
            "-s",
            "--date=iso-strict",
            "--format=%H%x1f%an%x1f%ad%x1f%s",
            commit_hash,
        ]
    )
    sha, author, date, subject = raw.split("\x1f", 3)
    return {"sha": sha, "author": author, "date": date, "subject": subject}


def get_commit_modified_files(commit_hash: str) -> List[Tuple[str, str, str | None]]:
    """Return changed Sigma rule files with git status and optional rename target."""
    output = run_git(
        ["diff-tree", "-M", "--no-commit-id", "--name-status", "-r", commit_hash, "--", *rule_pathspec()]
    )
    files: List[Tuple[str, str, str | None]] = []
    for line in output.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            files.append((status, parts[1], parts[2]))
        elif len(parts) >= 2:
            files.append((status, parts[1], None))
    return files


def get_commit_modified_file_diff(commit_hash: str, file_path: str) -> str:
    """Return a minimal diff for one file in one commit."""
    return run_git(["--no-pager", "show", "--pretty=", "--unified=0", commit_hash, "--", file_path])


def classify_rule_diff(diff_output: str) -> List[str]:
    """Convert a rule diff into a list of human-readable change descriptions."""
    changes = [label for pattern, label in CHANGE_PATTERNS if pattern.search(diff_output)]
    return changes or ["Misc rule metadata updated"]


def bucket_start(dt: datetime, bucket: str) -> datetime:
    """Normalize a datetime into the configured changelog bucket."""
    dt = dt.astimezone(UTC)
    if bucket == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if bucket == "week":
        week_start = dt - timedelta(days=dt.weekday())
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    if bucket == "month":
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if bucket == "quarter":
        quarter_month = 3 * ((dt.month - 1) // 3) + 1
        return dt.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError("bucket must be one of: day, week, month, quarter")


def bucket_end(start: datetime, bucket: str) -> datetime:
    """Return the exclusive end datetime for one bucket start."""
    if bucket == "day":
        return start + timedelta(days=1)
    if bucket == "week":
        return start + timedelta(days=7)
    if bucket == "month":
        if start.month == 12:
            return start.replace(year=start.year + 1, month=1)
        return start.replace(month=start.month + 1)
    if bucket == "quarter":
        if start.month >= 10:
            return start.replace(year=start.year + 1, month=1)
        return start.replace(month=start.month + 3)
    raise ValueError("bucket must be one of: day, week, month, quarter")


def build_change_log(commit_hashes: Iterable[str]) -> List[Dict[str, object]]:
    """Build a flattened change log from git history for Sigma rules only."""
    change_log: List[Dict[str, object]] = []
    for commit_hash in commit_hashes:
        meta = get_commit_meta(commit_hash)
        modified_files = get_commit_modified_files(commit_hash)
        for status_code, old_path, new_path in modified_files:
            status_label = STATUS_LABELS.get(status_code[0], status_code)
            changes: List[str] = []

            if status_label == "Modified":
                changes = classify_rule_diff(get_commit_modified_file_diff(commit_hash, old_path))
            elif status_label == "Renamed":
                if new_path:
                    old_dir = str(Path(old_path).parent)
                    new_dir = str(Path(new_path).parent)
                    if Path(old_path).name == Path(new_path).name and old_dir != new_dir:
                        status_label = "Moved"
                        changes = [f"Moved to {new_dir}"]
                    else:
                        changes = [f"Renamed to {new_path}"]

            if not changes:
                changes = [""]

            for change in changes:
                change_log.append(
                    {
                        "datetime": meta["date"],
                        "commit": meta["sha"],
                        "message": meta["subject"],
                        "author": meta["author"],
                        "file": old_path,
                        "filename": Path(old_path).name,
                        "filepath": str(Path(old_path).parent),
                        "status": status_label,
                        "change": change,
                    }
                )
    return change_log


def change_log_to_markdown(change_log: List[Dict[str, object]], repo_url: str, bucket: str) -> str:
    """Render the flattened changelog into markdown grouped by time bucket."""
    if not change_log:
        return "# Rule Changelog\n\nNo Sigma rule changes found for the requested time range.\n"

    grouped: DefaultDict[datetime, List[Dict[str, object]]] = defaultdict(list)
    for item in change_log:
        parsed = datetime.fromisoformat(str(item["datetime"]))
        grouped[bucket_start(parsed, bucket)].append(item)

    lines = ["# Rule Changelog", ""]
    sorted_groups = sorted(grouped.items(), key=lambda pair: pair[0], reverse=True)
    for start, entries in sorted_groups:
        end = bucket_end(start, bucket)
        lines.append(f"## {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
        lines.append("")

        by_status: DefaultDict[str, List[Dict[str, object]]] = defaultdict(list)
        for entry in entries:
            by_status[str(entry["status"])].append(entry)

        for status in ("Created", "Modified", "Deleted", "Moved", "Renamed"):
            items = by_status.get(status, [])
            if not items:
                continue
            lines.append(f"### {status}")
            for item in sorted(items, key=lambda row: (str(row["file"]), str(row["commit"]))):
                commit_ref = str(item["commit"])
                commit_label = commit_ref[:7]
                commit_url = f"{repo_url}/commit/{commit_ref}" if repo_url else ""
                commit_link = f"[{commit_label}]({commit_url})" if commit_url else commit_label
                message = f" - {item['change']}" if item["change"] else ""
                lines.append(
                    f"- `{item['file']}`{message} ({commit_link}, {item['author']}: {item['message']})"
                )
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: Dict[str, object]) -> None:
    """Write JSON with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def generate_change_log(
    *,
    repo_url: str,
    start_date: str | None,
    end_date: str | None,
    output_markdown: Path,
    output_json: Path,
    bucket: str,
) -> None:
    """Generate markdown and JSON changelog outputs."""
    commits = iter_commits(start_date=start_date, end_date=end_date)
    change_log = build_change_log(commits)
    markdown = change_log_to_markdown(change_log, repo_url=repo_url, bucket=bucket)

    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.write_text(markdown, encoding="utf-8")
    write_json(
        output_json,
        {
            "repo_url": repo_url,
            "start_date": start_date,
            "end_date": end_date,
            "bucket": bucket,
            "commit_count": len(commits),
            "change_count": len(change_log),
            "changes": change_log,
        },
    )


def main() -> None:
    repo_root = Path(__file__).parent.parent
    parser = argparse.ArgumentParser(description="Generate a Sigma rule changelog from git history")
    parser.add_argument("--repo-url", default=resolve_repo_url(), help="Repository URL used for commit links")
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", help="End date in YYYY-MM-DD format")
    parser.add_argument(
        "--bucket",
        default="month",
        choices=["day", "week", "month", "quarter"],
        help="Time bucket for markdown grouping",
    )
    parser.add_argument(
        "--output-markdown",
        default=str(repo_root / "documentation" / "changelog.md"),
        help="Markdown changelog output path",
    )
    parser.add_argument(
        "--output-json",
        default=str(repo_root / "documentation" / "changelog.json"),
        help="JSON changelog output path",
    )
    args = parser.parse_args()

    generate_change_log(
        repo_url=args.repo_url,
        start_date=args.start_date,
        end_date=args.end_date,
        output_markdown=Path(args.output_markdown),
        output_json=Path(args.output_json),
        bucket=args.bucket,
    )


if __name__ == "__main__":
    main()
