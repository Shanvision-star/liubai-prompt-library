"""通过真实本机HTTP验证手动分类、保存和令牌接口；所有数据均在临时库中。"""

from hashlib import sha256
import json
import threading

import pytest

from server import Library, LocalServer
from test_server import request


@pytest.fixture
def api(tmp_path):
    library = Library(tmp_path / "empty-library")
    server = LocalServer(("127.0.0.1", 0), library)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield {"root": library.root, "url": f"http://127.0.0.1:{server.server_port}", "token": server.api_token}
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


def post(api, path, body, native=False, extra=None):
    headers = {"Content-Type": "application/json"}
    headers.update({"Authorization": "Bearer " + api["token"]} if native else {"Origin": api["url"], "X-Prompt-Library": "1"})
    headers.update(extra or {})
    status, data, _ = request(api["url"] + path, body, headers)
    return status, json.loads(data)


def get(api, path):
    status, data, _ = request(api["url"] + path)
    return status, json.loads(data)


def test_help_and_lifecycle_assets_are_served(api):
    for name in ("guide.js", "guide.css", "lifecycle.js"):
        status, body, _ = request(api["url"] + "/" + name)
        assert status == 200 and body


def test_empty_install_can_create_category_and_save_exact_text(api):
    assert get(api, "/api/library")[1]["entry_count"] == 0
    assert len(get(api, "/api/categories")[1]["categories"]) == 13
    status, category = post(api, "/api/categories", {"name": "个人实验", "description": "自定义分类"})
    assert status == 200 and category["created"]
    original = "  原文不删空格\r\n```text\n示例中的代码围栏\n```\n保留结尾\n"
    status, saved = post(api, "/api/prompts", {"title": "合成示例", "original": original, "category_id": category["category"]["id"], "tags": ["测试"]})
    assert status == 200 and saved["id"] == "PRM-0001"
    entry = get(api, "/api/entries/PRM-0001")[1]
    assert entry["optimized"] == original
    assert entry["record"]["versions"][0]["optimization_status"] == "not_optimized"
    assert request(api["url"] + "/download/PRM-0001/original")[1] == original.encode("utf-8")
    status, duplicate = post(api, "/api/prompts", {"title": "重复提交不得覆盖", "original": original, "category_name": "不该新建"})
    assert status == 200 and duplicate["duplicate"] and duplicate["id"] == saved["id"]
    assert len(get(api, "/api/categories")[1]["categories"]) == 14
    assert get(api, "/api/library")[1]["entry_count"] == 1


def test_reclassify_changes_metadata_not_original_or_versions(api):
    _, saved = post(api, "/api/prompts", {"title": "合成示例", "original": "原文", "optimized": "优化建议", "category_name": "自建甲"})
    folder = api["root"] / "entries" / saved["id"]
    before = {p.name: sha256(p.read_bytes()).hexdigest() for p in folder.glob("*.md")}
    status, updated = post(api, f"/api/entries/{saved['id']}/metadata", {"category_name": "自建乙", "tags": ["新标签"]})
    assert status == 200
    entry = get(api, f"/api/entries/{saved['id']}")[1]
    assert entry["item"]["category_id"] == updated["item"]["category_id"]
    assert len(entry["record"]["versions"]) == 1 and entry["record"]["versions"][0]["optimization_status"] == "provided"
    assert {p.name: sha256(p.read_bytes()).hexdigest() for p in folder.glob("*.md")} == before
    assert post(api, f"/api/entries/{saved['id']}/metadata", {"original": "试图覆盖"})[0] == 400


def test_native_token_only_grants_new_save_and_classification_routes(api):
    status, result = post(api, "/api/prompts", {"title": "API示例", "original": "由本机接口保存", "category_id": "general"}, native=True)
    assert status == 200 and result["id"]
    assert post(api, "/api/categories", {"name": "API分类"}, native=True)[0] == 200
    assert post(api, "/api/references/check", {}, native=True)[0] == 403
    assert post(api, "/api/prompts", {"title": "x", "original": "x"}, native=True, extra={"Authorization": "Bearer invalid"})[0] == 403
    assert post(api, "/api/prompts", {"title": "x", "original": "x"}, native=True, extra={"Origin": "https://example.org"})[0] == 403


