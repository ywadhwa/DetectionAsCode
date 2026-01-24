#!/usr/bin/env python3
"""Generate release notes between tags."""
import subprocess
from pathlib import Path


def run_git(args):
    return subprocess.check_output(["git"] + args, text=True).strip()


def main() -> None:
    tags = run_git(["tag", "--sort=-creatordate"]).splitlines()
    if len(tags) < 2:
        print("Not enough tags to generate release notes")
        return
    current_tag = tags[0]
    previous_tag = tags[1]
    log = run_git(["log", f"{previous_tag}..{current_tag}", "--pretty=format:* %h %s (%an)"])
    output = [f"# Release Notes: {current_tag}", "", f"Changes since {previous_tag}:", "", log, ""]
    output_path = Path(__file__).parent.parent / "documentation" / "release-notes.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(output), encoding="utf-8")


if __name__ == "__main__":
    main()
