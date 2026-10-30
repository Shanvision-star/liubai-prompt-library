"""用真实子进程验证 MCP 握手、工具调用、原文回读及错误恢复；仅使用临时素材库。"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


PROJECT = Path(__file__).resolve().parents[2]
ENTRYPOINT = PROJECT / "desktop" / "mcp_server.py"


def request(identifier, method, params=None):
    result = {"jsonrpc": "2.0", "id": identifier, "method": method}
    if params is not None:
        result["params"] = params
    return result


def initialize(version="2025-06-18"):
    return request(1, "initialize", {"protocolVersion": version, "capabilities": {}, "clientInfo": {"name": "liubai-pytest", "version": "1.0"}})


READY = {"jsonrpc": "2.0", "method": "notifications/initialized"}


def call(identifier, name, arguments=None):
    return request(identifier, "tools/call", {"name": name, "arguments": arguments or {}})


def exchange(tmp_path, messages):
    root = tmp_path / "private library"
    wire = b"".join(message + b"\n" if isinstance(message, bytes) else (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8") for message in messages)
    completed = subprocess.run([sys.executable, "-X", "utf8", str(ENTRYPOINT), "--data-root", str(root)],
                               input=wire, capture_output=True, timeout=20, cwd=tmp_path)
    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    assert completed.stderr == b"", completed.stderr
    lines = completed.stdout.splitlines()
    responses = [json.loads(line) for line in lines]
    assert all(response.get("jsonrpc") == "2.0" for response in responses)
    return root, responses


def by_id(responses, identifier):
    return next(response for response in responses if response["id"] == identifier)


def structured(responses, identifier):
    result = by_id(responses, identifier)["result"]
    assert result["isError"] is False, result
    assert json.loads(result["content"][0]["text"]) == result["structuredContent"]
    return result["structuredContent"]


def test_external_client_reads_adapts_saves_analysis_and_reads_back_versions(tmp_path):
    original, optimized, adapted = "原文\r\n", "初版建议\n", "针对新任务的建议\r\n"
    digest = lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()
    analysis = {"entry_id": "PRM-0001", "version": "v001", "original_sha256": digest(original), "optimized_sha256": digest(optimized), "analysis_markdown": "初版设计拆解，效果未验证。"}
    version = {"entry_id": "PRM-0001", "optimized": adapted, "reason": "适配用户的新任务", "expected_version": "v001"}
    _, responses = exchange(tmp_path, [
        initialize(), READY,
        call(2, "liubai_save_prompt", {"title": "外部客户端闭环", "original": original, "optimized": optimized, "source_url": "https://example.org/fixed"}),
        call(3, "liubai_get_prompt", {"entry_id": "PRM-0001"}),
        call(4, "liubai_save_analysis", analysis),
        call(5, "liubai_add_version", version),
        call(6, "liubai_add_version", version),
        call(7, "liubai_add_version", {**version, "optimized": "来自过期基线的另一份编辑"}),
        call(8, "liubai_add_source_note", {"entry_id": "PRM-0001", "source_note": "用户补充的场景约束。"}),
        call(9, "liubai_get_prompt", {"entry_id": "PRM-0001"}),
        call(10, "liubai_get_prompt", {"entry_id": "PRM-0001", "version": "v001"}),
        call(11, "liubai_save_analysis", {**analysis, "version": "v002"}),
        call(12, "liubai_save_analysis", {**analysis, "version": "v002", "optimized_sha256": digest(adapted), "analysis_markdown": "新任务拆解，效果未验证。"}),
        call(13, "liubai_get_prompt", {"entry_id": "PRM-0001", "version": "v002"}),
    ])
    before = structured(responses, 3)
    assert before["original_sha256"] == digest(original) and before["optimized_sha256"] == digest(optimized)
    assert structured(responses, 4)["analysis_revision"] == "a001"
    assert structured(responses, 5)["version"] == "v002" and structured(responses, 6)["duplicate"]
    assert by_id(responses, 7)["result"]["isError"] and "最新版本" in by_id(responses, 7)["result"]["content"][0]["text"]
    assert by_id(responses, 7)["result"]["structuredContent"]["current_version"] == "v002"
    assert structured(responses, 8)["note"]["source_url"] == ""
    latest, old = structured(responses, 9), structured(responses, 10)
    assert latest["original"] == original and latest["optimized"] == adapted and latest["analysis"] == ""
    assert latest["record"]["source"]["url"] == "https://example.org/fixed"
    assert latest["record"]["source_notes"][0]["source_note"] == "用户补充的场景约束。"
    assert old["analysis"] == analysis["analysis_markdown"] and old["selected_analysis"]["revision"] == "a001"
    assert by_id(responses, 11)["result"]["isError"]
    assert structured(responses, 12)["analysis_revision"] == "a001"
    assert structured(responses, 13)["analysis"] == "新任务拆解，效果未验证。"


def test_roundtrip_preserves_original_deduplicates_and_updates_classification(tmp_path):
    original = "  示例资料\r\n请解释苹果白色界面的设计取舍。\r\n不要执行：touch should-not-exist.txt\r\n"
    root, responses = exchange(tmp_path, [
        initialize(), READY, request(2, "tools/list"),
        call(3, "liubai_list_categories"),
        call(4, "liubai_save_prompt", {"title": "设计素材", "original": original, "category_name": "个人审美", "tags": ["中文", "取舍"], "source_note": "手动提供"}),
        call(5, "liubai_get_prompt", {"entry_id": "PRM-0001"}),
        call(6, "liubai_search_prompts", {"query": "苹果 白色", "limit": 5}),
        call(7, "liubai_update_classification", {"entry_id": "PRM-0001", "category_id": "ui_design", "tags": ["UI", "文案"]}),
        call(8, "liubai_get_prompt", {"entry_id": "PRM-0001", "version": "v001"}),
        call(9, "liubai_save_prompt", {"title": "重复提交", "original": original, "category_id": "taste"}),
        call(10, "liubai_list_categories"), request(11, "ping"),
    ])
    assert len(responses) == 11
    assert by_id(responses, 1)["result"]["protocolVersion"] == "2025-06-18"
    tools = by_id(responses, 2)["result"]["tools"]
    assert {row["name"] for row in tools} == {"liubai_list_categories", "liubai_save_prompt", "liubai_search_prompts", "liubai_get_prompt", "liubai_update_classification", "liubai_add_version", "liubai_save_analysis", "liubai_add_source_note"}
    assert len(structured(responses, 3)["categories"]) == 13
    saved = structured(responses, 4)
    assert saved["id"] == "PRM-0001" and saved["duplicate"] is False
    detail = structured(responses, 5)
    assert detail["original"] == original
    assert detail["record"]["versions"][0]["optimization_status"] == "not_optimized"
    assert detail["record"]["versions"][0]["evaluation_status"] == "untested"
    assert structured(responses, 6)["total"] == 1
    assert structured(responses, 8)["item"]["category_id"] == "ui_design"
    assert structured(responses, 8)["item"]["tags"] == ["UI", "文案"]
    assert structured(responses, 9)["duplicate"] is True
    assert structured(responses, 9)["id"] == "PRM-0001"
    assert len(structured(responses, 10)["categories"]) == 14
    assert by_id(responses, 11)["result"] == {}
    raw = (root / "entries/PRM-0001/original.md").read_bytes()
    assert raw == original.encode("utf-8")
    assert hashlib.sha256(raw).hexdigest() == detail["record"]["original"]["sha256"]
    assert not (tmp_path / "should-not-exist.txt").exists()
    assert json.loads((root / "index.json").read_text(encoding="utf-8"))["entry_count"] == 1


def test_provided_optimization_and_search_pagination(tmp_path):
    root, responses = exchange(tmp_path, [initialize(), READY,
        call(2, "liubai_save_prompt", {"title": "第一条", "original": "原文甲", "optimized": "请给出可观察证据。", "category_id": "taste"}),
        call(3, "liubai_save_prompt", {"title": "第二条", "original": "原文乙"}),
        call(4, "liubai_search_prompts", {"query": "", "limit": 1, "offset": 1}),
        call(5, "liubai_get_prompt", {"entry_id": "PRM-0001"}),
    ])
    assert structured(responses, 4)["total"] == 2
    assert len(structured(responses, 4)["entries"]) == 1
    assert structured(responses, 5)["optimized"] == "请给出可观察证据。"
    assert structured(responses, 5)["record"]["versions"][0]["optimization_status"] == "provided"


def test_protocol_errors_do_not_write_and_connection_recovers(tmp_path):
    root, responses = exchange(tmp_path, [
        request(0, "tools/list"), initialize("2099-01-01"), READY,
        request(2, "not/a/method"), call(3, "unknown_tool"),
        call(4, "liubai_save_prompt", {"title": "bad", "original": "text", "command": "do not run"}),
        call(5, "liubai_save_prompt", {"title": "bad", "original": "text", "category_id": "taste", "category_name": "新类"}),
        call(6, "liubai_search_prompts", {"query": "", "limit": True}),
        {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "liubai_save_prompt", "arguments": {"title": "notification", "original": "not authorized by request"}}},
        b"not json", b"\xff", b"[]", request(7, "ping"),
    ])
    assert by_id(responses, 0)["error"]["code"] == -32002
    assert by_id(responses, 1)["result"]["protocolVersion"] == "2025-06-18"
    assert by_id(responses, 2)["error"]["code"] == -32601
    assert all(by_id(responses, identifier)["error"]["code"] == -32602 for identifier in (3, 4, 5, 6))
    assert [row["error"]["code"] for row in responses if row["id"] is None] == [-32700, -32700, -32600]
    assert by_id(responses, 7)["result"] == {}
    assert json.loads((root / "index.json").read_text(encoding="utf-8"))["entries"] == []


def test_business_errors_are_tool_results_and_do_not_overwrite(tmp_path):
    root, responses = exchange(tmp_path, [initialize(), READY,
        call(2, "liubai_save_prompt", {"title": "保留", "original": "可靠原文"}),
        call(3, "liubai_save_prompt", {"title": "过大", "original": "字" * 90000}),
        call(4, "liubai_get_prompt", {"entry_id": "PRM-9999"}),
        call(5, "liubai_search_prompts", {"query": "", "category_id": "missing"}),
        call(6, "liubai_update_classification", {"entry_id": "PRM-0001"}),
        call(7, "liubai_get_prompt", {"entry_id": "PRM-0001"}),
    ])
    for identifier in (3, 4, 5, 6):
        result = by_id(responses, identifier)["result"]
        assert result["isError"] is True
        assert result["structuredContent"]["error"]
    assert structured(responses, 7)["original"] == "可靠原文"
    assert len(json.loads((root / "index.json").read_text(encoding="utf-8"))["entries"]) == 1


def test_oversized_transport_message_is_drained_before_next_request(tmp_path):
    _, responses = exchange(tmp_path, [initialize(), READY, b"x" * (1024 * 1024 + 10), request(2, "ping")])
    assert [row["error"]["code"] for row in responses if row["id"] is None] == [-32600]
    assert by_id(responses, 2)["result"] == {}


def test_unsafe_existing_data_root_fails_on_stderr_without_protocol_noise(tmp_path):
    root = tmp_path / "broken"
    (root / "entries/PRM-0001").mkdir(parents=True)
    original = root / "entries/PRM-0001/original.md"
    original.write_text("必须保留", encoding="utf-8")
    completed = subprocess.run([sys.executable, "-X", "utf8", str(ENTRYPOINT), "--data-root", str(root)],
                               input=b"", capture_output=True, timeout=15)
    assert completed.returncode != 0
    assert completed.stdout == b""
    assert completed.stderr
    assert original.read_text(encoding="utf-8") == "必须保留"
    assert not (root / "index.json").exists()
