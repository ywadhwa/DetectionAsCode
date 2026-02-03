#!/usr/bin/env python3
"""Spell-check selected metadata fields with an allowlist."""
import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, Set, List

import yaml
from spellchecker import SpellChecker

WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z\-']+")


def load_allowlist(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    return {line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def extract_text(rule: dict) -> Iterable[str]:
    fields = ["title", "description"]
    for field in fields:
        value = rule.get(field)
        if isinstance(value, str):
            yield value
    for entry in rule.get("falsepositives", []) or []:
        if isinstance(entry, str):
            yield entry


def collect_rule_files(repo_root: Path, paths: List[str]) -> List[Path]:
    sigma_rules_dir = repo_root / "sigma-rules"
    if not paths:
        return list(sigma_rules_dir.rglob("*.yml")) + list(sigma_rules_dir.rglob("*.yaml"))

    files: List[Path] = []
    for raw in paths:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        if candidate.is_dir():
            files.extend(candidate.rglob("*.yml"))
            files.extend(candidate.rglob("*.yaml"))
        elif candidate.is_file():
            if candidate.suffix.lower() in {".yml", ".yaml"}:
                files.append(candidate)
        else:
            raise FileNotFoundError(raw)
    return sorted(set(files))


def main() -> None:
    parser = argparse.ArgumentParser(description="Spell-check Sigma rule metadata")
    parser.add_argument("files", nargs="*", help="Optional Sigma rule files or directories")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    allowlist = load_allowlist(repo_root / "config" / "spelling_allowlist.txt")
    spell = SpellChecker()

    try:
        rule_files = collect_rule_files(repo_root, args.files)
    except FileNotFoundError as exc:
        print(f"Error: file or directory not found: {exc}")
        sys.exit(1)

    all_valid = True
    for rule_file in rule_files:
        rule = yaml.safe_load(rule_file.read_text(encoding="utf-8")) or {}
        words = []
        for text in extract_text(rule):
            words.extend(WORD_PATTERN.findall(text))
        misspelled = {w.lower() for w in spell.unknown(words)} - allowlist
        if misspelled:
            all_valid = False
            print(f"✗ {rule_file}")
            print(f"  Misspelled: {', '.join(sorted(misspelled))}")
        else:
            print(f"✓ {rule_file}")

    if not all_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
