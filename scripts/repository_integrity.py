#!/usr/bin/env python3
"""Repository-wide integrity and exact-duplicate detector.

This check deliberately detects exact duplicate file contents without guessing
that similarly named files are duplicates. Ambiguous semantic duplicates remain
a human/diagnostic decision; exact duplicates are safe integrity findings.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

IGNORED_PARTS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", ".venv", "venv", "node_modules"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def _included(path: Path) -> bool:
    return not any(part in IGNORED_PARTS for part in path.parts) and path.suffix not in IGNORED_SUFFIXES


def file_groups(root: Path) -> dict[str, list[Path]]:
    """Group exact duplicate regular files by SHA-256 content hash."""
    groups: dict[str, list[Path]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not _included(path):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        groups.setdefault(digest, []).append(path.relative_to(root))
    return {digest: paths for digest, paths in groups.items() if len(paths) > 1}


def main(argv: list[str] | None = None) -> int:
    root = Path((argv or sys.argv[1:] or ["."])[0]).resolve()
    duplicates = file_groups(root)
    if not duplicates:
        print("repository integrity: OK (no exact duplicate files)")
        return 0

    print("repository integrity: exact duplicate files detected")
    for digest, paths in duplicates.items():
        print(f"  sha256={digest}")
        for path in paths:
            print(f"    - {path}")
    print("Resolve exact duplicates by keeping one canonical source; do not delete ambiguous semantic variants automatically.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
