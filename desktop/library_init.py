"""空素材库初始化与一致性保护；已有资料和自定义分类不被默认模板覆盖。"""

from copy import deepcopy
from pathlib import Path
import json
import re

from reference_store import ReferenceStore, ENTRY_ID, _json_bytes, _now
from runtime_paths import resource_root


DEFAULT_TAXONOMY = resource_root() / "defaults" / "taxonomy.json"


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, UnicodeError) as error:
        raise ValueError(f"素材库文件格式异常：{path.name}，请保留原文件并修复") from error


def validate_taxonomy(taxonomy):
    if not isinstance(taxonomy, dict) or not isinstance(taxonomy.get("categories"), list):
        raise ValueError("taxonomy.json 需要有效的分类列表")
    identifiers = set()
    for item in taxonomy["categories"]:
        if (not isinstance(item, dict) or not isinstance(item.get("id"), str)
                or not re.fullmatch(r"[a-z][a-z0-9_-]*", item["id"])
                or not isinstance(item.get("name"), str) or not item["name"].strip()
                or item["id"] in identifiers):
            raise ValueError("分类存在无效或重复的编号，停止初始化以保护现有资料")
        identifiers.add(item["id"])
    return taxonomy


def render_index(index, taxonomy):
    names = {category["id"]: category["name"] for category in taxonomy["categories"]}

    def escape(value):
        text = str(value).replace("\n", " ").replace("\r", " ")
        return re.sub(r"([\\`*{}\[\]()#+!|<>])", r"\\\1", text)

    entries = index["entries"]
    lines = ["# 提示词目录", "", f"实际素材：**{len(entries)} 条**。", "", "每条保留原文与独立版本。保存或改写完成不代表实际效果已验证。", "", "| 编号 | 标题 | 分类 | 标签 | 最新版本 | 效果状态 |", "| --- | --- | --- | --- | --- | --- |"]
    for item in entries:
        version = item.get("latest_version", "v001")
        version_label = version + (" 保存版" if item.get("optimization_status") == "not_optimized" else "")
        effect = "待验证" if item.get("evaluation_status", "untested") == "untested" else escape(item["evaluation_status"])
        lines.append(f"| [{item['id']} 原文]({item['original_file']}) | {escape(item['title'])} | {escape(names.get(item['category_id'], item['category_id']))} | {escape('、'.join(item.get('tags', [])))} | [{version_label}]({item['optimized_file']}) | {effect} |")
    lines.extend(["", "[返回使用说明](README.md)", ""])
    return "\n".join(lines).encode("utf-8")


def ensure_library(root):
    """首次建立空库；不完整的已有库报错，绝不以空索引覆盖。"""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    store = ReferenceStore(root)
    with store._locked():
        index_path = store._path("index.json")
        taxonomy_path = store._path("taxonomy.json")
        entries_dir = store._path("entries")
        original_files = [path for path in entries_dir.rglob("*") if path.is_file() and path.name != ".gitkeep"] if entries_dir.exists() else []
        if not index_path.exists() and (original_files or store._path("INDEX.md").exists()):
            raise ValueError("检测到已有素材或目录但 index.json 缺失；请恢复索引，不能初始化为空库")
        index = read_json(index_path) if index_path.exists() else {
            "schema_version": 1, "library_name": "留白 · 提示词素材库", "timezone": "Asia/Shanghai",
            "created_date": _now()[:10], "updated_at": _now(), "entry_count": 0, "entries": [],
        }
        if not isinstance(index, dict) or not isinstance(index.get("entries"), list):
            raise ValueError("index.json 需要有效的 entries 列表")
        if "entry_count" in index and index["entry_count"] != len(index["entries"]):
            raise ValueError("索引条目数量不一致，请先修复，不能重置已有素材")
        if not taxonomy_path.exists() and (index["entries"] or list(store.directory.glob("REF-*/record.json"))):
            raise ValueError("已有素材或参考的 taxonomy.json 缺失；请恢复分类后再打开")
        taxonomy = validate_taxonomy(read_json(taxonomy_path if taxonomy_path.exists() else DEFAULT_TAXONOMY))
        category_ids = {category["id"] for category in taxonomy["categories"]}
        identifiers = set()
        folders = set()
        for item in index["entries"]:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not ENTRY_ID.fullmatch(item["id"]) or item["id"] in identifiers:
                raise ValueError("素材索引存在无效或重复编号")
            identifiers.add(item["id"])
            if item.get("category_id") not in category_ids:
                raise ValueError(f"素材 {item['id']} 引用的分类不存在，请先修复分类")
            for field in ("record_file", "original_file", "optimized_file"):
                if not isinstance(item.get(field), str) or not store._path(item[field]).is_file():
                    raise ValueError(f"素材 {item['id']} 的 {field} 缺失；现有索引不会被覆盖")
            record_path = store._path(item["record_file"])
            record = read_json(record_path)
            if not isinstance(record, dict) or record.get("id") != item["id"]:
                raise ValueError(f"素材 {item['id']} 的记录与索引不一致")
            folders.add(record_path.parent)
        for path in original_files:
            if not any(path.is_relative_to(folder) for folder in folders):
                raise ValueError("entries 中存在未被索引登记的资料，请先核对，不能自动清空或忽略")
        changes = {}
        if not taxonomy_path.exists():
            changes["taxonomy.json"] = _json_bytes(deepcopy(taxonomy))
        if not store._path("INDEX.md").exists():
            changes["INDEX.md"] = render_index(index, taxonomy)
        if not index_path.exists():
            changes["index.json"] = _json_bytes(index)
        entries_dir.mkdir(exist_ok=True)
        if changes:
            store._transaction(changes)
        return {"root": str(root), "created": list(changes), "entry_count": len(index["entries"])}
