"""Repository integrity checks for duplicate content and forbidden generated files."""
from __future__ import annotations

import argparse
import hashlib
from collections import defaultdict
from pathlib import Path

IGNORED_PARTS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", "node_modules"}


def file_groups(root: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        digest = hashlib.sha256(data).hexdigest()
        groups[digest].append(path.relative_to(root))
    return {digest: paths for digest, paths in groups.items() if len(paths) > 1}


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect exact duplicate repository files")
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    duplicates = file_groups(Path(args.root).resolve())
    if not duplicates:
        print("PASS: no exact duplicate file contents found")
        return 0
    print("FAIL: exact duplicate file contents detected")
    for digest, paths in sorted(duplicates.items()):
        print(f"SHA256 {digest}")
        for path in paths:
            print(f"  - {path}")
    print("Resolve duplicates by keeping the canonical source defined in docs/CANONICAL_SOURCES.md.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
