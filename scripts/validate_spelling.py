#!/usr/bin/env python3
"""Spell-check selected metadata fields with an allowlist."""
import re
import sys
from pathlib import Path
from typing import Iterable, Set

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


def main() -> None:
    repo_root = Path(__file__).parent.parent
    allowlist = load_allowlist(repo_root / "config" / "spelling_allowlist.txt")
    spell = SpellChecker()

    all_valid = True
    for rule_file in (repo_root / "sigma-rules").rglob("*.yml"):
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
