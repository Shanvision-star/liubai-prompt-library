"""隔离验证安装包：清空 Python 环境路径，检查启动、素材、MCP、重复安装与卸载。"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen

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
    work = args.workdir.resolve()
    work.mkdir(parents=True, exist_ok=False)
    installation, data = work / "installed", work / "用户 素材库"
    env = dict(os.environ)
    env["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    flags = subprocess.CREATE_NO_WINDOW
    def command(argv, **kwargs):
        return subprocess.run([str(x) for x in argv], env=env, creationflags=flags, check=True, timeout=180, **kwargs)
    def install():
        command([args.installer.resolve(), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/NOICONS", "/GROUP=Liubai QA", f"/DIR={installation}", f"/LOG={work / 'install.log'}"])
    install()
    exe = installation / "Liubai.exe"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    def get(path):
        with urlopen(url + path, timeout=30) as response:
            return json.load(response)
    def launch():
        process = subprocess.Popen([str(exe), "--data-root", str(data), "--port", str(port), "--no-browser"], env=env, creationflags=flags)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise AssertionError(f"程序提前退出 {process.returncode}；查看 {data / 'desktop/.runtime/server.log'}")
            try:
                if get("/api/health")["version"] == APP_VERSION:
                    return process
            except OSError:
                time.sleep(0.3)
        raise AssertionError("独立程序启动超时")
    process = launch()
    report = {"installer_sha256": sha256(args.installer.read_bytes()).hexdigest(), "python_removed_from_environment": True, "port": port, "installation": str(installation), "data_root": str(data), "process_id": process.pid}
    assert get("/api/library")["entry_count"] == expected_entries
    assert len(get("/api/references")["references"]) == expected_references
    prompt = get("/api/entries/PRM-0218")
    assert prompt["selected_version"] == "v002" and prompt["analysis"] and "{{主体或项目}}" in prompt["optimized"]
    assert prompt["teaching_status"] == "ready" and "只改一个条件" in prompt["analysis"]
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
    for name in ("guide.js", "guide.css", "lifecycle.js"):
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
    def post(path, body):
        req = Request(url + path, data=json.dumps(body, ensure_ascii=False).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
        with urlopen(req, timeout=30) as response:
            return json.load(response)
    entry_path = "/api/entries/" + saved["id"]
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
    assert get("/api/library")["entry_count"] == expected_entries + 2
    report["mcp"] = "installed executable initialized, discovered all 8 tools, saved and read the selected version"
    before = {str(p.relative_to(data)): sha256(p.read_bytes()).hexdigest() for p in (data / "entries").rglob("*") if p.is_file()}
    command([exe, "--data-root", data, "--stop", "--no-browser"])
    process.wait(timeout=15)
    install()
    process = launch()
    assert get("/api/library")["entry_count"] == expected_entries + 2
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
