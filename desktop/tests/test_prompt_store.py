"""手工入库、分类、原文保护与参考采用并发的隔离验证。"""

from hashlib import sha256
from pathlib import Path
import json
import re
import subprocess
import sys

import pytest

DESKTOP = Path(__file__).parents[1]
if str(DESKTOP) not in sys.path:
    sys.path.insert(0, str(DESKTOP))
from prompt_store import PromptStore
from library_init import ensure_library
from reference_store import ReferenceStore
from test_references import prepared


@pytest.fixture
def prompts(tmp_path):
    return PromptStore(tmp_path / "library")


def record_for(prompts, result):
    return json.loads((prompts.root / result["item"]["record_file"]).read_text(encoding="utf-8"))


def test_manual_original_is_preserved_byte_for_byte_and_copy_is_not_called_optimized(prompts):
    original = "\ufeff  原文\r\n保留 {{变量}} 与空白。\r\n  "
    result = prompts.save_prompt({"title": "第一次保存", "original": original})
    record = record_for(prompts, result)
    original_file = prompts.root / result["item"]["original_file"]
    copied_file = prompts.root / result["item"]["optimized_file"]
    assert original_file.read_bytes() == copied_file.read_bytes() == original.encode("utf-8")
    assert record["original"]["sha256"] == sha256(original.encode("utf-8")).hexdigest()
    assert record["versions"][0]["optimization_status"] == "not_optimized"
    assert result["item"]["optimization_status"] == "not_optimized"
    assert record["versions"][0]["evaluation_status"] == "untested"
    assert result["item"]["category_id"] == "uncategorized"
    assert "保存版" in (prompts.root / "INDEX.md").read_text(encoding="utf-8")


def test_provided_optimized_version_does_not_replace_original(prompts):
    result = prompts.save_prompt({"title": "视频提示词", "original": "Original\r\n", "optimized": "改写 {{镜头}}\n", "category_id": "visual", "source_url": "https://example.org/prompt", "source_note": "用户提供来源"})
    record = record_for(prompts, result)
    assert (prompts.root / result["item"]["original_file"]).read_bytes() == b"Original\r\n"
    assert (prompts.root / result["item"]["optimized_file"]).read_text(encoding="utf-8") == "改写 {{镜头}}\n"
    assert record["versions"][0]["optimization_status"] == "provided"
    assert record["source"]["verification_status"] == "user_provided_unverified"
    assert record["source"]["url"] == "https://example.org/prompt"


def test_category_names_are_normalized_case_insensitively_and_use_safe_ids(prompts):
    assert prompts.create_category("  ｕｉ　设计  ")["category"]["id"] == "ui_design"
    assert len(prompts.categories()) == 13
    first = prompts.create_category("  AI 镜头  ", "镜头训练")
    second = prompts.create_category("ai 镜头")
    assert first["created"] is True and second["created"] is False
    assert first["category"]["id"] == second["category"]["id"]
    assert second["category"]["description"] == "镜头训练"
    unusual = prompts.create_category("../../特殊名称")
    assert re.fullmatch(r"custom_[a-f0-9]+", unusual["category"]["id"])
    assert not (prompts.root.parent / "特殊名称").exists()


def test_new_category_and_prompt_are_saved_in_one_consistent_transaction(prompts):
    result = prompts.save_prompt({"title": "分镜", "original": "describe a shot", "category_name": "AI 视频分镜", "tags": ["镜头", "Camera", " camera "]})
    record = record_for(prompts, result)
    category = next(row for row in prompts.categories() if row["id"] == record["category_id"])
    assert category["name"] == "AI 视频分镜"
    assert record["tags"] == ["镜头", "Camera"]
    assert "AI 视频分镜" in (prompts.root / "INDEX.md").read_text(encoding="utf-8")
    assert ensure_library(prompts.root)["entry_count"] == 1


def test_duplicate_original_does_not_mutate_existing_content_or_add_empty_category(prompts):
    first = prompts.save_prompt({"title": "原来的标题", "original": "same text", "category_id": "taste"})
    before = record_for(prompts, first)
    repeated = prompts.save_prompt({"title": "不同标题", "original": "same text", "optimized": "未确认采用的改写", "category_name": "重复输入不应新增的分类"})
    assert repeated["duplicate"] is True and repeated["id"] == first["id"]
    assert record_for(prompts, repeated) == before
    assert len(prompts.categories()) == 13
    assert ensure_library(prompts.root)["entry_count"] == 1


def test_update_metadata_keeps_original_and_version_history_unchanged(prompts):
    first = prompts.save_prompt({"title": "旧标题", "original": "immutable\r\n", "optimized": "保留独立优化版"})
    original_record = record_for(prompts, first)
    folder = prompts.root / "entries" / first["id"]
    original_files = {path.name: path.read_bytes() for path in folder.iterdir() if path.name != "record.json"}
    updated = prompts.update_metadata(first["id"], {"title": "新标题", "category_name": "架构判断", "tags": ["边界", "审核"]})
    record = record_for(prompts, {"item": updated["item"]})
    assert record["title"] == "新标题" and record["tags"] == ["边界", "审核"]
    assert record["versions"] == original_record["versions"]
    assert record["original"] == original_record["original"]
    assert record["source"] == original_record["source"]
    assert original_files == {path.name: path.read_bytes() for path in folder.iterdir() if path.name != "record.json"}
    assert "新标题" in (prompts.root / "INDEX.md").read_text(encoding="utf-8")
    assert ensure_library(prompts.root)["entry_count"] == 1


