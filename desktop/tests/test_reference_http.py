"""通过真实本机 HTTP 服务验证参考库；全部资料位于临时目录，外部客户端使用假响应。"""

from hashlib import sha256
from pathlib import Path
import json
import sys
import threading

import pytest

DESKTOP = Path(__file__).parents[1]
if str(DESKTOP) not in sys.path:
    sys.path.insert(0, str(DESKTOP))
from test_server import library, request, server
from test_references import analysis, source, save_json
from test_reference_runner import FakeClient


@pytest.fixture
def reference_http(library):
    ids = ["development", "ui_design", "llm_design", "langchain_design", "taste", "product", "business", "writing", "visual", "learning", "productivity", "general", "uncategorized"]
    save_json(library.root / "taxonomy.json", {"categories": [{"id": value, "name": value} for value in ids]})
    personal_path = library.root / "entries/PRM-0001/record.json"
    personal = json.loads(personal_path.read_text(encoding="utf-8"))
    personal["versions"] = [{"version": "v001", "file": "optimized-v001.md", "evaluation_status": "untested"}]
    save_json(personal_path, personal)
    index = json.loads((library.root / "index.json").read_text(encoding="utf-8"))
    index["entries"][0].update(latest_version="v001", original_sha256=sha256((personal_path.parent / "original.md").read_bytes()).hexdigest())
    index["entry_count"] = 1
    save_json(library.root / "index.json", index)
    (library.root / "README.md").write_text("已收录实际提示词 1 条。\n当前已有 1 条素材。\n", encoding="utf-8")
    instance = server.LocalServer(("127.0.0.1", 0), library)
    client = FakeClient()
    instance.references.runner.client_factory = lambda budget: client
    raw_by_id = {}
    source_by_id = {}
    for i in range(12):
        raw = (f"原文 {i + 1:02d}\r\n```text\r\nKeep labels.\r\n```\r\n<svg onload=alert(1)>\r\n").encode("utf-8")
        if i == 0:
            raw = b"\xef\xbb\xbf" + raw
        provenance = source(path=f"prompts/{i + 1:02d}.md")
        provenance["tracking_full_sha256"] = sha256(raw).hexdigest()
        category = ["taste", "ui_design", "visual"][i // 4]
        item = instance.references.store.ingest(provenance, raw, {"title": f"测试参考 {i + 1:02d}", "category_id": category, "tags": ["文案", "对照"], "material_type": "prompt", "selection_status": "selected", "related_ids": ["PRM-0001"] if i == 0 else []})
        card = analysis(f"请按参考 {i + 1:02d} 处理 {{{{任务}}}}。")
        card["use_cases"] = f"第 {i + 1} 份参考适用场景。"
        instance.references.store.set_analysis(item["id"], item["snapshot_id"], card)
        raw_by_id[item["id"]] = raw
        source_by_id[item["id"]] = provenance
        client.contents[provenance["path"]] = ({**provenance, "license_status": "unknown"}, raw)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{instance.server_port}"
    yield {"server": instance, "library": library, "url": endpoint, "raw": raw_by_id, "sources": source_by_id, "client": client}
    instance.shutdown()
    instance.server_close()
    thread.join(timeout=3)


def get(ctx, route):
    status, body, headers = request(ctx["url"] + route)
    return status, json.loads(body), headers


def post(ctx, route, payload, headers=None):
    valid = {"Origin": ctx["url"], "Content-Type": "application/json", "X-Prompt-Library": "1"}
    status, body, response_headers = request(ctx["url"] + route, payload, valid if headers is None else headers)
    return status, json.loads(body), response_headers


def adopt(ctx, ref_id="REF-0001", target_id=None):
    status, preview, _ = post(ctx, "/api/references/adopt-preview", {"id": ref_id, "target_id": target_id})
    assert status == 200 and preview["can_adopt"]
    return post(ctx, "/api/references/adopt", {"id": ref_id, "target_id": preview["target_id"], "expected_snapshot": preview["snapshot_id"], "expected_analysis_version": preview["analysis_version"]})


def test_twelve_reference_catalogue_contract_does_not_inflate_personal_count(reference_http):
    ctx = reference_http
    status, catalogue, _ = get(ctx, "/api/references")
    assert status == 200
    assert len(catalogue["references"]) == 12 and len(catalogue["categories"]) == 13
    assert {category: sum(row["category_id"] == category for row in catalogue["references"]) for category in ("taste", "ui_design", "visual")} == {"taste": 4, "ui_design": 4, "visual": 4}
    assert all(row["analysis_status"] == "ready" and row["evaluation_status"] == "untested" for row in catalogue["references"])
    assert all(row["source"]["commit"] in row["source"]["url"] for row in catalogue["references"])
    assert catalogue["schedule"]["timezone"] == "Asia/Shanghai"
    assert get(ctx, "/api/library")[1]["entry_count"] == 1


def test_original_download_is_byte_exact_and_card_places_original_before_analysis(reference_http):
    ctx = reference_http
    status, body, headers = request(ctx["url"] + "/download/reference/REF-0001/original")
    assert status == 200 and body == ctx["raw"]["REF-0001"]
    assert "attachment" in headers["Content-Disposition"] and headers["X-Content-Type-Options"] == "nosniff"
    status, body, _ = request(ctx["url"] + "/download/reference/REF-0001/card")
    text = body.decode("utf-8")
    assert status == 200
    assert text.index("## 提示词原文") < text.index("原文 01\r\n") < text.index("## 适用场景") < text.index("## 通用模板")
    assert "````text\n" in text
    assert ctx["raw"]["REF-0001"].decode("utf-8-sig") in text
    assert "状态：illustrative" in text
    status, template, _ = request(ctx["url"] + "/download/reference/REF-0001/template")
    assert status == 200 and template.decode("utf-8") == "请按参考 01 处理 {{任务}}。"


def test_snapshot_query_returns_prior_raw_and_analysis_after_update(reference_http):
    ctx = reference_http
    store = ctx["server"].references.store
    changed = {**ctx["sources"]["REF-0001"], "commit": "b" * 40}
    changed["url"] = changed["url"].replace("a" * 40, "b" * 40)
    store.ingest(changed, b"Changed prompt\n")
    status, current, _ = get(ctx, "/api/references/REF-0001")
    assert status == 200 and current["snapshot"]["id"] == "s002" and current["analysis"] is None
    status, previous, _ = get(ctx, "/api/references/REF-0001?snapshot=s001")
    assert status == 200 and previous["analysis"]["version"] == "a001"
    assert previous["original"] == ctx["raw"]["REF-0001"].decode("utf-8-sig")
    assert request(ctx["url"] + "/download/reference/REF-0001/original?snapshot=s001")[1] == ctx["raw"]["REF-0001"]
    assert get(ctx, "/api/references/REF-0001?snapshot=s999")[0] == 404


@pytest.mark.parametrize("change", ["analysis", "snapshot"])
def test_stale_adoption_preview_is_rejected_over_http(reference_http, change):
    ctx = reference_http
    _, preview, _ = post(ctx, "/api/references/adopt-preview", {"id": "REF-0001"})
    store = ctx["server"].references.store
    if change == "analysis":
        store.set_analysis("REF-0001", "s001", analysis("更正后的模板"))
    else:
        changed = {**ctx["sources"]["REF-0001"], "commit": "b" * 40}
        changed["url"] = changed["url"].replace("a" * 40, "b" * 40)
        store.ingest(changed, b"changed")
    status, failure, _ = post(ctx, "/api/references/adopt", {"id": "REF-0001", "expected_snapshot": preview["snapshot_id"], "expected_analysis_version": preview["analysis_version"]})
    assert status == 400 and "更新" in failure["error"]
    assert get(ctx, "/api/library")[1]["entry_count"] == 1


def test_confirmed_adoption_creates_personal_entry_and_is_idempotent(reference_http):
    ctx = reference_http
    status, saved, _ = adopt(ctx)
    assert status == 200 and saved["entry_id"] == "PRM-0002" and saved["version"] == "v001"
    status, personal, _ = get(ctx, "/api/entries/PRM-0002")
    assert status == 200 and personal["optimized"] == "请按参考 01 处理 {{任务}}。"
    assert personal["record"]["versions"][0]["reference_provenance"]["reference_id"] == "REF-0001"
    assert get(ctx, "/api/library")[1]["entry_count"] == 2
    assert request(ctx["url"] + "/download/PRM-0002/original")[1] == ctx["raw"]["REF-0001"]
    assert adopt(ctx)[1]["duplicate"] is True
    assert get(ctx, "/api/library")[1]["entry_count"] == 2


def test_personal_version_history_download_and_analysis_stay_bound_to_selected_version(reference_http):
    ctx = reference_http
    assert adopt(ctx)[0] == 200
    old_optimized = request(ctx["url"] + "/download/PRM-0002/optimized?version=v001")[1]
    changed_analysis = analysis("第二版个人模板")
    changed_analysis["use_cases"] = "第二版独有适用场景。"
    ctx["server"].references.store.set_analysis("REF-0001", "s001", changed_analysis)
    assert adopt(ctx, target_id="PRM-0002")[1]["version"] == "v002"
    assert request(ctx["url"] + "/download/PRM-0002/optimized?version=v001")[1] == old_optimized
    assert request(ctx["url"] + "/download/PRM-0002/optimized?version=v002")[1].decode("utf-8") == "第二版个人模板"
    _, old, _ = get(ctx, "/api/entries/PRM-0002?version=v001")
    _, latest, _ = get(ctx, "/api/entries/PRM-0002?version=v002")
    assert old["selected_version"] == "v001" and len(latest["record"]["versions"]) == 2
    assert "第 1 份参考适用场景。" in old["analysis"]
    assert "第二版独有适用场景。" not in old["analysis"]
    assert "第二版独有适用场景。" in latest["analysis"]
    assert request(ctx["url"] + "/download/PRM-0002/original")[1] == ctx["raw"]["REF-0001"]


def test_flags_schedule_and_related_routes_roundtrip(reference_http):
    ctx = reference_http
    status, result, _ = post(ctx, "/api/references/flags", {"id": "REF-0001", "favorite": True, "followed": True})
    assert status == 200 and result["item"]["favorite"] and result["item"]["followed"]
    assert get(ctx, "/api/references/REF-0001")[1]["item"]["followed"]
    status, schedule, _ = post(ctx, "/api/references/schedule", {"enabled": False, "frequency": "weekly", "weekday": 6})
    assert status == 200 and schedule["enabled"] is False and schedule["frequency"] == "weekly" and schedule["next_run"] is None
    status, view, _ = get(ctx, "/api/references/status")
    assert status == 200 and view["enabled"] is False and view["timezone"] == "Asia/Shanghai"
    status, related, _ = get(ctx, "/api/references/related/PRM-0001")
    assert status == 200 and 1 <= len(related["references"]) <= 3
    assert related["references"][0]["id"] == "REF-0001"
    assert "reason" in related["references"][0]


@pytest.mark.parametrize("headers", [
    {"Origin": "https://outside.invalid", "Content-Type": "application/json", "X-Prompt-Library": "1"},
    {"Content-Type": "application/json", "X-Prompt-Library": "1"},
    {"Origin": "http://localhost:1", "Content-Type": "application/json"},
])
def test_reference_writes_reject_missing_or_foreign_origin(reference_http, headers):
    ctx = reference_http
    status, failure, _ = post(ctx, "/api/references/flags", {"id": "REF-0001", "followed": True}, headers)
    assert status == 403 and "error" in failure
    assert get(ctx, "/api/references/REF-0001")[1]["item"]["followed"] is False


def test_reference_writes_require_custom_header_even_with_valid_origin(reference_http):
    ctx = reference_http
    status, _, _ = post(ctx, "/api/references/schedule", {"enabled": False}, {"Origin": ctx["url"], "Content-Type": "application/json"})
    assert status == 403
    assert get(ctx, "/api/references/status")[1]["enabled"] is True


def test_unknown_license_blocks_original_download_and_adoption(reference_http):
    ctx = reference_http
    store = ctx["server"].references.store
    item = store.ingest(source(path="unknown.md", license_status="unknown"), b"unknown-licensed original")
    store.set_analysis(item["id"], item["snapshot_id"], analysis())
    status, detail, _ = get(ctx, "/api/references/" + item["id"])
    assert status == 200 and detail["original"] is None
    status, failure, _ = get(ctx, "/download/reference/" + item["id"] + "/original")
    assert status == 400 and "许可" in failure["error"]
    _, preview, _ = post(ctx, "/api/references/adopt-preview", {"id": item["id"]})
    assert preview["can_adopt"] is False
    status, _, _ = post(ctx, "/api/references/adopt", {"id": item["id"], "expected_snapshot": preview["snapshot_id"], "expected_analysis_version": preview["analysis_version"]})
    assert status == 400
