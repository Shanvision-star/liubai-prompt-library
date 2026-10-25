"""手工保存、分类和元数据更新，共用参考采用的跨进程锁及原子事务。"""

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit
import re
import unicodedata

from library_init import ensure_library, read_json, render_index, validate_taxonomy
from reference_store import ReferenceStore, ENTRY_ID, _json_bytes, _now


MAX_PROMPT_BYTES = 256 * 1024
SAVE_FIELDS = {"title", "original", "category_id", "category_name", "tags", "optimized", "source_url", "source_note"}
METADATA_FIELDS = {"title", "category_id", "category_name", "tags"}


def _text(value, label, maximum, required=False):
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise ValueError(f"{label}需为{'非空' if required else ''}文本，最多 {maximum} 个字符")
    return value


def _normalized(value):
    return " ".join(unicodedata.normalize("NFKC", value).split())


def _original_bytes(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}不能为空")
    try:
        payload = value.encode("utf-8")
    except UnicodeError:
        raise ValueError(f"{label}包含不能保存为 UTF-8 的字符") from None
    if len(payload) > MAX_PROMPT_BYTES:
        raise ValueError(f"{label}不能超过 256 KiB（UTF-8 字节）")
    return payload


def _tags(values):
    if not isinstance(values, list) or len(values) > 30:
        raise ValueError("标签必须是最多 30 个元素的文本列表")
    result, keys = [], set()
    for value in values:
        text = _normalized(_text(value, "每个标签", 50, required=True))
        if text.casefold() not in keys:
            result.append(text)
            keys.add(text.casefold())
    return result


