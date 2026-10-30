"""在临时素材库验证版本并发保护、外部拆解绑定与来源追加，保留原文和历史。"""

from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from prompt_store import PromptStore
from server import Library


@pytest.fixture
def store(tmp_path):
    return PromptStore(tmp_path / "library")


def saved(store):
    return store.save_prompt({"title": "测试素材", "original": "原文\r\n", "optimized": "初版建议\n", "source_url": "https://example.org/original", "source_note": "原来源"})


def record(store, entry_id):
    return json.loads((store.root / "entries" / entry_id / "record.json").read_text(encoding="utf-8"))


def analysis_body(store, entry_id, version="v001", text="# 设计拆解\n\n明确目标，保留边界。"):
    detail = Library(store.root).entry(entry_id, version)
    chosen = next(v for v in detail["record"]["versions"] if v["version"] == version)
    return {"version": version, "original_sha256": detail["record"]["original"]["sha256"], "optimized_sha256": chosen["sha256"], "analysis_markdown": text}


def test_append_keeps_original_and_old_analysis_without_inheriting_it(store):
    first = saved(store)
    entry_id = first["id"]
    store.save_analysis(entry_id, analysis_body(store, entry_id))
    before = record(store, entry_id)
    original_bytes = (store.root / first["item"]["original_file"]).read_bytes()
    result = store.append_version(entry_id, {"optimized": "新任务的建议\n", "reason": "替换任务", "expected_version": "v001"})
    after = record(store, entry_id)
    assert result["version"] == "v002" and not result["duplicate"]
    assert after["original"] == before["original"] and after["source"] == before["source"]
    assert (store.root / first["item"]["original_file"]).read_bytes() == original_bytes
    assert all(after["versions"][0][key] == value for key, value in before["versions"][0].items())
    assert after["versions"][0]["loop_review"] == before["loop_review"]
    assert after["versions"][1]["based_on_version"] == "v001"
    assert after["versions"][1]["evaluation_status"] == "untested"
    assert "analysis_file" not in after["versions"][1]
    assert "design_analysis_file" not in after
    library = Library(store.root)
    assert library.entry(entry_id, "v001")["analysis"] == "# 设计拆解\n\n明确目标，保留边界。"
    assert library.entry(entry_id)["analysis"] == ""
    assert library.entry(entry_id)["loop"].get("max_rounds") is None
    index = json.loads((store.root / "index.json").read_text(encoding="utf-8"))
    assert index["entry_count"] == 1 and index["entries"][0]["latest_version"] == "v002"


def test_append_retries_are_idempotent_but_stale_different_content_is_rejected(store):
    entry_id = saved(store)["id"]
    body = {"optimized": "改编二", "reason": "明确输入", "expected_version": "v001"}
    result = store.append_version(entry_id, body)
    before = record(store, entry_id)
    retry = store.append_version(entry_id, body)
    assert retry["duplicate"] and retry["version"] == result["version"]
    assert record(store, entry_id) == before
    with pytest.raises(ValueError, match="最新版本"):
        store.append_version(entry_id, {**body, "optimized": "另一个改编"})
    assert record(store, entry_id) == before
    third = store.append_version(entry_id, {**body, "optimized": "从初版重新改写", "expected_version": "v002", "based_on_version": "v001"})
    assert third["version"] == "v003"
    assert record(store, entry_id)["versions"][-1]["based_on_version"] == "v001"


def test_append_preserves_legacy_record_level_analysis_on_old_version(store):
    entry_id = saved(store)["id"]
    folder = store.root / "entries" / entry_id
    before = record(store, entry_id)
    before["design_analysis_file"] = "legacy-analysis.md"
    before["loop_review"] = {"reviewed_version": "v001", "max_rounds": 2}
    (folder / "legacy-analysis.md").write_bytes("初版历史拆解".encode("utf-8"))
    (folder / "record.json").write_text(json.dumps(before, ensure_ascii=False), encoding="utf-8")
    store.append_version(entry_id, {"optimized": "新改编", "reason": "切换任务", "expected_version": "v001"})
    old = Library(store.root).entry(entry_id, "v001")
    latest = Library(store.root).entry(entry_id)
    assert old["analysis"] == "初版历史拆解" and old["loop"]["max_rounds"] == 2
    assert latest["analysis"] == "" and latest["loop"].get("max_rounds") is None
    assert (folder / "legacy-analysis.md").read_bytes() == "初版历史拆解".encode("utf-8")


def test_concurrent_different_edits_have_one_winner(store):
    entry_id = saved(store)["id"]
    def edit(text):
        try:
            return store.append_version(entry_id, {"optimized": text, "reason": "并发编辑", "expected_version": "v001"})
        except ValueError as error:
            return {"error": str(error)}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(edit, ["编辑甲", "编辑乙"]))
    assert sum("error" not in result for result in results) == 1
    assert len(record(store, entry_id)["versions"]) == 2


def test_analysis_requires_exact_version_and_both_body_hashes(store):
    entry_id = saved(store)["id"]
    body = analysis_body(store, entry_id)
    before = record(store, entry_id)
    for field in ("original_sha256", "optimized_sha256"):
        with pytest.raises(ValueError, match="校验|哈希"):
            store.save_analysis(entry_id, {**body, field: "0" * 64})
    with pytest.raises((ValueError, KeyError)):
        store.save_analysis(entry_id, {**body, "version": "v999"})
    assert record(store, entry_id) == before