@pytest.mark.parametrize("body", [
    {"title": "X", "original": ""},
    {"title": "", "original": "Y"},
    {"title": "X", "original": "Y", "category_id": "taste", "category_name": "新分类"},
    {"title": "X", "original": "Y", "category_id": "missing"},
    {"title": "X", "original": "Y", "tags": "wrong"},
    {"title": "X", "original": "Y", "source_url": "javascript:alert(1)"},
    {"title": "X", "original": "Y", "unexpected": "no"},
    {"title": "X", "original": "汉" * 87382},
])
def test_invalid_submission_does_not_create_any_entry(prompts, body):
    with pytest.raises(ValueError):
        prompts.save_prompt(body)
    assert ensure_library(prompts.root)["entry_count"] == 0
    assert len(prompts.categories()) == 13


def test_metadata_route_cannot_edit_original_or_versions(prompts):
    saved = prompts.save_prompt({"title": "Test", "original": "protected"})
    before = record_for(prompts, saved)
    for payload in ({"original": "replace"}, {"optimized": "replace"}, {"versions": []}, {}):
        with pytest.raises(ValueError):
            prompts.update_metadata(saved["id"], payload)
    assert record_for(prompts, saved) == before


def test_save_failure_rolls_back_category_entry_and_both_indexes(prompts, monkeypatch):
    baseline = {path.relative_to(prompts.root): path.read_bytes() for path in prompts.root.rglob("*") if path.is_file()}
    replace = prompts._store._replace
    writes = []

    def fail_late(staging, target):
        writes.append(target)
        if len(writes) == 7:
            raise OSError("simulated disk failure")
        replace(staging, target)

    monkeypatch.setattr(prompts._store, "_replace", fail_late)
    with pytest.raises(OSError, match="simulated"):
        prompts.save_prompt({"title": "Unfinished", "original": "should roll back", "category_name": "回滚测试分类"})
    after = {path.relative_to(prompts.root): path.read_bytes() for path in prompts.root.rglob("*") if path.is_file()}
    assert after == baseline
    assert len(prompts.categories()) == 13


def test_metadata_failure_rolls_back_new_category_and_record(prompts, monkeypatch):
    saved = prompts.save_prompt({"title": "Keep", "original": "history"})
    before = {path.relative_to(prompts.root): path.read_bytes() for path in prompts.root.rglob("*") if path.is_file()}
    replace = prompts._store._replace
    calls = []

    def fail_midway(staging, target):
        calls.append(target)
        if len(calls) == 3:
            raise OSError("simulated metadata failure")
        replace(staging, target)

    monkeypatch.setattr(prompts._store, "_replace", fail_midway)
    with pytest.raises(OSError):
        prompts.update_metadata(saved["id"], {"title": "Changed", "category_name": "临时分类"})
    assert before == {path.relative_to(prompts.root): path.read_bytes() for path in prompts.root.rglob("*") if path.is_file()}


def test_missing_existing_taxonomy_is_not_replaced_by_defaults(prompts):
    prompts.save_prompt({"title": "已有数据", "original": "private prompt"})
    (prompts.root / "taxonomy.json").unlink()
    with pytest.raises(ValueError, match="分类"):
        ensure_library(prompts.root)
    assert not (prompts.root / "taxonomy.json").exists()
    assert (prompts.root / "entries/PRM-0001/original.md").read_bytes() == b"private prompt"


def test_concurrent_manual_and_reference_adoption_share_id_allocation_and_dedup(prompts):
    reference = ReferenceStore(prompts.root)
    ref_id = prepared(reference)
    script = "import sys;sys.path.insert(0,sys.argv[1]);from prompt_store import PromptStore;from reference_store import ReferenceStore;root=sys.argv[2];mode=sys.argv[3];s=PromptStore(root) if mode=='save' else ReferenceStore(root);p=None if mode=='save' else s.adoption_preview(sys.argv[4]);print(s.save_prompt({'title':'manual','original':'A separate user submission'}) if mode=='save' else s.adopt(sys.argv[4],expected_snapshot=p['snapshot_id'],expected_analysis_version=p['analysis_version']))"
    processes = [subprocess.Popen([sys.executable, "-c", script, str(DESKTOP), str(prompts.root), mode, ref_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace") for mode in ("save", "adopt", "save", "adopt")]
    outputs = [process.communicate(timeout=40) for process in processes]
    assert all(process.returncode == 0 for process in processes), outputs
    index = json.loads((prompts.root / "index.json").read_text(encoding="utf-8"))
    assert index["entry_count"] == 2
    assert {item["id"] for item in index["entries"]} == {"PRM-0001", "PRM-0002"}
    assert {item["original_sha256"] for item in index["entries"]} == {sha256(b"A separate user submission").hexdigest(), sha256(b"Original\r\nKeep labels.\r\n").hexdigest()}
    assert ensure_library(prompts.root)["entry_count"] == 2