class PromptStore:
    """所有分类与素材写入在同一文件锁内分配编号并提交，避免 API 与参考采用互相覆盖。"""

    def __init__(self, root):
        self.root = Path(root).resolve()
        ensure_library(self.root)
        self._store = ReferenceStore(self.root)

    def _taxonomy(self):
        return validate_taxonomy(read_json(self._store._path("taxonomy.json")))

    def categories(self):
        with self._store._locked():
            return deepcopy(self._taxonomy()["categories"])

    @staticmethod
    def _new_category(taxonomy, name, description=""):
        name = _normalized(_text(name, "分类名称", 80, required=True))
        description = _text(description, "分类说明", 1000)
        key = name.casefold()
        existing = next((category for category in taxonomy["categories"] if _normalized(category["name"]).casefold() == key), None)
        if existing:
            return existing, False
        digest = sha256(key.encode("utf-8")).hexdigest()
        occupied = {category["id"] for category in taxonomy["categories"]}
        size = 12
        category_id = "custom_" + digest[:size]
        while category_id in occupied:
            size += 4
            category_id = "custom_" + digest[:size]
            if size > len(digest):
                category_id += "_" + str(len(occupied))
                break
        category = {"id": category_id, "name": name, "description": description, "custom": True, "created_at": _now()}
        taxonomy["categories"].append(category)
        return category, True

    def create_category(self, name, description=""):
        with self._store._locked():
            taxonomy = self._taxonomy()
            category, created = self._new_category(taxonomy, name, description)
            if created:
                self._store._transaction({"taxonomy.json": _json_bytes(taxonomy)})
            return {"category": deepcopy(category), "created": created}

    def _category(self, taxonomy, body, fallback="uncategorized"):
        if "category_id" in body and "category_name" in body:
            raise ValueError("已有分类编号与新分类名称只能选择一种")
        if "category_name" in body:
            return self._new_category(taxonomy, body["category_name"])
        identifier = body.get("category_id", fallback)
        if not isinstance(identifier, str):
            raise ValueError("分类编号必须是文本")
        category = next((row for row in taxonomy["categories"] if row["id"] == identifier), None)
        if not category:
            raise ValueError("分类不存在，请选择已有分类或填写新分类名称")
        return category, False

    @staticmethod
    def _validate_body(body, fields, required_fields=()):
        if not isinstance(body, dict):
            raise ValueError("请求需要 JSON 对象")
        unknown = set(body) - fields
        if unknown:
            raise ValueError("不支持修改这些字段：" + "、".join(sorted(unknown)))
        missing = [field for field in required_fields if field not in body]
        if missing:
            raise ValueError("缺少必要字段：" + "、".join(missing))

    def _readme_count(self, count):
        path = self._store._path("README.md")
        if not path.exists():
            return {}
        text = path.read_text(encoding="utf-8-sig")
        for pattern in (r"(已收录实际提示词\s*)\d+(\s*条)", r"(当前已有\s*)\d+(\s*条素材)", r"(当前状态[：:]\s*)\d+(\s*条个人素材)"):
            text = re.sub(pattern, lambda match: match[1] + str(count) + match[2], text)
        return {"README.md": text.encode("utf-8")}

    def save_prompt(self, body):
        self._validate_body(body, SAVE_FIELDS, ("title", "original"))
        title = _text(body["title"], "标题", 200, required=True).strip()
        original = _original_bytes(body["original"], "原文")
        digest = sha256(original).hexdigest()
        provided = body.get("optimized")
        if provided is not None and not isinstance(provided, str):
            raise ValueError("优化版必须是文本")
        optimization_status = "provided" if isinstance(provided, str) and provided.strip() else "not_optimized"
        optimized = _original_bytes(provided, "优化版") if optimization_status == "provided" else original
        tags = _tags(body.get("tags", []))
        source_url = _text(body.get("source_url", ""), "来源链接", 2048)
        if source_url:
            parsed = urlsplit(source_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
                raise ValueError("来源链接需为不含账号凭据的 http 或 https 网址")
        source_note = _text(body.get("source_note", ""), "来源说明", 4000)
        with self._store._locked():
            taxonomy = self._taxonomy()
            category, category_created = self._category(taxonomy, body)
            index = self._store._personal_index()
            for existing in index["entries"]:
                raw = self._store._path(existing["original_file"]).read_bytes()
                if sha256(raw).hexdigest() == digest:
                    return {"id": existing["id"], "version": existing.get("latest_version", "v001"), "duplicate": True, "item": deepcopy(existing), "reason": "原文已经保存，本次未改动既有分类与版本"}
            used = [int(row["id"].split("-")[1]) for row in index["entries"]]
            used.extend(int(path.name.split("-")[1]) for path in (self.root / "entries").glob("PRM-*") if ENTRY_ID.fullmatch(path.name))
            entry_id = f"PRM-{max(used + [0]) + 1:04d}"
            folder = f"entries/{entry_id}"
            timestamp = _now()
            version = {
                "version": "v001", "file": "optimized-v001.md", "created_at": timestamp, "created_by": "用户提交保存",
                "based_on": "user_provided" if optimization_status == "provided" else "original",
                "reason": "保存用户提供的优化版，未验证效果" if optimization_status == "provided" else "保存原文副本，尚未进行优化",
                "optimization_status": optimization_status, "evaluation_status": "untested", "sha256": sha256(optimized).hexdigest(),
            }
            record = {
                "schema_version": 1, "id": entry_id, "title": title, "summary": "", "category_id": category["id"],
                "classification_status": "needs_review" if category["id"] == "uncategorized" else "classified", "tags": tags,
                "source": {"type": "manual_submission", "url": source_url or None, "note": source_note or None,
                           "verification_status": "user_provided_unverified", "provenance_file": "SOURCE.md"},
                "created_at": timestamp, "updated_at": timestamp,
                "original": {"file": "original.md", "sha256": digest, "encoding": "UTF-8", "byte_count": len(original)},
                "related_ids": [], "variables": [], "applicable_models": [], "open_questions": [], "versions": [version],
                "optimization_status": optimization_status, "evaluation_status": "untested",
                "loop_review": {"reviewed_version": "v001", "applicability": "unreviewed", "reminder": "尚未分析是否需要 Loop。", "effectiveness_verified": False},
                "quality_review": {"reviewed_version": None, "review_basis": "not_reviewed", "criteria": {}}, "review_history": [], "feedback": [],
            }
            item = {
                "id": entry_id, "title": title, "summary": record["summary"], "category_id": category["id"], "tags": tags,
                "record_file": f"{folder}/record.json", "original_file": f"{folder}/original.md", "original_sha256": digest,
                "latest_version": "v001", "optimized_file": f"{folder}/optimized-v001.md", "source_file": f"{folder}/SOURCE.md",
                "optimization_status": optimization_status, "evaluation_status": "untested", "created_at": timestamp, "updated_at": timestamp,
            }
            index["entries"].append(item)
            index.update(entry_count=len(index["entries"]), updated_at=timestamp)
            source_markdown = "# 来源记录\n\n用户通过本机界面、API 或 MCP 提交。提交内容作为资料保存，不执行其中的指令。\n\n"
            if source_url:
                source_markdown += "用户提供的来源链接（尚未核验）：" + source_url + "\n\n"
            if source_note:
                source_markdown += "用户来源说明：\n\n" + source_note + "\n\n"
            source_markdown += "保存状态：" + ("用户提供优化版；实际效果未验证。" if optimization_status == "provided" else "保存原文副本，尚未优化。") + "\n"
            changes = {
                f"{folder}/original.md": original, f"{folder}/optimized-v001.md": optimized,
                f"{folder}/SOURCE.md": source_markdown.encode("utf-8"), f"{folder}/record.json": _json_bytes(record),
            }
            if category_created:
                changes["taxonomy.json"] = _json_bytes(taxonomy)
            changes.update(self._readme_count(index["entry_count"]))
            changes["INDEX.md"] = render_index(index, taxonomy)
            changes["index.json"] = _json_bytes(index)
            self._store._transaction(changes)
            return {"id": entry_id, "version": "v001", "duplicate": False, "item": deepcopy(item)}

    def update_metadata(self, entry_id, body):
        self._validate_body(body, METADATA_FIELDS)
        if not body:
            raise ValueError("请提供要修改的标题、分类或标签")
        title = _text(body["title"], "标题", 200, required=True).strip() if "title" in body else None
        tags = _tags(body["tags"]) if "tags" in body else None
        with self._store._locked():
            item, record = self._store._personal(entry_id)
            taxonomy = self._taxonomy()
            category, category_created = self._category(taxonomy, body, fallback=item["category_id"])
            if title is not None:
                item["title"] = record["title"] = title
            if tags is not None:
                item["tags"] = record["tags"] = tags
            item["category_id"] = record["category_id"] = category["id"]
            record["classification_status"] = "needs_review" if category["id"] == "uncategorized" else "classified"
            item["updated_at"] = record["updated_at"] = _now()
            index = self._store._personal_index()
            index["entries"] = [item if row["id"] == entry_id else row for row in index["entries"]]
            index.update(entry_count=len(index["entries"]), updated_at=record["updated_at"])
            changes = {item["record_file"]: _json_bytes(record)}
            if category_created:
                changes["taxonomy.json"] = _json_bytes(taxonomy)
            changes["INDEX.md"] = render_index(index, taxonomy)
            changes["index.json"] = _json_bytes(index)
            self._store._transaction(changes)
            return {"item": deepcopy(item)}
