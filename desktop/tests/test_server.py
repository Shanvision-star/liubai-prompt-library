"""覆盖文件库读取、收藏留存、原文字节导出和本机请求边界。"""

from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import importlib.util
import json
import threading
import urllib.error
import urllib.request

import pytest

spec = importlib.util.spec_from_file_location("prompt_library_server", Path(__file__).parents[1] / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "library"
    folder = root / "entries" / "PRM-0001"
    folder.mkdir(parents=True)
    original = "原文不改\r\n<svg onload=alert(1)>\r\n".encode("utf-8")
    (folder / "original.md").write_bytes(original)
    (folder / "optimized-v001.md").write_text("# 标题\n```text\n请分析 {{主题}}\n```\n", encoding="utf-8")
    record = {"id": "PRM-0001", "original": {"file": "original.md"}, "source": {"type": "user_submission"}, "loop_review": {"reminder": "最多两轮"}}
    (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")
    item = {"id": "PRM-0001", "title": "示例", "summary": "说明", "category_id": "taste", "tags": [], "record_file": "entries/PRM-0001/record.json", "original_file": "entries/PRM-0001/original.md", "optimized_file": "entries/PRM-0001/optimized-v001.md"}
    (root / "index.json").write_text(json.dumps({"entries": [item]}), encoding="utf-8")
    (root / "taxonomy.json").write_text(json.dumps({"categories": [{"id": "taste", "name": "审美"}]}), encoding="utf-8")
    return server.Library(root, tmp_path / "state")


@pytest.fixture
def endpoint(library):
    instance = server.LocalServer(("127.0.0.1", 0), library)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{instance.server_port}"
    instance.shutdown()
    instance.server_close()
    thread.join(timeout=2)


def request(url, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        response = urllib.request.urlopen(req)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.read(), response.headers


def test_catalogue_reads_real_entries_and_full_text(library):
    catalogue = library.catalogue()
    assert catalogue["entry_count"] == 1
    assert "原文不改" in catalogue["entries"][0]["search_text"]
    assert library.entry("PRM-0001")["optimized"] == "请分析 {{主题}}"


def test_favorite_persists_without_changing_sources(library):
    before = {p: sha256(p.read_bytes()).digest() for p in library.root.rglob("*") if p.is_file()}
    library.set_favorite("PRM-0001", True)
    reopened = server.Library(library.root, library.state_dir)
    assert reopened.favorites() == ["PRM-0001"]
    assert before == {p: sha256(p.read_bytes()).digest() for p in before}
    assert reopened.set_favorite("PRM-0001", False) == []


def test_invalid_state_does_not_overwrite_favorites(library):
    library.set_favorite("PRM-0001", True)
    with pytest.raises(ValueError):
        library.set_favorite("PRM-0001", "false")
    assert library.favorites() == ["PRM-0001"]


def test_metadata_cannot_escape_library(library):
    with pytest.raises(ValueError):
        library.contained_path("../outside.txt")


def test_original_download_preserves_bytes(endpoint, library):
    status, body, headers = request(endpoint + "/download/PRM-0001/original")
    assert status == 200
    assert body == (library.root / "entries/PRM-0001/original.md").read_bytes()
    assert "attachment" in headers["Content-Disposition"]


@pytest.mark.parametrize("path", ["/api/entries/PRM-9999", "/api/entries/../../index.json", "/desktop/.runtime/favorites.json", "/index.json"])
def test_unknown_and_private_paths_not_served(endpoint, path):
    assert request(endpoint + path)[0] == 404


def test_cross_site_mutation_is_rejected(endpoint, library):
    status, _, _ = request(endpoint + "/api/favorites", {"id": "PRM-0001", "favorite": True}, {"Origin": "https://example.org", "Content-Type": "application/json", "X-Prompt-Library": "1"})
    assert status == 403
    assert library.favorites() == []


def test_valid_mutation_roundtrip(endpoint):
    status, body, _ = request(endpoint + "/api/favorites", {"id": "PRM-0001", "favorite": True}, {"Origin": endpoint, "Content-Type": "application/json", "X-Prompt-Library": "1"})
    assert status == 200
    assert json.loads(body)["favorites"] == ["PRM-0001"]
    assert json.loads(request(endpoint + "/api/library")[1])["favorites"] == ["PRM-0001"]


def test_external_host_is_rejected(endpoint):
    assert request(endpoint + "/api/library", headers={"Host": "outside.invalid"})[0] == 403


def test_empty_library_is_valid(library):
    (library.root / "index.json").write_text('{"entries":[]}', encoding="utf-8")
    assert library.catalogue()["entry_count"] == 0


def test_html_is_protected_by_content_security_policy(endpoint):
    status, body, headers = request(endpoint + "/")
    assert status == 200
    assert b"<script src=\"/app.js\" defer>" in body
    assert "script-src 'self'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"
