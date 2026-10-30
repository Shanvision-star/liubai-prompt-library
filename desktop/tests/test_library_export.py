"""验证备份可恢复、原文字节不变，以及授权和机器状态不进入备份。"""

from hashlib import sha256
from io import BytesIO
import json
import subprocess
import sys
import tomllib
import zipfile

import pytest

import library_export
from library_export import app_info, export_library
from prompt_store import PromptStore
from reference_store import ReferenceStore
from server import Library
from test_prompt_http import api
from test_server import request
from test_references import source, analysis


def test_backup_roundtrip_keeps_bytes_versions_references_and_favorites(tmp_path):
    library = Library(tmp_path / "original library", tmp_path / "custom-state")
    raw = "  保留空白\r\n<script>不可执行</script>\n"
    saved = PromptStore(library.root).save_prompt({"title": "合成素材", "original": raw, "optimized": "建议版", "category_name": "我的分类"})
    library.set_favorite(saved["id"], True)
    store = ReferenceStore(library.root)
    ref = store.ingest(source(), b"Keep labels.\r\n", {"title": "参考", "category_id": "ui_design"})
    store.set_analysis(ref["id"], ref["snapshot_id"], analysis())
    store.ingest(source(commit="b" * 40), b"Keep labels and names.\r\n")
    (library.state_dir / "api-token").write_text("secret-never-include", encoding="utf-8")
    operations = library.root / "references/.operations"
    operations.mkdir()
    (operations / "schedule.json").write_text('{"enabled":true,"automation_id":"private"}', encoding="utf-8")
    (library.root / "README.md").write_text("not-a-backup-file", encoding="utf-8")
    private_lesson = library.root / "private-learning-library" / "lesson.md"
    private_lesson.parent.mkdir()
    private_lesson.write_text("本机保留的教学资料", encoding="utf-8")
    license_asset = library.root / "references/assets/license.txt"
    license_asset.parent.mkdir()
    license_asset.write_text("保留参考许可附件", encoding="utf-8")
    before = {p: sha256(p.read_bytes()).hexdigest() for p in library.root.rglob("*") if p.is_file()}
    payload = export_library(library)
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        names = archive.namelist()
        assert not any("api-token" in name or ".operations" in name or "README.md" in name for name in names)
        manifest = json.loads(archive.read("backup-manifest.json"))
        for row in manifest["files"]:
            assert sha256(archive.read(row["path"])).hexdigest() == row["sha256"]
        restored_root = tmp_path / "restored"
        archive.extractall(restored_root)
    restored = Library(restored_root)
    assert restored.entry(saved["id"])["original"] == raw
    assert restored.entry(saved["id"])["optimized"] == "建议版"
    assert restored.favorites() == [saved["id"]]
    assert (restored_root / "private-learning-library" / "lesson.md").read_text(encoding="utf-8") == "本机保留的教学资料"
    assert (restored_root / "references/assets/license.txt").read_text(encoding="utf-8") == "保留参考许可附件"
    assert len(ReferenceStore(restored_root).detail(ref["id"])["snapshots"]) == 2
    assert ReferenceStore(restored_root).detail(ref["id"], "s001")["analysis"]["template"] == analysis()["template"]
    assert {p: sha256(p.read_bytes()).hexdigest() for p in before} == before


def test_export_budget_fails_without_mutation(tmp_path, monkeypatch):
    library = Library(tmp_path / "library")
    before = (library.root / "index.json").read_bytes()
    monkeypatch.setattr(library_export, "MAX_BACKUP_BYTES", 10)
    with pytest.raises(ValueError, match="256 MiB"):
        export_library(library)
    assert (library.root / "index.json").read_bytes() == before


def test_backup_rejects_symlink_in_entry(tmp_path):
    library = Library(tmp_path / "library")
    saved = PromptStore(library.root).save_prompt({"title": "合成素材", "original": "内容"})
    outside = tmp_path / "outside.txt"
    outside.write_text("private", encoding="utf-8")
    try:
        (library.root / "entries" / saved["id"] / "link.md").symlink_to(outside)
    except OSError:
        pytest.skip("系统未授权创建符号链接")
    with pytest.raises(ValueError, match="库外|链接"):
        export_library(library)


def test_backup_directory_read_error_is_not_silently_skipped(tmp_path, monkeypatch):
    library = Library(tmp_path / "library")
    PromptStore(library.root).save_prompt({"title": "内容", "original": "应备份"})
    def fail_walk(folder, **options):
        options["onerror"](PermissionError("无法读取目录"))
        return iter(())
    monkeypatch.setattr(library_export.os, "walk", fail_walk)
    with pytest.raises(PermissionError, match="无法读取目录"):
        export_library(library)


def test_generated_mcp_config_points_to_running_library(tmp_path):
    library = Library(tmp_path / '中文 library')
    info = app_info(library)
    config = tomllib.loads(info["mcp_config"])["mcp_servers"]["liubai"]
    assert config["args"][-1] == str(library.root)
    assert config["command"] == sys.executable
    # 真正启动生成的命令并握手，避免配置只是语法看起来正确。
    messages = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}}]
    result = subprocess.run([config["command"], *config["args"]], input="\n".join(json.dumps(m) for m in messages) + "\n", capture_output=True, text=True, encoding="utf-8", timeout=15)
    assert result.returncode == 0
    assert json.loads(result.stdout)["result"]["serverInfo"]["name"] == "liubai-prompt-library"


def test_client_instructions_share_the_exact_running_library(tmp_path):
    library = Library(tmp_path / "用户的资料 ' draft")
    info = app_info(library)
    toml_server = tomllib.loads(info["mcp_config"])["mcp_servers"]["liubai"]
    json_server = json.loads(info["mcp_json_config"])["mcpServers"]["liubai"]
    assert json_server == {"command": toml_server["command"], "args": toml_server["args"]}
    assert info["mcp_connection"]["args"][-1] == str(library.root)
    assert info["client_commands"]["codex"].startswith("codex mcp add liubai -- ")
    assert info["client_commands"]["claude_code"].startswith("claude mcp add --transport stdio --scope user liubai -- ")
    assert info["mcp_connection"]["transport"] == "stdio"
    assert "api-token" not in json.dumps(info)


def test_backup_instructions_include_installed_executable(tmp_path):
    payload = export_library(Library(tmp_path / "library"))
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        instructions = archive.read("RESTORE.txt").decode("utf-8")
    assert 'Liubai.exe --data-root' in instructions
    assert 'python -X utf8 start.py' in instructions


def test_export_http_is_downloadable_and_rejects_cross_site(api):
    status, payload, headers = request(api["url"] + "/download/library-backup")
    assert status == 200 and headers["Content-Type"] == "application/zip"
    assert "attachment" in headers["Content-Disposition"]
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        assert json.loads(archive.read("index.json"))["entry_count"] == 0
        assert not any("api-token" in name for name in archive.namelist())
    assert request(api["url"] + "/download/library-backup", headers={"Sec-Fetch-Site": "cross-site"})[0] == 403
    status, body, _ = request(api["url"] + "/api/app-info")
    assert status == 200 and api["token"] not in body.decode()
    assert json.loads(body)["library_root"] == str(api["root"])
