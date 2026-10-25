"""空库启动和不完整库保护的隔离验证，默认模板不含个人素材。"""

from pathlib import Path
import json
import subprocess
import sys

import pytest

DESKTOP = Path(__file__).parents[1]
if str(DESKTOP) not in sys.path:
    sys.path.insert(0, str(DESKTOP))
from library_init import ensure_library, DEFAULT_TAXONOMY
from reference_store import ReferenceStore


def test_empty_root_bootstraps_thirteen_categories_without_personal_content(tmp_path):
    root = tmp_path / "empty"
    result = ensure_library(root)
    taxonomy = json.loads((root / "taxonomy.json").read_text(encoding="utf-8"))
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    assert len(taxonomy["categories"]) == 13
    assert index["entries"] == [] and index["entry_count"] == 0
    assert result["entry_count"] == 0
    assert set(result["created"]) == {"taxonomy.json", "index.json", "INDEX.md"}
    assert (root / "entries").is_dir() and not list((root / "entries").iterdir())
    assert "实际素材：**0 条**" in (root / "INDEX.md").read_text(encoding="utf-8")
    assert json.loads(DEFAULT_TAXONOMY.read_text(encoding="utf-8")) == taxonomy


def test_existing_custom_taxonomy_and_program_readme_are_preserved(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    custom = b'{"categories":[{"id":"my_category","name":"Custom"}]}'
    (root / "taxonomy.json").write_bytes(custom)
    (root / "README.md").write_bytes(b"Application documentation\r\n")
    ensure_library(root)
    before = {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()}
    assert ensure_library(root)["created"] == []
    assert (root / "taxonomy.json").read_bytes() == custom
    assert before == {path.name: path.read_bytes() for path in root.iterdir() if path.is_file()}


def test_missing_index_with_existing_material_is_not_reset(tmp_path):
    root = tmp_path / "library"
    original = root / "entries/PRM-0001/original.md"
    original.parent.mkdir(parents=True)
    original.write_bytes(b"Do not discard")
    with pytest.raises(ValueError, match="index.json"):
        ensure_library(root)
    assert original.read_bytes() == b"Do not discard"
    assert not (root / "index.json").exists()


def test_existing_directory_document_without_machine_index_is_not_overwritten(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    (root / "INDEX.md").write_bytes(b"Existing hand-maintained directory")
    with pytest.raises(ValueError):
        ensure_library(root)
    assert (root / "INDEX.md").read_bytes() == b"Existing hand-maintained directory"
    assert not (root / "index.json").exists()


def test_corrupt_index_is_preserved_for_repair(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    (root / "index.json").write_bytes(b"{broken")
    with pytest.raises(ValueError, match="格式异常"):
        ensure_library(root)
    assert (root / "index.json").read_bytes() == b"{broken"


def test_inconsistent_count_and_unindexed_files_are_rejected(tmp_path):
    root = tmp_path / "library"
    ensure_library(root)
    index_path = root / "index.json"
    original_index = index_path.read_bytes()
    data = json.loads(original_index)
    data["entry_count"] = 10
    index_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="数量"):
        ensure_library(root)
    index_path.write_bytes(original_index)
    orphan = root / "entries/PRM-0123/original.md"
    orphan.parent.mkdir(parents=True)
    orphan.write_bytes(b"orphaned but valuable")
    with pytest.raises(ValueError, match="未被索引"):
        ensure_library(root)
    assert orphan.read_bytes() == b"orphaned but valuable"


def test_initialization_failure_rolls_back_new_files(tmp_path, monkeypatch):
    root = tmp_path / "library"
    original_replace = ReferenceStore._replace
    calls = []

    def broken_replace(self, staging, target):
        calls.append(target)
        if len(calls) == 2:
            raise OSError("simulated write failure")
        original_replace(self, staging, target)

    monkeypatch.setattr(ReferenceStore, "_replace", broken_replace)
    with pytest.raises(OSError, match="simulated"):
        ensure_library(root)
    assert not any((root / name).exists() for name in ("index.json", "taxonomy.json", "INDEX.md"))
    monkeypatch.setattr(ReferenceStore, "_replace", original_replace)
    assert ensure_library(root)["entry_count"] == 0


def test_separate_processes_initialize_same_empty_root_consistently(tmp_path):
    root = tmp_path / "shared"
    script = "import sys;sys.path.insert(0,sys.argv[1]);from library_init import ensure_library;print(ensure_library(sys.argv[2])['entry_count'])"
    children = [subprocess.Popen([sys.executable, "-c", script, str(DESKTOP), str(root)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(3)]
    outputs = [child.communicate(timeout=30) for child in children]
    assert all(child.returncode == 0 for child in children), outputs
    assert all(stdout.strip() == "0" for stdout, _ in outputs)
    assert len(json.loads((root / "taxonomy.json").read_text(encoding="utf-8"))["categories"]) == 13
    assert ensure_library(root)["created"] == []
