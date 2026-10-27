"""验证公开素材初始化、历史保护、清单完整性与安装版请求边界。"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import threading

import pytest
from bundled_library import install_collection
from library_export import app_info
from server import Library, LocalServer
from prompt_store import PromptStore
from reference_store import ReferenceStore
from test_server import request


COLLECTION = Path(__file__).resolve().parents[2] / "bundled-library"


def test_public_collection_is_readable_and_keeps_user_changes(tmp_path):
    assert install_collection(tmp_path)
    library = Library(tmp_path)
    assert library.catalogue()["entry_count"] == 222
    assert len(ReferenceStore(tmp_path).catalogue()["references"]) == 13
    entry = library.entry("PRM-0205")
    assert entry["selected_version"] == "v002" and entry["analysis"]
    assert "非网站提示词原文" in entry["original"]
    assert "原语言短引" not in entry["original"]
    saved = PromptStore(tmp_path).save_prompt({"title": "安装后的个人内容", "original": "不随升级覆盖"})
    before = (tmp_path / "index.json").read_bytes()
    assert not install_collection(tmp_path)
    assert (tmp_path / "index.json").read_bytes() == before
    assert Library(tmp_path).entry(saved["id"])["original"] == "不随升级覆盖"


def test_incomplete_library_is_never_seeded(tmp_path):
    (tmp_path / "entries/PRM-9000").mkdir(parents=True)
    original = tmp_path / "entries/PRM-9000/original.md"
    original.write_text("已有资料", encoding="utf-8")
    with pytest.raises(ValueError, match="索引不完整"):
        install_collection(tmp_path)
    assert not (tmp_path / "index.json").exists()
    assert original.read_text(encoding="utf-8") == "已有资料"


@pytest.mark.parametrize("name", ["../escape.txt", "desktop/.runtime/api-token", "references/.operations/schedule.json"])
def test_collection_paths_cannot_install_runtime_or_escape(tmp_path, name):
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "manifest.json").write_text(json.dumps({"files": [{"path": name, "sha256": "0" * 64}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="不允许的路径"):
        install_collection(tmp_path / "target", seed)
    assert not (tmp_path / "target/index.json").exists()


def test_corrupted_collection_does_not_create_partial_index(tmp_path):
    seed = tmp_path / "seed"
    seed.mkdir()
    (seed / "index.json").write_text("{}", encoding="utf-8")
    (seed / "manifest.json").write_text(json.dumps({"files": [{"path": "index.json", "sha256": "0" * 64}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="校验失败"):
        install_collection(tmp_path / "target", seed)
    assert not (tmp_path / "target/index.json").exists()


def test_public_collection_hashes_and_metadata_are_consistent():
    manifest = json.loads((COLLECTION / "manifest.json").read_text(encoding="utf-8"))
    for row in manifest["files"]:
        assert sha256((COLLECTION / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    index = json.loads((COLLECTION / "index.json").read_text(encoding="utf-8"))
    for entry in index["entries"]:
        record = json.loads((COLLECTION / entry["record_file"]).read_text(encoding="utf-8"))
        assert entry["original_sha256"] == record["original"]["sha256"] == sha256((COLLECTION / entry["original_file"]).read_bytes()).hexdigest()
    for path in COLLECTION.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        json.loads(text)
        assert '"thread_id"' not in text and 'C:\\\\Users\\\\Rome' not in text


def test_frozen_mcp_config_uses_executable_not_python_flags(tmp_path, monkeypatch):
    import tomllib
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "Liubai.exe"))
    config = tomllib.loads(app_info(Library(tmp_path / "data"))["mcp_config"])["mcp_servers"]["liubai"]
    assert config["command"].endswith("Liubai-MCP.exe")
    assert config["args"] == ["--data-root", str(tmp_path / "data")]


def test_quit_requires_authorization_and_stops_server(tmp_path):
    instance = LocalServer(("127.0.0.1", 0), Library(tmp_path))
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{instance.server_port}/api/application/quit"
    try:
        assert request(url, {}, {"Content-Type": "application/json"})[0] == 403
        assert thread.is_alive()
        assert request(url, {}, {"Content-Type": "application/json", "Authorization": "Bearer " + instance.api_token})[0] == 200
        thread.join(timeout=3)
        assert not thread.is_alive()
    finally:
        instance.shutdown()
        instance.server_close()
