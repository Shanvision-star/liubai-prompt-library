"""构建 Windows 安装包，收集运行许可并生成下载校验清单。"""
import argparse
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import shutil
import ssl
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktop"))
from library_export import APP_VERSION


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iscc", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/windows")
    parser.add_argument("--skip-freeze", action="store_true")
    args = parser.parse_args()
    if sys.platform != "win32":
        raise SystemExit("Windows 安装包必须在 Windows 上构建")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if not args.skip_freeze:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--distpath", str(out), "--workpath", str(out / "work"), str(ROOT / "packaging/windows.spec")], cwd=ROOT, check=True)
    licenses = out / "runtime-licenses"
    licenses.mkdir(exist_ok=True)
    shutil.copyfile(Path(sys.base_prefix) / "LICENSE.txt", licenses / "Python.txt")
    distro = importlib.metadata.distribution("pyinstaller")
    license_path = next(p for p in distro.files if str(p).endswith("licenses/COPYING.txt"))
    shutil.copyfile(distro.locate_file(license_path), licenses / "PyInstaller.txt")
    shutil.copyfile(args.iscc.resolve().parent / "License.txt", licenses / "InnoSetup.txt")
    shutil.copyfile(ROOT / "packaging/licenses/OpenSSL.txt", licenses / "OpenSSL.txt")
    (licenses / "BUILD.json").write_text(json.dumps({"app_version": APP_VERSION, "python": sys.version.split()[0], "pyinstaller": distro.version, "openssl": ssl.OPENSSL_VERSION}, indent=2), encoding="utf-8")
    release = out / "release"
    release.mkdir(exist_ok=True)
    subprocess.run([str(args.iscc.resolve()), "/Qp", f"/DBuildDir={out}", f"/O{release}", str(ROOT / "packaging/windows.iss")], cwd=ROOT, check=True)
    installer = release / f"Liubai-Setup-{APP_VERSION}-windows-x64.exe"
    (release / "SHA256SUMS.txt").write_text(sha256(installer.read_bytes()).hexdigest() + "  " + installer.name + "\n", encoding="ascii")
    print(installer)


if __name__ == "__main__":
    main()
