"""导出可迁移的素材备份；只包含资料与收藏，不携带授权或机器调度状态。"""

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import os
import stat
import sys
import zipfile

from reference_store import ReferenceStore, ENTRY_ID, REF_ID, _now


APP_VERSION = "0.4.0"
MAX_BACKUP_BYTES = 256 * 1024 * 1024
MAX_BACKUP_FILES = 10000


def app_info(library):
    """生成当前实例的配置，避免复制示例后连到另一份空库。"""
    python = Path(sys.executable)
    if python.name.lower() == "pythonw.exe" and python.with_name("python.exe").exists():
        python = python.with_name("python.exe")
    mcp = Path(__file__).with_name("mcp_server.py").resolve()
    quote = lambda value: json.dumps(str(value), ensure_ascii=False)
    args = ["-X", "utf8", str(mcp), "--data-root", str(library.root)]
    config = "\n".join([
        "[mcp_servers.liubai]", "command = " + quote(python),
        "args = " + json.dumps(args, ensure_ascii=False),
        "startup_timeout_sec = 15", "tool_timeout_sec = 60", "enabled = true", "",
    ])
    return {"version": APP_VERSION, "library_root": str(library.root),
            "python_executable": str(python), "mcp_server": str(mcp),
            "mcp_config": config, "backup_url": "/download/library-backup"}


def export_library(library):
    """在资料事务锁内读取一致快照；遇到链接或超额时失败，不生成残缺备份。"""
    root = library.root
    store = ReferenceStore(root)
    output = BytesIO()
    manifest = {"format": "liubai-library-backup", "version": 1, "created_at": _now(), "files": []}
    total = 0

    def check_path(path):
        if not path.resolve().is_relative_to(root):
            raise ValueError("资料包含指向库外的路径，备份已停止")
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024):
            raise ValueError("资料包含符号链接或目录联接，请先核对后再备份")
        return info

    def collect(folder):
        check_path(folder)
        def traversal_error(error):
            raise error
        for directory, names, files in os.walk(folder, followlinks=False, onerror=traversal_error):
            names.sort()
            for name in names:
                check_path(Path(directory) / name)
            for name in sorted(files):
                path = Path(directory) / name
                check_path(path)
                yield path

    # 收藏有独立的进程内锁；资料与 MCP/参考采用共用跨进程锁。
    with library.lock, store._locked(), zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        def add(name, payload):
            nonlocal total
            total += len(payload)
            if total > MAX_BACKUP_BYTES or len(manifest["files"]) >= MAX_BACKUP_FILES:
                raise ValueError("备份超过 256 MiB 或 10000 个文件，请停止服务后复制整个资料目录")
            archive.writestr(name, payload)
            manifest["files"].append({"path": name, "bytes": len(payload), "sha256": sha256(payload).hexdigest()})

        paths = [root / name for name in ("index.json", "INDEX.md", "taxonomy.json")]
        reference_index = root / "references/index.json"
        if reference_index.exists():
            paths.append(reference_index)
        def data_paths():
            yield from paths
            for parent, pattern in ((root / "entries", ENTRY_ID), (root / "references", REF_ID)):
                check_path(parent)
                for folder in sorted(parent.iterdir()):
                    if pattern.fullmatch(folder.name):
                        yield from collect(folder)
        for path in data_paths():
            info = check_path(path)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("资料路径不是普通文件，备份已停止")
            if info.st_size + total > MAX_BACKUP_BYTES or len(manifest["files"]) >= MAX_BACKUP_FILES:
                raise ValueError("备份超过 256 MiB 或 10000 个文件，请停止服务后复制整个资料目录")
            add(path.relative_to(root).as_posix(), path.read_bytes())
        # 即使使用自定义 state-dir，恢复到默认位置仍能保留收藏；不复制令牌和浏览器档案。
        add("desktop/.runtime/favorites.json", json.dumps(library.favorites(), ensure_ascii=False).encode("utf-8"))
        archive.writestr("backup-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
        archive.writestr("RESTORE.txt", (
            "留白资料备份\n\n将 ZIP 解压到新的空目录，再使用新程序的 --data-root 指向该目录。\n"
            "例如：python -X utf8 start.py --data-root /path/to/restored-library\n"
            "请先检查条目、原文和历史版本，再决定是否继续使用恢复后的目录；不要覆盖现有库。\n"
            "包含个人素材、参考快照/分析、分类、索引与收藏。备份可能含私人内容，请自行妥善保存。\n"
            "不含 API 令牌、Codex 配置、网络缓存、程序、执行日志或调度注册；恢复后调度需重新配置。\n"
            "backup-manifest.json 记录各资料文件的 SHA-256，可用于校验完整性。\n"
        ).encode("utf-8"))
    return output.getvalue()
