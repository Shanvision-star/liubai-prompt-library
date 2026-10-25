"""参考快照、许可、采用和跨进程写入的隔离验证，不读取或修改真实素材。"""

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys

import pytest


MODULE = Path(__file__).parents[1] / "reference_store.py"
spec = importlib.util.spec_from_file_location("reference_store", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ReferenceStore = module.ReferenceStore


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def store(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    save_json(root / "index.json", {"schema_version": 1, "entry_count": 0, "entries": []})
    save_json(root / "taxonomy.json", {"categories": [{"id": "taste", "name": "审美 Taste"}, {"id": "ui_design", "name": "UI 设计"}, {"id": "uncategorized", "name": "待分类"}]})
    (root / "README.md").write_text("# 素材库\n已收录实际提示词 0 条。\n当前已有 0 条素材。\n", encoding="utf-8")
    return ReferenceStore(root)


def source(commit="a" * 40, path="skills/design.md", license_status="allowed", repository="owner/design"):
    return {"repository": repository, "path": path, "commit": commit, "url": f"https://github.com/{repository}/blob/{commit}/{path}",
            "tracked_ref": "main", "license": "MIT", "license_status": license_status, "retrieved_at": "2026-10-25T09:00:00+08:00", "license_text": "Copyright Example\nMIT license text"}


def analysis(template="请为 {{任务}} 保留必要标签，最多两轮核验。"):
    return {
        "use_cases": "整理现有 UI 的文案。", "not_for": "不可删除必要表单标签。",
        "structure": [{"part": "目标", "observation": "删减冗余", "evidence": "首句"}],
        "key_sentences": [{"quote": "保留标签", "location": "第 2 行", "reason": "防止误删", "without": "可能无法理解控件"}],
        "design_reasoning": {"author_stated": "保留标签", "inferred": "意在减少理解成本", "evidence": "原文指令，未进行用户试验"},
        "template": template, "example": {"task": "搜索页", "prompt": "保留搜索控件名称", "changes": "限定场景", "status": "illustrative"},
        "counterexample": {"before": "删除所有标签", "after": "保留必要标签", "changed_variable": "标签保留范围", "expected_effect": "预期减少误删", "status": "illustrative"},
        "loop": {"applicability": "conditional", "max_rounds": 2, "text": "最多 2 轮，发现问题后修正；达标或无新证据停止。"},
        "quality_review": {key: {"status": "reviewed", "note": "文本结构审核，效果未实测"} for key in ("goal_clarity", "input_clarity", "constraint_quality", "output_checkability", "usage_evidence", "task_fit")},
        "maturity": {"status": "candidate", "reason": "有明确版本与维护方"}, "fit": {"status": "matched", "reason": "与 UI 文案有关"},
        "evidence": {"status": "published_instruction", "reason": "原作者公开指令，无本库实测"},
    }


def prepared(store, raw=b"Original\r\nKeep labels.\r\n", **kwargs):
    result = store.ingest(source(**kwargs), raw, {"title": "界面减法", "category_id": "ui_design", "tags": ["文案"], "selection_status": "selected"})
    store.set_analysis(result["id"], result["snapshot_id"], analysis())
    return result["id"]


def adopt_preview(store, ref_id, target_id=None):
    preview = store.adoption_preview(ref_id, target_id)
    return store.adopt(ref_id, target_id, preview["snapshot_id"], preview["analysis_version"])


def test_original_bytes_and_source_commit_are_preserved(store):
    raw = b"\xef\xbb\xbfOriginal\r\nKeep labels.\r\n"
    ref_id = prepared(store, raw)
    detail = store.detail(ref_id)
    snapshot = detail["snapshot"]
    assert (store.directory / ref_id / snapshot["original_file"]).read_bytes() == raw
    assert snapshot["sha256"] == sha256(raw).hexdigest()
    assert snapshot["byte_count"] == len(raw)
    assert snapshot["commit"] == "a" * 40
    assert detail["analysis"]["evaluation_status"] == "untested"


def test_same_source_same_content_is_idempotent_even_with_new_commit(store):
    ref_id = prepared(store)
    original_analysis = store.detail(ref_id)["analysis"]
    result = store.ingest(source(commit="b" * 40), b"Original\r\nKeep labels.\r\n")
    detail = store.detail(ref_id)
    assert result == {"id": ref_id, "duplicate": True, "changed": False, "snapshot_id": "s001"}
    assert len(detail["snapshots"]) == 1
    assert detail["snapshot"]["commit"] == "a" * 40
    assert detail["item"]["source"]["commit"] == "b" * 40
    assert detail["analysis"] == original_analysis


def test_changed_snapshot_pending_keeps_prior_analysis_and_diff(store):
    ref_id = prepared(store)
    old_analysis = store.detail(ref_id)["analysis"]
    result = store.ingest(source(commit="b" * 40), "Changed\nKeep labels.\n")
    detail = store.detail(ref_id)
    assert result["changed"] is True
    assert detail["snapshot"]["id"] == "s002"
    assert detail["analysis"] is None
    assert detail["item"]["analysis_status"] == "pending"
    assert "-Original" in detail["diff"]["text"]
    assert "+Changed" in detail["diff"]["text"]
    assert store.detail(ref_id, "s001")["analysis"] == old_analysis
    store.set_analysis(ref_id, "s001", analysis("重新解释旧版本"))
    assert store.detail(ref_id)["item"]["analysis_status"] == "pending"


def test_analysis_is_immutable_versioned_and_repeat_is_idempotent(store):
    ref_id = prepared(store)
    old_path = store.directory / ref_id / "analyses/a001.json"
    before = old_path.read_bytes()
    detail = store.set_analysis(ref_id, "s001", analysis())
    assert detail["analysis"]["version"] == "a001"
    changed = analysis("修订后的模板")
    changed["evaluation_status"] = "tested"
    detail = store.set_analysis(ref_id, "s001", changed)
    assert detail["analysis"]["version"] == "a002"
    assert detail["analysis"]["evaluation_status"] == "untested"
    assert old_path.read_bytes() == before


def test_same_content_from_another_repository_adds_provenance_not_duplicate(store):
    ref_id = prepared(store)
    result = store.ingest(source(repository="other/design"), b"Original\r\nKeep labels.\r\n")
    assert result["id"] == ref_id
    assert result["duplicate"] is True
    assert len(store.catalogue()["references"]) == 1
    assert store.detail(ref_id)["item"]["alternate_sources"][0]["repository"] == "other/design"


def test_flags_persist_and_failed_check_does_not_change_last_success(store):
    ref_id = prepared(store)
    store.set_flags(ref_id, favorite=True, followed=True)
    before = store.detail(ref_id)["item"]["last_success"]
    store.record_check(ref_id, "failed", "2026-10-26T09:00:00+08:00", "网络断开")
    reopened = ReferenceStore(store.root).detail(ref_id)["item"]
    assert reopened["favorite"] is True and reopened["followed"] is True
    assert reopened["last_success"] == before
    assert reopened["last_attempt"] == "2026-10-26T09:00:00+08:00"
    assert reopened["last_error"] == "网络断开"
    with pytest.raises(ValueError):
        store.set_flags(ref_id, favorite="true")


@pytest.mark.parametrize("license_status", ["unknown", "restricted"])
def test_unconfirmed_license_does_not_archive_original_or_allow_adoption(store, license_status):
    ref_id = prepared(store, license_status=license_status)
    detail = store.detail(ref_id)
    assert detail["original"] is None
    assert detail["snapshot"]["original_file"] is None
    preview = store.adoption_preview(ref_id)
    assert preview["can_adopt"] is False
    with pytest.raises(ValueError, match="许可"):
        adopt_preview(store, ref_id)
    assert store._personal_index()["entries"] == []


def test_verified_license_can_fill_original_without_losing_flags_or_analysis(store):
    ref_id = prepared(store, license_status="unknown")
    store.set_flags(ref_id, favorite=True, followed=True)
    permitted = source()
    permitted["license_evidence"] = "已检查具体文件与仓库 MIT 许可"
    result = store.ingest(permitted, b"Original\r\nKeep labels.\r\n", {"selection_status": "selected", "related_ids": ["PRM-0001"], "quality_review": {"evidence": "reviewed"}})
    detail = store.detail(ref_id)
    assert result["snapshot_id"] == "s001"
    assert detail["original"] == "Original\r\nKeep labels.\r\n"
    assert detail["item"]["favorite"] and detail["item"]["followed"]
    assert detail["analysis"]["version"] == "a001"
    assert detail["snapshot"]["source"]["license_evidence"] == permitted["license_evidence"]
    assert store.adoption_preview(ref_id)["can_adopt"]


def test_adopt_creates_complete_entry_and_syncs_indexes(store):
    ref_id = prepared(store)
    result = adopt_preview(store, ref_id)
    assert result["entry_id"] == "PRM-0001" and result["version"] == "v001"
    index = json.loads((store.root / "index.json").read_text(encoding="utf-8"))
    assert index["entry_count"] == len(index["entries"]) == 1
    row = index["entries"][0]
    personal = json.loads((store.root / row["record_file"]).read_text(encoding="utf-8"))
    assert (store.root / row["original_file"]).read_bytes() == b"Original\r\nKeep labels.\r\n"
    assert (store.root / row["optimized_file"]).read_text(encoding="utf-8") == analysis()["template"]
    assert personal["versions"][0]["reference_provenance"]["snapshot_id"] == "s001"
    assert personal["versions"][0]["evaluation_status"] == "untested"
    assert "PRM-0001" in (store.root / "INDEX.md").read_text(encoding="utf-8")
    assert "已收录实际提示词 1 条" in (store.root / "README.md").read_text(encoding="utf-8")
    assert adopt_preview(store, ref_id)["duplicate"] is True
    assert len(store._personal_index()["entries"]) == 1


def test_adopt_new_version_preserves_original_and_prior_personal_files(store):
    ref_id = prepared(store)
    result = adopt_preview(store, ref_id)
    folder = store.root / "entries" / result["entry_id"]
    before = {path.name: path.read_bytes() for path in folder.iterdir() if path.name != "record.json"}
    store.ingest(source(commit="b" * 40), b"New source\n")
    store.set_analysis(ref_id, "s002", analysis("改编新版模板"))
    result = adopt_preview(store, ref_id, "PRM-0001")
    assert result["version"] == "v002"
    for name, payload in before.items():
        assert (folder / name).read_bytes() == payload
    personal = json.loads((folder / "record.json").read_text(encoding="utf-8"))
    assert len(personal["versions"]) == 2
    assert personal["versions"][-1]["reference_provenance"]["source_commit"] == "b" * 40
    assert store._personal_index()["entry_count"] == 1


def test_stale_preview_and_missing_confirmation_are_rejected(store):
    ref_id = prepared(store)
    preview = store.adoption_preview(ref_id)
    store.set_analysis(ref_id, "s001", analysis("更正后的模板"))
    with pytest.raises(ValueError, match="已更新"):
        store.adopt(ref_id, expected_snapshot=preview["snapshot_id"], expected_analysis_version=preview["analysis_version"])
    with pytest.raises(ValueError, match="预览"):
        store.adopt(ref_id)
    assert store._personal_index()["entry_count"] == 0


def test_existing_source_hash_is_adopted_as_existing_entry_new_version(store):
    ref_id = prepared(store)
    adopt_preview(store, ref_id)
    record_path = store.root / "entries/PRM-0001/record.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["versions"][0].pop("reference_provenance")
    record["versions"][0].pop("template_sha256")
    save_json(record_path, record)
    store.set_analysis(ref_id, "s001", analysis("参考改写的第二版"))
    preview = store.adoption_preview(ref_id)
    assert preview["target_id"] == preview["existing_entry_id"] == "PRM-0001"
    assert preview["action"] == "new_version"
    assert adopt_preview(store, ref_id)["version"] == "v002"
    assert len(store._personal_index()["entries"]) == 1


def test_transaction_failure_rolls_back_personal_and_reference_indexes(store, monkeypatch):
    ref_id = prepared(store)
    before = {p.relative_to(store.root): p.read_bytes() for p in store.root.rglob("*") if p.is_file() and p.name != ".store.lock"}
    original_replace = store._replace
    calls = []

    def fail_after_some_writes(staging, target):
        calls.append(target)
        if len(calls) == 6:
            raise OSError("injected disk failure")
        original_replace(staging, target)

    monkeypatch.setattr(store, "_replace", fail_after_some_writes)
    with pytest.raises(OSError, match="injected"):
        adopt_preview(store, ref_id)
    after = {p.relative_to(store.root): p.read_bytes() for p in store.root.rglob("*") if p.is_file() and p.name != ".store.lock"}
    assert before == after


def test_restart_recovers_prepared_transaction(store):
    index_path = store.root / "index.json"
    original = index_path.read_bytes()
    folder = store.directory / ".transactions/interrupted"
    folder.mkdir(parents=True)
    (folder / "0.old").write_bytes(original)
    index_path.write_text('{"corrupted":true}', encoding="utf-8")
    new_file = store.root / "entries/PRM-0099/original.md"
    new_file.parent.mkdir(parents=True)
    new_file.write_bytes(b"partial")
    save_json(folder / "manifest.json", {"state": "prepared", "files": [{"path": "index.json", "existed": True, "backup": "0.old"}, {"path": "entries/PRM-0099/original.md", "existed": False, "backup": "1.old"}]})
    ReferenceStore(store.root)
    assert index_path.read_bytes() == original
    assert not new_file.exists()
    assert not folder.exists()


def test_separate_processes_cannot_duplicate_adoption(store):
    ref_id = prepared(store)
    script = "import sys;sys.path.insert(0,sys.argv[1]);from reference_store import ReferenceStore;s=ReferenceStore(sys.argv[2]);p=s.adoption_preview(sys.argv[3]);print(s.adopt(sys.argv[3],expected_snapshot=p['snapshot_id'],expected_analysis_version=p['analysis_version']))"
    child_environment = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    workers = [subprocess.Popen([sys.executable, "-X", "utf8", "-c", script, str(MODULE.parent), str(store.root), ref_id], env=child_environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace") for _ in range(3)]
    outputs = [worker.communicate(timeout=25) for worker in workers]
    failures = [f"child {number}, exit {worker.returncode}:\n{stderr}" for number, (worker, (_, stderr)) in enumerate(zip(workers, outputs), 1) if worker.returncode != 0]
    assert not failures, "\n\n".join(failures)
    index = store._personal_index()
    assert index["entry_count"] == 1
    record = json.loads((store.root / index["entries"][0]["record_file"]).read_text(encoding="utf-8"))
    assert len(record["versions"]) == 1


def test_recommendations_use_explainable_matching_and_exclude_rejected(store):
    ref_id = prepared(store)
    adopt_preview(store, ref_id)
    store.ingest(source(path="other.md"), b"another source", {"category_id": "taste", "tags": ["unrelated"], "selection_status": "selected"})
    store.ingest(source(path="rejected.md"), b"rejected source", {"category_id": "ui_design", "tags": ["文案"], "selection_status": "rejected"})
    result = store.recommendations("PRM-0001")
    assert [row["id"] for row in result] == [ref_id]
    assert "共同标签" in result[0]["reason"]
    assert "score" not in result[0]


@pytest.mark.parametrize("bad_source", [source(commit="main"), source(path="../escape.md"), {**source(), "url": "https://github.com/owner/design/blob/" + "a" * 40 + "/other.md"}])
def test_invalid_source_is_rejected(store, bad_source):
    with pytest.raises(ValueError):
        store.ingest(bad_source, b"text")


def test_corrupted_original_and_analysis_are_detected(store):
    ref_id = prepared(store)
    path = store.directory / ref_id / "snapshots/s001/original.md"
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="原文校验失败"):
        store.detail(ref_id)
    path.write_bytes(b"Original\r\nKeep labels.\r\n")
    (store.directory / ref_id / "analyses/a001.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="分析版本校验失败"):
        store.detail(ref_id)


def test_paths_in_records_cannot_read_outside_library(store, tmp_path):
    ref_id = prepared(store)
    outside = tmp_path / "private.txt"
    outside.write_text("private", encoding="utf-8")
    record_path = store.directory / ref_id / "record.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["analyses"][0]["file"] = "../../../../private.txt"
    save_json(record_path, record)
    with pytest.raises(ValueError, match="越出"):
        store.detail(ref_id)


def test_empty_download_does_not_replace_source(store):
    ref_id = prepared(store)
    with pytest.raises(ValueError, match="空原文"):
        store.ingest(source(commit="b" * 40), b"")
    assert store.detail(ref_id)["snapshot"]["id"] == "s001"


def test_different_heading_excerpts_in_same_file_are_distinct_references(store):
    first_source = {**source(), "extraction": {"type": "heading", "heading": "Camera motion"}, "source_span": "Camera motion section"}
    second_source = {**source(), "extraction": {"type": "heading", "heading": "Lighting"}, "source_span": "Lighting section"}
    first = store.ingest(first_source, "# Camera motion\nMove camera slowly.\n")
    second = store.ingest(second_source, "# Lighting\nKeep direction consistent.\n")
    assert first["id"] != second["id"]
    assert len(store.catalogue()["references"]) == 2
    first_source.update(commit="b" * 40, url=source(commit="b" * 40)["url"])
    changed = store.ingest(first_source, "# Camera motion\nMove camera slowly and deliberately.\n")
    assert changed["id"] == first["id"] and changed["snapshot_id"] == "s002"
    assert store.detail(second["id"])["snapshot"]["id"] == "s001"


def test_same_body_permission_downgrade_preserves_immutable_old_snapshot(store):
    ref_id = prepared(store)
    old = store.detail(ref_id)
    result = store.ingest(source(commit="b" * 40, license_status="unknown"), b"Original\r\nKeep labels.\r\n")
    assert result["changed"] and result["snapshot_id"] == "s002"
    assert store.detail(ref_id)["analysis"] is None
    assert store.detail(ref_id)["original"] is None
    assert store.detail(ref_id, "s001")["snapshot"] == old["snapshot"]
    assert not store.adoption_preview(ref_id)["can_adopt"]


def test_adoption_saves_loop_per_version_and_updates_new_readme_count_format(store):
    (store.root / "README.md").write_text("**当前状态：0 条个人素材，0 份参考。**", encoding="utf-8")
    ref_id = prepared(store)
    adopt_preview(store, ref_id)
    second = analysis("下一版模板")
    second["loop"]["text"] = "只做一次材料核查。"
    second["loop"]["max_rounds"] = 1
    store.set_analysis(ref_id, "s001", second)
    adopt_preview(store, ref_id)
    personal = json.loads((store.root / "entries/PRM-0001/record.json").read_text(encoding="utf-8"))
    assert personal["versions"][0]["loop_review"]["max_rounds"] == 2
    assert personal["versions"][1]["loop_review"]["max_rounds"] == 1
    assert "当前状态：1 条个人素材" in (store.root / "README.md").read_text(encoding="utf-8")


def test_adoption_backfills_only_matching_prior_loop_and_preserves_legacy_links(store):
    ref_id = prepared(store)
    adopt_preview(store, ref_id)
    path = store.root / "entries/PRM-0001/record.json"
    personal = json.loads(path.read_text(encoding="utf-8"))
    prior = personal["versions"][0]
    prior.pop("analysis_file")
    prior.pop("source_file")
    prior.pop("loop_review")
    old_analysis = personal["design_analysis_file"]
    old_source = personal["source"]["provenance_file"]
    save_json(path, personal)
    store.set_analysis(ref_id, "s001", analysis("新版本"))
    adopt_preview(store, ref_id)
    personal = json.loads(path.read_text(encoding="utf-8"))
    prior = personal["versions"][0]
    assert prior["analysis_file"] == old_analysis and prior["source_file"] == old_source
    assert prior["loop_review"]["reviewed_version"] == "v001"
