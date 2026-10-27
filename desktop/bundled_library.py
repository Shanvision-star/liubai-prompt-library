"""首次使用时以事务安装公开素材；已有库永不被发行内容覆盖。"""
from hashlib import sha256
from pathlib import Path, PurePosixPath
import json

from reference_store import ReferenceStore, _json_bytes
from runtime_paths import resource_root


def install_collection(root, source=None):
    root = Path(root).resolve()
    source = Path(source) if source else resource_root() / "bundled-library"
    store = ReferenceStore(root)
    with store._locked():
        if (root / "index.json").exists():
            return False
        if (root / "taxonomy.json").exists() or (root / "INDEX.md").exists() or any((root / "entries").rglob("*")) or list((root / "references").glob("REF-*")):
            raise ValueError("目录已有资料但索引不完整，请先恢复；内置素材不会覆盖它")
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        changes = {}
        for row in manifest["files"]:
            name = row["path"]
            path = PurePosixPath(name)
            allowed = name in {"index.json", "INDEX.md", "taxonomy.json", "references/index.json"} or (path.parts[0] in {"entries", "references"} and len(path.parts) > 2 and path.parts[1].startswith(("PRM-", "REF-")))
            if not allowed or ".." in path.parts or path.is_absolute() or "\\" in name:
                raise ValueError("内置素材清单含不允许的路径")
            candidate = source / name
            if not candidate.resolve().is_relative_to(source.resolve()) or candidate.is_symlink():
                raise ValueError("内置素材不能引用外部文件")
            data = candidate.read_bytes()
            if sha256(data).hexdigest() != row["sha256"]:
                raise ValueError(f"内置素材校验失败：{name}")
            changes[name] = data
        if not {"index.json", "taxonomy.json"}.issubset(changes):
            raise ValueError("内置素材缺少索引或分类")
        changes["installed-collection.json"] = _json_bytes({"version": manifest["version"], "entry_count": manifest["entry_count"], "reference_count": manifest["reference_count"]})
        store._transaction(changes)
    return True