def test_integration_discovery_never_returns_secret_or_serves_token(api):
    status, integration = get(api, "/api/integrations")
    assert status == 200 and integration["local_only"] is True
    assert api["token"] not in json.dumps(integration)
    assert request(api["url"] + "/desktop/.runtime/api-token")[0] == 404
    assert request(api["url"] + "/api/prompts", {"title": "x", "original": "x"}, {"Content-Type": "application/json"})[0] == 403


def test_failed_or_oversized_prompt_does_not_create_entry_or_category(api):
    assert post(api, "/api/prompts", {"title": "x", "original": "x" * (256 * 1024 + 1), "category_name": "不可残留"})[0] == 400
    assert get(api, "/api/library")[1]["entry_count"] == 0
    assert len(get(api, "/api/categories")[1]["categories"]) == 13
    assert post(api, "/api/categories", {"name": "", "description": "x"})[0] == 400


@pytest.mark.parametrize("native", [False, True])
def test_version_analysis_and_source_roundtrip_with_each_allowed_client(api, native):
    original, first, second = "  原文\r\n", "初版建议\n", "适配新任务\r\n"
    _, saved = post(api, "/api/prompts", {"title": "多版本素材", "original": original, "optimized": first}, native=native)
    base = f"/api/entries/{saved['id']}"
    detail = get(api, base)[1]
    analysis = {"version": "v001", "original_sha256": detail["original_sha256"], "optimized_sha256": detail["optimized_sha256"], "analysis_markdown": "# 初版拆解\n原文与改编分开。"}
    status, stored = post(api, base + "/analysis", analysis, native=native)
    assert status == 200 and stored["analysis_revision"] == "a001"
    assert post(api, base + "/analysis", analysis, native=native)[1]["duplicate"]
    version = {"optimized": second, "reason": "适配新任务", "expected_version": "v001"}
    assert post(api, base + "/versions", version, native=native)[1]["version"] == "v002"
    assert post(api, base + "/versions", version, native=native)[1]["duplicate"]
    status, conflict = post(api, base + "/versions", {**version, "optimized": "过期的另一份编辑"}, native=native)
    assert status == 409 and conflict["current_version"] == "v002"
    assert post(api, base + "/source-notes", {"source_url": "https://example.org/context", "source_note": "补充上下文，尚未核实。"}, native=native)[0] == 200
    latest, old = get(api, base)[1], get(api, base + "?version=v001")[1]
    assert latest["original"] == original and latest["optimized"] == second and latest["analysis"] == ""
    assert old["optimized"] == first and old["analysis"] == analysis["analysis_markdown"]
    assert old["analysis_status"] == "ready" and old["analysis_origin"] == "external_client"
    assert latest["record"]["source_notes"][0]["source_note"] == "补充上下文，尚未核实。"
    assert latest["record"]["evaluation_status"] == "untested"
    assert post(api, base + "/analysis", {**analysis, "version": "v002"}, native=native)[0] == 400


@pytest.mark.parametrize("operation,body", [
    ("versions", {"optimized": "新版", "reason": "测试权限", "expected_version": "v001"}),
    ("analysis", {"version": "v001", "original_sha256": "0" * 64, "optimized_sha256": "0" * 64, "analysis_markdown": "说明"}),
    ("source-notes", {"source_note": "补充"}),
])
def test_new_routes_reject_missing_invalid_or_cross_origin_authorization(api, operation, body):
    _, saved = post(api, "/api/prompts", {"title": "权限测试", "original": "原文"})
    path = f"/api/entries/{saved['id']}/{operation}"
    before = (api["root"] / "entries" / saved["id"] / "record.json").read_bytes()
    assert request(api["url"] + path, body, {"Content-Type": "application/json"})[0] == 403
    assert post(api, path, body, native=True, extra={"Authorization": "Bearer invalid"})[0] == 403
    assert post(api, path, body, native=True, extra={"Origin": "https://example.org"})[0] == 403
    assert post(api, path, body, extra={"X-Prompt-Library": ""})[0] == 403
    assert (api["root"] / "entries" / saved["id"] / "record.json").read_bytes() == before
