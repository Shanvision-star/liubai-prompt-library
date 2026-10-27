"""隔离验证安装包：清空 Python 环境路径，检查启动、素材、MCP、重复安装与卸载。"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--keep-running", action="store_true")
    args = parser.parse_args()
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
                if get("/api/health")["version"] == "0.5.0":
                    return process
            except OSError:
                time.sleep(0.3)
        raise AssertionError("独立程序启动超时")
    process = launch()
    report = {"installer_sha256": sha256(args.installer.read_bytes()).hexdigest(), "python_removed_from_environment": True, "port": port, "installation": str(installation), "data_root": str(data), "process_id": process.pid}
    assert get("/api/library")["entry_count"] == 222
    assert len(get("/api/references")["references"]) == 13
    prompt = get("/api/entries/PRM-0205")
    assert prompt["selected_version"] == "v002" and prompt["analysis"] and "{{主体或项目}}" in prompt["optimized"]
    report["bundled_collection"] = "222 prompts, 13 references, Chinese template and analysis readable"
    token = (data / "desktop/.runtime/api-token").read_text(encoding="utf-8").strip()
    original = "安装后保存的私人素材\r\n保留原文。\n"
    req = Request(url + "/api/prompts", data=json.dumps({"title": "安装验证", "original": original}, ensure_ascii=False).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    with urlopen(req, timeout=30) as response:
        saved = json.load(response)
    assert get("/api/entries/" + saved["id"])["original"] == original
    report["saved_id"] = saved["id"]
    info = get("/api/app-info")
    import tomllib
    config = tomllib.loads(info["mcp_config"])["mcp_servers"]["liubai"]
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "installer-smoke", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "liubai_save_prompt", "arguments": {"title": "MCP 安装验证", "original": "独立 MCP 不需要 Python", "category_id": "development"}}},
    ]
    reply = command([config["command"], *config["args"]], input=("\n".join(json.dumps(m, ensure_ascii=False) for m in messages) + "\n").encode(), capture_output=True)
    results = [json.loads(line) for line in reply.stdout.decode("utf-8").splitlines()]
    assert results[-1]["id"] == 2 and not results[-1].get("error") and not results[-1]["result"].get("isError")
    assert get("/api/library")["entry_count"] == 224
    report["mcp"] = "bundled executable initialized and saved through protocol"
    before = {str(p.relative_to(data)): sha256(p.read_bytes()).hexdigest() for p in (data / "entries").rglob("*") if p.is_file()}
    command([exe, "--data-root", data, "--stop", "--no-browser"])
    process.wait(timeout=15)
    install()
    process = launch()
    assert get("/api/library")["entry_count"] == 224
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
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
