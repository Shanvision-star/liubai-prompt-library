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
