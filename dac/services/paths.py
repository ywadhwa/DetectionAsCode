"""Repository path helpers shared by wrappers and services."""
from __future__ import annotations

from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    """Find repository root by walking upward from *start* or this file."""
    probe = (start or Path(__file__)).resolve()
    for parent in [probe.parent, *probe.parents]:
        if (parent / ".git").exists() or (parent / "requirements.txt").exists():
            return parent
    return probe.parent


def sigma_rules_dir(root: Path | None = None) -> Path:
    """Return sigma-rules path under repository root."""
    return (root or repo_root()) / "sigma-rules"


def artifacts_dir(root: Path | None = None) -> Path:
    """Return default artifact root used by machine-readable outputs."""
    return (root or repo_root()) / "output" / "artifacts"
