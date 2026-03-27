#!/usr/bin/env python3
"""Run a lightweight spelling check with codespell."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List


def resolve_targets(args: Iterable[str], repo_root: Path) -> List[str]:
    """Resolve validate.sh arguments against the repo root."""
    if not args:
        return [str(repo_root / "sigma-rules")]

    targets: List[str] = []
    for arg in args:
        path = Path(arg)
        if not path.is_absolute():
            path = repo_root / path
        targets.append(str(path))
    return targets


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent

    if not shutil.which("codespell"):
        print("codespell is required. Install it with: pip install codespell")
        sys.exit(1)

    targets = resolve_targets(sys.argv[1:], repo_root)  # validate.sh forwards $@

    command = [
        "codespell",
        "--quiet-level=2",
    ]

    ignore_file = repo_root / "config" / "spelling_allowlist.txt"
    if not ignore_file.exists():
        # Backward-compat fallback for older filename.
        ignore_file = repo_root / "config" / "codespell_ignore.txt"
    if ignore_file.exists():
        command.append(f"--ignore-words={ignore_file}")  # optional ignore list for security vocab

    # codespell focuses on common typos with a low false-positive baseline.
    command.extend(targets)

    result = subprocess.run(command, check=False)

    if result.returncode == 0:
        print("✓ No spelling issues found.")
        return
    if result.returncode == 65:
        print("✗ Spelling issues found.")
        sys.exit(1)

    print("✗ codespell failed to run.")
    sys.exit(1)


if __name__ == "__main__":
    main()
