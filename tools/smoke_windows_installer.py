"""隔离验证双语安装、素材、MCP、备份恢复、重复安装与卸载。"""
import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktop"))
from library_export import APP_VERSION


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--keep-running", action="store_true")
    args = parser.parse_args()
    collection = json.loads((ROOT / "bundled-library/manifest.json").read_text(encoding="utf-8"))
    expected_entries, expected_references = collection["entry_count"], collection["reference_count"]
    import winreg
    key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Shanvision.Liubai.PromptLibrary_is1"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key):
            raise SystemExit("当前用户已有留白安装记录；请换测试用户，不能覆盖日常安装")
    except FileNotFoundError:
        pass
    menu_root = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs"
    # 禁用分组选择页的安装包会忽略 /GROUP，即使没有注册表记录也可能已有快捷方式。
    if any((menu_root / name).exists() for name in ("Liubai", "留白")):
        raise SystemExit("当前用户已有留白开始菜单目录；请换测试用户，保护日常快捷方式")
    work = args.workdir.resolve()
    work.mkdir(parents=True, exist_ok=False)
    installation, data = work / "installed", work / "用户 素材库"
    env = dict(os.environ)
    env["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
    # 卸载程序会以默认资料路径执行 --stop，测试中须与日常资料隔离。
    env["LOCALAPPDATA"] = str(work / "local-appdata")
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    flags = subprocess.CREATE_NO_WINDOW
    def command(argv, **kwargs):
        return subprocess.run([str(x) for x in argv], env=env, creationflags=flags, check=True, timeout=180, **kwargs)
    def install(language, shortcuts):
        command([args.installer.resolve(), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/NOCLOSEAPPLICATIONS", f"/LANG={language}", f"/DIR={installation}", f"/LOG={work / (language + '.log')}"])
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as installed_key:
            menu_group = winreg.QueryValueEx(installed_key, "Inno Setup: Icon Group")[0]
        menu = menu_root / menu_group
        assert all((menu / name).is_file() for name in shortcuts)
        return menu_group
    menu_group = install("english", ("Liubai.lnk", "Close Liubai.lnk"))
    exe = installation / "Liubai.exe"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    def get(path):
        with urlopen(url + path, timeout=30) as response:
            return json.load(response)
    def launch(library_root=data):
        process = subprocess.Popen([str(exe), "--data-root", str(library_root), "--port", str(port), "--no-browser"], env=env, creationflags=flags)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise AssertionError(f"程序提前退出 {process.returncode}；查看 {library_root / 'desktop/.runtime/server.log'}")
            try:
                health = get("/api/health")
                if health["version"] == APP_VERSION and Path(health["library_root"]) == library_root:
                    return process
            except OSError:
                time.sleep(0.3)
        raise AssertionError("独立程序启动超时")
    process = launch()
    report = {"installer_sha256": sha256(args.installer.read_bytes()).hexdigest(), "python_removed_from_environment": True, "port": port, "installation": str(installation), "data_root": str(data), "process_id": process.pid}
    report["start_menu_shortcuts"] = True
    report["start_menu_group"] = menu_group
    assert get("/api/language-preference") == {"language": "auto"}
    assert isinstance(get("/api/system-language")["language"], str)
    assert get("/api/library")["entry_count"] == expected_entries
    assert len(get("/api/references")["references"]) == expected_references
    prompt = get("/api/entries/PRM-0218")
    assert prompt["selected_version"] == "v002" and prompt["analysis"] and "{{主体或项目}}" in prompt["optimized"]
    assert prompt["teaching_status"] == "ready" and "只改一个条件" in prompt["analysis"]
    motion = get("/api/entries/PRM-0243")
    pair = motion["reading_pair"]
    assert pair["copyable"] and pair["translation_status"] == "ready"
    assert pair["original"] == motion["original"] and "Pop-in" in pair["original"] and "弹跳" in pair["translation"]
    assert motion["teaching_status"] == "ready" and "角标" in motion["analysis"]
    english = get("/api/entries/PRM-0159")["reading_pair_en"]
    assert english["translation_status"] == "ready" and "30-second video" in english["translation"]
    with urlopen(url + "/download/PRM-0243/original", timeout=30) as response:
        assert sha256(response.read()).hexdigest() == motion["record"]["original"]["sha256"]
    report["bilingual_reading"] = "upstream original, matching Chinese and English translations, source and version-bound analysis"
    assets = installation / "_internal"
    assert "PRM-0218" in (assets / "learning-library/learning-route.md").read_text(encoding="utf-8")
    teaching = json.loads((assets / "learning-library/checksums.json").read_text(encoding="utf-8"))
    for row in teaching["files"]:
        assert sha256((assets / "learning-library" / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    assert not (assets / "private-learning-library").exists()
    report["teaching_resources"] = "version-bound teaching and learning route loaded from installed assets"
    report["bundled_collection"] = {"entries": expected_entries, "references": expected_references, "teaching_files_verified": len(teaching["files"])}
    with urlopen(url, timeout=30) as response:
        page = response.read().decode("utf-8")
    assert 'data-guide-open="start"' in page and 'id="guide-tab-connect"' in page
    assert 'id="guide-tab-workflow"' in page and "Claude Code" in page
    assert 'id="language-select"' in page and 'id="feedback-dialog"' in page
    for name in ("guide.js", "guide.css", "lifecycle.js", "language-choice.js", "i18n.js", "language-ui.js", "feedback.js"):
        with urlopen(url + "/" + name, timeout=30) as response:
            assert response.status == 200 and response.read()
    report["usage_guide"] = "installed HTML, chapter controls and all help/lifecycle assets served"
    token = (data / "desktop/.runtime/api-token").read_text(encoding="utf-8").strip()
    original = "安装后保存的私人素材\r\n保留原文。\n"
    req = Request(url + "/api/prompts", data=json.dumps({"title": "安装验证", "original": original}, ensure_ascii=False).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    with urlopen(req, timeout=30) as response:
        saved = json.load(response)
    assert get("/api/entries/" + saved["id"])["original"] == original
    report["saved_id"] = saved["id"]
    def post(path, body, *, browser=False):
        headers = {"Content-Type": "application/json"}
        if browser:
            headers.update({"Origin": url, "X-Prompt-Library": "1"})
        else:
            headers["Authorization"] = "Bearer " + token
        req = Request(url + path, data=json.dumps(body, ensure_ascii=False).encode(), headers=headers)
        with urlopen(req, timeout=30) as response:
            return json.load(response)
    entry_path = "/api/entries/" + saved["id"]
    assert post("/api/favorites", {"id": saved["id"], "favorite": True}, browser=True)["favorites"] == [saved["id"]]
    assert post("/api/language-preference", {"language": "en"}, browser=True) == {"language": "en"}
    try:
        post("/api/language-preference", {"language": ["en"]}, browser=True)
    except HTTPError as error:
        assert error.code == 400
    else:
        raise AssertionError("语言设置必须拒绝非字符串")
    version = post(entry_path + "/versions", {"optimized": "安装后追加的新版本", "reason": "验证独立安装包追加版本", "expected_version": "v001", "based_on_version": "v001"})
    assert version["version"] == "v002"
    current = get(entry_path)
    post(entry_path + "/analysis", {"version": "v002", "original_sha256": current["original_sha256"], "optimized_sha256": current["optimized_sha256"], "analysis_markdown": "# 安装验证拆解\n\n这是合成测试内容，未调用模型或验证实际效果。"})
    post(entry_path + "/source-notes", {"source_url": "https://example.com/installer-smoke", "source_note": "隔离安装验证的来源补充"})
    current = get(entry_path)
    assert current["original"] == original and current["analysis_origin"] == "external_client"
    assert "安装验证拆解" in current["analysis"] and len(current["record"]["source_notes"]) == 1
    assert len(current["record"]["versions"]) == 2 and not get(entry_path + "?version=v001")["analysis"]
    report["new_features"] = "v002, original/history preservation, hash-bound analysis, source note and version isolation passed"
    info = get("/api/app-info")
    import tomllib
    config = tomllib.loads(info["mcp_config"])["mcp_servers"]["liubai"]
    assert info["version"] == APP_VERSION and info["runtime_mode"] == "installed"
    assert info["client_commands"]["codex"].startswith("codex mcp add liubai -- ")
    assert info["client_commands"]["claude_code"].startswith("claude mcp add --transport stdio --scope user liubai -- ")
    assert config["command"].endswith("Liubai-MCP.exe") and config["args"] == ["--data-root", str(data)]
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "installer-smoke", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "liubai_save_prompt", "arguments": {"title": "MCP 安装验证", "original": "独立 MCP 不需要 Python", "category_id": "development"}}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "liubai_get_prompt", "arguments": {"entry_id": saved["id"], "version": "v002"}}},
    ]
    reply = command([config["command"], *config["args"]], input=("\n".join(json.dumps(m, ensure_ascii=False) for m in messages) + "\n").encode(), capture_output=True)
    results = [json.loads(line) for line in reply.stdout.decode("utf-8").splitlines()]
    replies = {row["id"]: row for row in results if "id" in row}
    assert not replies[2].get("error") and not replies[2]["result"].get("isError")
    tools = {row["name"] for row in replies[3]["result"]["tools"]}
    assert len(tools) == 8 and {"liubai_add_version", "liubai_save_analysis", "liubai_add_source_note"}.issubset(tools)
    detail = replies[4]["result"]["structuredContent"]
    assert detail["original"] == original and detail["selected_version"] == "v002"
    mcp_id = replies[2]["result"]["structuredContent"]["id"]
    def mcp_calls(calls):
        requests = messages[:2] + [{"jsonrpc": "2.0", "id": number, "method": "tools/call", "params": {"name": name, "arguments": body}} for number, name, body in calls]
        result = command([config["command"], *config["args"]], input=("\n".join(json.dumps(row, ensure_ascii=False) for row in requests) + "\n").encode(), capture_output=True)
        rows = {row["id"]: row for line in result.stdout.decode("utf-8").splitlines() if (row := json.loads(line)).get("id")}
        for number, _, _ in calls:
            assert not rows[number].get("error") and not rows[number]["result"].get("isError"), rows[number]
        return {number: rows[number]["result"]["structuredContent"] for number, _, _ in calls}
    rows = mcp_calls([
        (5, "liubai_add_version", {"entry_id": mcp_id, "optimized": "MCP 追加改编", "reason": "安装验证", "expected_version": "v001"}),
        (6, "liubai_add_source_note", {"entry_id": mcp_id, "source_note": "由安装后的 MCP 追加"}),
        (7, "liubai_get_prompt", {"entry_id": mcp_id, "version": "v002"}),
    ])
    assert rows[5]["version"] == "v002" and rows[7]["record"]["source_notes"]
    read = rows[7]
    rows = mcp_calls([
        (8, "liubai_save_analysis", {"entry_id": mcp_id, "version": "v002", "original_sha256": read["original_sha256"], "optimized_sha256": read["optimized_sha256"], "analysis_markdown": "# MCP 安装拆解\n\n合成验证，不调用模型。"}),
        (9, "liubai_get_prompt", {"entry_id": mcp_id, "version": "v002"}),
    ])
    assert "MCP 安装拆解" in rows[9]["analysis"]
    assert get("/api/library")["entry_count"] == expected_entries + 2
    report["mcp"] = "installed executable discovered 8 tools; save/read/version/source/analysis calls and readback passed"
    restored = work / "还原 素材库"
    with urlopen(url + "/download/library-backup", timeout=30) as response:
        backup = response.read()
    with ZipFile(BytesIO(backup)) as archive:
        manifest = json.loads(archive.read("backup-manifest.json"))
        assert "Liubai library backup" in archive.read("RESTORE.txt").decode("utf-8")
        assert all(sha256(archive.read(row["path"])).hexdigest() == row["sha256"] for row in manifest["files"])
        assert "desktop/.runtime/api-token" not in archive.namelist()
        archive.extractall(restored)
    before = {str(p.relative_to(data)): sha256(p.read_bytes()).hexdigest() for p in (data / "entries").rglob("*") if p.is_file()}
    command([exe, "--data-root", data, "--stop", "--no-browser"])
    process.wait(timeout=15)
    restored_process = launch(restored)
    try:
        catalogue = get("/api/library")
        assert catalogue["entry_count"] == expected_entries + 2 and catalogue["favorites"] == [saved["id"]]
        restored_prompt = get(entry_path)
        assert restored_prompt["original"] == original and restored_prompt["selected_version"] == "v002"
        assert len(restored_prompt["record"]["source_notes"]) == 1 and "安装验证拆解" in restored_prompt["analysis"]
        assert len(get("/api/references")["references"]) == expected_references
    finally:
        command([exe, "--data-root", restored, "--stop", "--no-browser"])
        restored_process.wait(timeout=15)
    report["backup_restore"] = "ZIP hashes, original, versions, analysis, source, favorites and references verified from a fresh data root"
    install("chinesesimplified", ("留白.lnk", "关闭留白.lnk"))
    report["installer_languages"] = ["english", "chinesesimplified"]
    process = launch()
    assert get("/api/library")["entry_count"] == expected_entries + 2
    assert get("/api/language-preference") == {"language": "en"}
    report["language_preference_persisted"] = True
    assert all(sha256((data / name).read_bytes()).hexdigest() == digest for name, digest in before.items())
    report["reinstall_preserves_data"] = True
    report["process_id"] = process.pid
    if not args.keep_running:
        command([exe, "--data-root", data, "--stop", "--no-browser"])
        process.wait(timeout=15)
        command([installation / "unins000.exe", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"])
        deadline = time.monotonic() + 30
        while exe.exists() and time.monotonic() < deadline:
            time.sleep(0.5)
        assert not exe.exists()
        assert all(sha256((data / name).read_bytes()).hexdigest() == digest for name, digest in before.items())
        report["uninstall_preserves_data"] = True
    (work / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    # CI 控制台可能仍是 cp1252；文件报告保留 UTF-8，控制台 JSON 使用可移植转义。
    print(json.dumps(report, ensure_ascii=True))


if __name__ == "__main__":
    main()
