#!/usr/bin/env python3
"""Generate a changelog from git history."""
import os
import subprocess
from collections import defaultdict
from pathlib import Path


def run_git(args):
    return subprocess.check_output(["git"] + args, text=True).strip()


def main() -> None:
    repo_root = Path(__file__).parent.parent
    repo_url = os.getenv("REPO_URL", "")
    if not repo_url:
        repo_url = run_git(["config", "--get", "remote.origin.url"]) or ""
        repo_url = repo_url.replace("git@github.com:", "https://github.com/").replace(".git", "")

    log_output = run_git(["log", "--name-status", "--pretty=format:%H|%an|%ad|%s", "--date=short"])
    entries = log_output.split("\n")
    changes = defaultdict(list)
    current_commit = None

    for line in entries:
        if "|" in line and line.count("|") >= 3:
            sha, author, date, subject = line.split("|", 3)
            current_commit = {
                "sha": sha,
                "author": author,
                "date": date,
                "subject": subject,
                "files": []
            }
            changes["commits"].append(current_commit)
        elif current_commit and line:
            status, path = line.split("\t", 1)
            normalized_status = status[0]
            current_commit["files"].append((normalized_status, path))

    changelog_lines = ["# Changelog", ""]
    for commit in changes["commits"]:
        link = f"{repo_url}/commit/{commit['sha']}" if repo_url else commit["sha"]
        changelog_lines.append(f"## {commit['date']} - {commit['subject']}")
        changelog_lines.append(f"- Author: {commit['author']}")
        changelog_lines.append(f"- Commit: {link}")
        buckets = defaultdict(list)
        for status, path in commit["files"]:
            if path.startswith("sigma-rules/"):
                buckets["detections"].append((status, path))
            else:
                buckets["other"].append((status, path))
        for bucket, items in buckets.items():
            changelog_lines.append(f"- {bucket}:")
            for status, path in items:
                action = {"A": "added", "M": "modified", "D": "deleted", "R": "moved"}.get(status, status)
                changelog_lines.append(f"  - {action}: {path}")
        changelog_lines.append("")

    output_path = repo_root / "documentation" / "changelog.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(changelog_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