def test_analysis_revisions_are_immutable_idempotent_and_read_per_version(store):
    entry_id = saved(store)["id"]
    body = analysis_body(store, entry_id)
    first = store.save_analysis(entry_id, body)
    after_first = record(store, entry_id)
    assert first["analysis_revision"] == "a001"
    retry = store.save_analysis(entry_id, body)
    assert retry["duplicate"] and record(store, entry_id) == after_first
    old_file = after_first["versions"][0]["analysis_revisions"][0]["file"]
    old_bytes = (store.root / "entries" / entry_id / old_file).read_bytes()
    second = store.save_analysis(entry_id, {**body, "analysis_markdown": "第二次拆解，包含反例。"})
    assert second["analysis_revision"] == "a002"
    assert (store.root / "entries" / entry_id / old_file).read_bytes() == old_bytes
    assert len(record(store, entry_id)["versions"][0]["analysis_revisions"]) == 2
    retry_after_newer_revision = store.save_analysis(entry_id, body)
    assert retry_after_newer_revision["analysis_revision"] == "a001"
    assert retry_after_newer_revision["current_analysis_revision"] == "a002"
    assert Library(store.root).entry(entry_id)["analysis"] == "第二次拆解，包含反例。"
    store.append_version(entry_id, {"optimized": "改编二", "reason": "新任务", "expected_version": "v001"})
    assert Library(store.root).entry(entry_id, "v001")["analysis"] == "第二次拆解，包含反例。"
    assert Library(store.root).entry(entry_id, "v002")["analysis"] == ""
    assert record(store, entry_id)["evaluation_status"] == "untested"


def test_explicit_analysis_takes_precedence_over_bundled_teaching(store, monkeypatch):
    entry_id = saved(store)["id"]
    monkeypatch.setattr("server.teaching_card", lambda *args: {"status": "ready", "markdown": "随应用发布的旧拆解", "revision": "v001"})
    store.save_analysis(entry_id, analysis_body(store, entry_id, text="用户的外部AI客户端提供的新拆解"))
    detail = Library(store.root).entry(entry_id)
    assert detail["analysis"] == "用户的外部AI客户端提供的新拆解"
    assert detail["analysis_status"] == "ready"
    assert detail["analysis_origin"] == "external_client"


@pytest.mark.parametrize("tamper", ["analysis", "optimized", "missing_analysis", "invalid_utf8"])
def test_analysis_readback_does_not_apply_tampered_or_stale_content(store, tamper):
    entry_id = saved(store)["id"]
    store.save_analysis(entry_id, analysis_body(store, entry_id))
    version = record(store, entry_id)["versions"][0]
    file = version["file"] if tamper == "optimized" else version["analysis_file"]
    path = store.root / "entries" / entry_id / file
    if tamper == "missing_analysis":
        path.unlink()
    elif tamper == "invalid_utf8":
        path.write_bytes(b"\xff\xfe")
    else:
        path.write_text("手动改过的正文", encoding="utf-8")
    detail = Library(store.root).entry(entry_id)
    assert detail["original"] == "原文\r\n"
    assert detail["analysis"] == ""
    assert detail["analysis_status"] == ("version_mismatch" if tamper == "optimized" else "unavailable")


def test_source_notes_append_without_rewriting_fixed_source_or_versions(store):
    entry_id = saved(store)["id"]
    before = record(store, entry_id)
    body = {"source_url": "https://example.org/addition", "source_note": "这是补充信息，尚未核实。"}
    first = store.add_source_note(entry_id, body)
    after = record(store, entry_id)
    assert not first["duplicate"]
    assert after["source"] == before["source"] and after["versions"] == before["versions"]
    assert after["original"] == before["original"]
    assert set(after["source_notes"][0]) == {"id", "source_url", "source_note", "created_at"}
    assert store.add_source_note(entry_id, body)["duplicate"]
    assert record(store, entry_id) == after
    store.add_source_note(entry_id, {"source_note": "另一项没有链接的补充"})
    assert len(record(store, entry_id)["source_notes"]) == 2
    assert record(store, entry_id)["source_notes"][-1]["source_url"] == ""
    with pytest.raises(ValueError):
        store.add_source_note(entry_id, {"source_url": "javascript:alert(1)", "source_note": "不能成为链接"})


@pytest.mark.parametrize("method", ["append_version", "save_analysis", "add_source_note"])
def test_new_operations_roll_back_record_and_indexes_on_io_failure(store, monkeypatch, method):
    entry_id = saved(store)["id"]
    body = {"append_version": {"optimized": "新版本", "reason": "测试回滚", "expected_version": "v001"},
            "save_analysis": analysis_body(store, entry_id),
            "add_source_note": {"source_note": "回滚来源"}}[method]
    before = {str(p.relative_to(store.root)): p.read_bytes() for p in store.root.rglob("*") if p.is_file()}
    replace = store._store._replace
    calls = []
    def fail(staging, target):
        calls.append(target)
        if len(calls) == 2:
            raise OSError("simulated failure")
        replace(staging, target)
    monkeypatch.setattr(store._store, "_replace", fail)
    with pytest.raises(OSError):
        getattr(store, method)(entry_id, body)
    assert before == {str(p.relative_to(store.root)): p.read_bytes() for p in store.root.rglob("*") if p.is_file()}
