from pathlib import Path

from scripts.repository_integrity import file_groups


def test_duplicate_detector_groups_exact_content(tmp_path: Path):
    (tmp_path / "a.md").write_text("same\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("same\n", encoding="utf-8")
    (tmp_path / "c.md").write_text("different\n", encoding="utf-8")

    duplicates = file_groups(tmp_path)

    assert len(duplicates) == 1
    paths = {str(path) for path in next(iter(duplicates.values()))}
    assert paths == {"a.md", "b.md"}
