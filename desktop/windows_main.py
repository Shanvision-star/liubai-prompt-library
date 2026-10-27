"""Windows 安装版入口：内置运行环境、独立资料目录、单实例及显式停止。"""
import argparse
import ctypes
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import webbrowser
from urllib.request import Request, urlopen

from bundled_library import install_collection
from library_export import APP_VERSION
from reference_runner import RunLock
from server import Library, LocalServer
from startup_notice import StartupNotice


def data_directory():
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Liubai" / "library"


def health(port):
    try:
        with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as response:
            return json.load(response)
    except (OSError, ValueError):
        return None


def open_window(url, root):
    candidates = [Path(base) / suffix for base in (os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", ""), os.environ.get("LOCALAPPDATA", "")) if base for suffix in ("Microsoft/Edge/Application/msedge.exe", "Google/Chrome/Application/chrome.exe")]
    # 冻结程序的 DLL 搜索目录不能传给外部浏览器。
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetDllDirectoryW(None)
    try:
        browser = next((p for p in candidates if p.is_file()), None)
        if browser:
            subprocess.Popen([str(browser), "--app=" + url, "--user-data-dir=" + str(root / "desktop/.runtime/browser-profile"), "--no-first-run", "--window-size=1440,960"])
        else:
            webbrowser.open(url)
    finally:
        if getattr(sys, "frozen", False) and sys.platform == "win32":
            ctypes.windll.kernel32.SetDllDirectoryW(sys._MEIPASS)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=data_directory())
    parser.add_argument("--port", type=int)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--stop", action="store_true")
    args = parser.parse_args(argv)
    root = args.data_root.expanduser().resolve()
    runtime = root / "desktop/.runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=runtime / "server.log", encoding="utf-8", level=logging.INFO)
    lock = RunLock(runtime / "application.lock")
    acquired = False
    server = None
    try:
        address_file = runtime / "app-address.json"
        saved_port = json.loads(address_file.read_text(encoding="utf-8"))["port"] if address_file.exists() else None
        existing = health(saved_port) if saved_port else None
        matches = existing and existing.get("app") == "prompt-library-desktop" and os.path.normcase(existing.get("library_root", "")) == os.path.normcase(str(root))
        if args.stop:
            if matches:
                token = (runtime / "api-token").read_text(encoding="utf-8").strip()
                request = Request(f"http://127.0.0.1:{saved_port}/api/application/quit", data=b"{}", headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
                with urlopen(request, timeout=5):
                    pass
            return 0
        if matches:
            if existing.get("version") != APP_VERSION:
                raise ValueError("旧版留白仍在运行，请先使用“关闭留白”，再启动新版")
            if not args.no_browser:
                open_window(f"http://127.0.0.1:{saved_port}", root)
            return 0
        acquired = lock.acquire()
        if not acquired:
            raise ValueError("留白正在启动，请稍候重新打开")
        if args.port is not None and not 1 <= args.port <= 65535:
            raise ValueError("端口必须为 1–65535")
        notice = StartupNotice() if not args.no_browser and not (root / "index.json").exists() else None
        try:
            install_collection(root)
        finally:
            if notice:
                notice.close()
        if notice and notice.cancelled:
            return 0
        library = Library(root)
        for port in ([args.port] if args.port else range(8767, 8788)):
            try:
                server = LocalServer(("127.0.0.1", port), library)
                break
            except OSError as error:
                if error.errno not in (98, 48, 10048) and getattr(error, "winerror", None) != 10048:
                    raise
        if server is None:
            raise ValueError("本机端口已占用，请通过 --port 指定其他端口")
        address_file.write_text(json.dumps({"port": server.server_port}), encoding="utf-8")
        if not args.no_browser:
            threading.Thread(target=open_window, args=(f"http://127.0.0.1:{server.server_port}", root), daemon=True).start()
        server.serve_forever()
        return 0
    except Exception as error:
        logging.exception("启动或停止失败")
        if not args.no_browser and sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(0, f"{error}\n\n日志：{runtime / 'server.log'}", "留白", 0x10)
        return 1
    finally:
        if server:
            server.server_close()
        if acquired:
            lock.release()


if __name__ == "__main__":
    raise SystemExit(main())
