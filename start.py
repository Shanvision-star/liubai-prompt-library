"""留白的跨平台启动入口：核对本机服务，打开浏览器，并在终端中管理服务生命周期。"""

import argparse
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser


PROJECT_ROOT = Path(__file__).resolve().parent
APP_ID = "prompt-library-desktop"


def port_number(value):
    """拒绝无效端口，避免打开与实际监听地址不同的浏览器页面。"""
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("端口必须在 1–65535 之间")
    return port


def same_directory(left, right):
    return os.path.normcase(str(Path(left).resolve())) == os.path.normcase(str(Path(right).resolve()))


def expected_version():
    if str(PROJECT_ROOT / "desktop") not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT / "desktop"))
    from library_export import APP_VERSION
    return APP_VERSION


def existing_service(port, data_root):
    """只复用同一资料目录的服务；其他占用端口的程序保持原样。"""
    with socket.socket() as connection:
        connection.settimeout(0.4)
        if connection.connect_ex(("127.0.0.1", port)) != 0:
            return False
    try:
        with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as response:
            health = json.loads(response.read(16385))
        if (not isinstance(health, dict) or health.get("app") != APP_ID
                or not isinstance(health.get("library_root"), str)):
            raise ValueError("服务身份不匹配")
    except (URLError, OSError, ValueError) as error:
        raise ValueError(f"端口 {port} 已被其他程序占用，请使用 --port 选择另一个端口。") from error
    if not same_directory(health["library_root"], data_root):
        raise ValueError(f"端口 {port} 正在打开另一份素材库；请使用相同的 --data-root，或换一个 --port。")
    if health.get("version") != expected_version():
        raise ValueError("旧版服务仍在运行，请先用 Ctrl+C 或原来的 Stop-Desktop.ps1 停止，再启动更新后的程序。")
    return True


def open_browser(url):
    if not webbrowser.open(url, new=2):
        print(f"浏览器未自动打开，请访问 {url}", flush=True)


def open_when_ready(port, data_root, stopped):
    # 健康检查成功后才打开页面，不以固定等待时间假定初始化完成。
    deadline = time.monotonic() + 20
    while not stopped.is_set() and time.monotonic() < deadline:
        try:
            if existing_service(port, data_root):
                if not stopped.is_set():
                    open_browser(f"http://127.0.0.1:{port}")
                return
        except ValueError:
            pass
        stopped.wait(0.15)


def main(argv=None):
    """保持原有默认目录；明确指定目录时，界面与 API 共用该资料库。"""
    if sys.version_info < (3, 11):
        print("留白需要 Python 3.11 或更新版本。", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description="启动留白 · 提示词素材库")
    parser.add_argument("--data-root", type=Path, default=PROJECT_ROOT, help="资料目录，默认当前程序目录")
    parser.add_argument("--port", type=port_number, default=8767, help="本机端口，默认 8767")
    parser.add_argument("--no-browser", action="store_true", help="只启动服务，不打开浏览器")
    args = parser.parse_args(argv)
    data_root = args.data_root.expanduser().resolve()
    url = f"http://127.0.0.1:{args.port}"
    stopped = threading.Event()
    try:
        if existing_service(args.port, data_root):
            print(f"已连接现有素材库：{url}\n资料目录：{data_root}", flush=True)
            if not args.no_browser:
                open_browser(url)
            return 0
        if str(PROJECT_ROOT / "desktop") not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT / "desktop"))
        from server import main as serve

        print(f"正在启动留白：{url}\n资料目录：{data_root}\n按 Ctrl+C 停止服务。", flush=True)
        if not args.no_browser:
            threading.Thread(target=open_when_ready, args=(args.port, data_root, stopped), daemon=True).start()
        serve(["--data-root", str(data_root), "--port", str(args.port)])
        return 0
    except KeyboardInterrupt:
        print("\n留白服务已停止。", flush=True)
        return 0
    except (OSError, ValueError) as error:
        print(f"无法启动留白：{error}", file=sys.stderr, flush=True)
        return 1
    finally:
        stopped.set()


if __name__ == "__main__":
    raise SystemExit(main())
