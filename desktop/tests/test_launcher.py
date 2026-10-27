"""用临时资料目录验证真实启动、同库复用、端口冲突与 Windows 停止进程的身份边界。"""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
from tempfile import TemporaryFile
from urllib.error import URLError
from urllib.request import urlopen

import pytest


ROOT = Path(__file__).resolve().parents[2]


def free_port():
    with socket.socket() as connection:
        connection.bind(("127.0.0.1", 0))
        return connection.getsockname()[1]


def request(port, path="/api/health"):
    with urlopen(f"http://127.0.0.1:{port}{path}", timeout=1) as response:
        return json.load(response)


def launch_args(data_root, port):
    return [sys.executable, "-X", "utf8", str(ROOT / "start.py"), "--no-browser", "--data-root", str(data_root), "--port", str(port)]


@contextmanager
def running_launcher(data_root, port):
    child = subprocess.Popen(launch_args(data_root, port), cwd=data_root.parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if child.poll() is not None:
                stdout, stderr = child.communicate(timeout=3)
                pytest.fail(f"启动失败：{stdout.decode('utf-8')}\n{stderr.decode('utf-8')}")
            try:
                if request(port).get("app") == "prompt-library-desktop":
                    break
            except (URLError, OSError, ValueError):
                time.sleep(0.1)
        else:
            pytest.fail("临时服务未就绪")
        yield child
    finally:
        if child.poll() is None:
            child.terminate()
        child.communicate(timeout=10)


def test_launcher_bootstraps_separate_unicode_path_and_reuses_matching_server(tmp_path):
    data_root = tmp_path / "我的 素材库"
    port = free_port()
    with running_launcher(data_root, port) as child:
        assert Path(request(port)["library_root"]) == data_root
        assert request(port, "/api/library")["entry_count"] == 0
        before = (data_root / "index.json").read_bytes()
        reused = subprocess.run(launch_args(data_root, port), capture_output=True, timeout=10)
        assert reused.returncode == 0, reused.stderr.decode("utf-8")
        assert "已连接现有素材库" in reused.stdout.decode("utf-8")
        assert child.poll() is None
        assert (data_root / "index.json").read_bytes() == before


def test_launcher_refuses_another_library_without_initializing_it(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    port = free_port()
    with running_launcher(first, port):
        blocked = subprocess.run(launch_args(second, port), capture_output=True, timeout=10)
        assert blocked.returncode == 1
        assert "另一份素材库" in blocked.stderr.decode("utf-8")
        assert not second.exists()
        assert Path(request(port)["library_root"]) == first


@pytest.mark.parametrize("application,version,message", [
    ("another-app", "0.4.0", "其他程序占用"),
    ("prompt-library-desktop", "0.0.0", "旧版服务仍在运行"),
])
def test_launcher_refuses_an_unrelated_or_outdated_http_service(tmp_path, application, version, message):
    data_root = tmp_path / "library"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"app": application, "version": version, "library_root": str(data_root)}).encode("utf-8"))

        def log_message(self, *args):
            pass

    service = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=service.serve_forever, daemon=True)
    thread.start()
    try:
        blocked = subprocess.run(launch_args(data_root, service.server_port), capture_output=True, timeout=10)
        assert blocked.returncode == 1
        assert message in blocked.stderr.decode("utf-8")
        assert not data_root.exists()
        assert request(service.server_port)["app"] == application
    finally:
        service.shutdown()
        service.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("port", ["0", "65536"])
def test_launcher_validates_port_before_initializing_library(tmp_path, port):
    result = subprocess.run(launch_args(tmp_path / "untouched", port), capture_output=True, timeout=10)
    assert result.returncode == 2
    assert not (tmp_path / "untouched").exists()


def powershell(script, data_root, port, *extra):
    env = dict(os.environ)
    # 使用正在运行测试的解释器，不依赖开发者的 PATH 或 Codex 安装目录。
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "desktop" / script), "-DataRoot", str(data_root), "-Port", str(port), *extra]
    # PowerShell 后台子进程可继承额外管道句柄；文件输出让测试只等脚本退出。
    with TemporaryFile() as output, TemporaryFile() as error:
        result = subprocess.run(command, stdout=output, stderr=error, timeout=35, env=env)
        output.seek(0)
        error.seek(0)
        return subprocess.CompletedProcess(command, result.returncode, output.read(), error.read())


@pytest.mark.skipif(sys.platform != "win32" or not shutil.which("powershell.exe"), reason="Windows 桌面入口")
def test_windows_launcher_stops_only_matching_record_and_preserves_library(tmp_path):
    data_root = tmp_path / "桌面 素材库"
    port = free_port()
    record_path = data_root / "desktop/.runtime" / f"server-process-{port}.json"
    original_record = None
    try:
        started = powershell("Open-Desktop.ps1", data_root, port, "-ServerOnly")
        assert started.returncode == 0, started.stderr.decode("utf-8", errors="replace")
        assert Path(request(port)["library_root"]) == data_root
        original_record = record_path.read_bytes()
        reused = powershell("Open-Desktop.ps1", data_root, port, "-ServerOnly")
        assert reused.returncode == 0
        assert record_path.read_bytes() == original_record
        changed = json.loads(original_record.decode("utf-8-sig"))
        changed["started_utc"] = "2000-01-01T00:00:00Z"
        record_path.write_text(json.dumps(changed), encoding="utf-8-sig")
        refused = powershell("Stop-Desktop.ps1", data_root, port)
        assert refused.returncode != 0
        assert request(port)["app"] == "prompt-library-desktop"
    finally:
        if record_path.exists():
            if original_record:
                record_path.write_bytes(original_record)
            stopped = powershell("Stop-Desktop.ps1", data_root, port)
            assert stopped.returncode == 0, stopped.stderr.decode("utf-8", errors="replace")
    assert (data_root / "index.json").is_file()
    with socket.socket() as connection:
        connection.settimeout(1)
        assert connection.connect_ex(("127.0.0.1", port)) != 0
