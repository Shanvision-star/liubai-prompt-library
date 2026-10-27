"""按正文与版本绑定只读教学卡；不改写使用者保存的原文和个人版本。"""

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from runtime_paths import resource_root


@lru_cache(maxsize=4)
def _manifest(path, modified, size):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def teaching_card(entry_id, version, original, optimized, root=None):
    directory = Path(root) if root is not None else resource_root() / "learning-library"
    path = directory / "manifest.json"
    if not path.exists():
        return {"status": "missing", "markdown": ""}
    try:
        stat = path.stat()
        manifest = _manifest(str(path), stat.st_mtime_ns, stat.st_size)
        if not isinstance(manifest, dict) or not isinstance(manifest.get("entries"), dict):
            raise ValueError("教学清单格式异常")
        item = manifest["entries"].get(entry_id)
        if not item:
            return {"status": "missing", "markdown": ""}
        digest = lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()
        signature = {"version": version, "original_sha256": digest(original), "optimized_sha256": digest(optimized)}
        if signature not in item["bindings"]:
            return {"status": "version_mismatch", "markdown": ""}
        target = (directory / item["file"]).resolve()
        if not target.is_relative_to(directory.resolve()):
            raise ValueError("教学文件越界")
        data = target.read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("教学文件校验不一致")
        return {"status": "ready", "markdown": data.decode("utf-8"), "revision": item["revision"]}
    except (OSError, ValueError, KeyError, TypeError):
        # 教学资源缺损不应阻断原始素材的读取，也不能把缺损报告为分析完成。
        return {"status": "unavailable", "markdown": ""}
