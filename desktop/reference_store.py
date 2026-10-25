"""参考库的原文快照、拆解版本和采用事务；所有写入均在本机文件锁内完成。"""

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path, PurePosixPath
import difflib
import json
import os
import re
import shutil
import threading
import time
import uuid
from urllib.parse import unquote, urlsplit


REF_ID = re.compile(r"REF-\d{4,}\Z")
ENTRY_ID = re.compile(r"PRM-\d{4,}\Z")
SNAPSHOT_ID = re.compile(r"s\d{3,}\Z")
_THREAD_LOCKS = {}
_THREAD_LOCKS_GUARD = threading.Lock()


def _now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else deepcopy(default)


def _digest(value):
    return sha256(value).hexdigest()


class ReferenceStore:
    """单个素材库的持久化入口，读写和中断恢复共用跨进程锁。"""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.directory = self.root / "references"
        self.directory.mkdir(parents=True, exist_ok=True)
        with _THREAD_LOCKS_GUARD:
            self._thread_lock = _THREAD_LOCKS.setdefault(str(self.root), threading.RLock())
        with self._locked():
            pass

    def _path(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("记录路径越出素材库")
        return path

    @contextmanager
    def _locked(self):
        with self._thread_lock:
            lock_path = self._path("references/.store.lock")
            with lock_path.open("a+b") as handle:
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                deadline = time.monotonic() + 30
                while True:
                    try:
                        handle.seek(0)
                        if os.name == "nt":
                            import msvcrt
                            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                        else:
                            import fcntl
                            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except (BlockingIOError, OSError):
                        if time.monotonic() >= deadline:
                            raise TimeoutError("参考库正在写入，请稍后重试")
                        time.sleep(0.05)
                try:
                    self._recover()
                    yield
                finally:
                    handle.seek(0)
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _write_durable(path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

    def _replace(self, staging, target):
        """独立替换点便于用故障注入验证实际回滚路径。"""
        os.replace(staging, target)

    def _recover(self):
        transactions = self._path("references/.transactions")
        if not transactions.exists():
            return
        for folder in sorted(transactions.iterdir()):
            if not folder.is_dir() or folder.is_symlink():
                raise ValueError("事务目录异常，请保留现场检查")
            manifest_path = folder / "manifest.json"
            if manifest_path.exists():
                manifest = _read_json(manifest_path)
                if manifest["state"] != "committed":
                    self._rollback(folder, manifest)
            shutil.rmtree(folder)

    def _rollback(self, folder, manifest):
        for row in reversed(manifest["files"]):
            target = self._path(row["path"])
            if row["existed"]:
                backup = folder / row["backup"]
                if not backup.exists():
                    raise ValueError("事务备份丢失，停止恢复以保护现有资料")
                restore = folder / (row["backup"] + ".restore")
                self._write_durable(restore, backup.read_bytes())
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(restore, target)
            elif target.exists():
                target.unlink()

    def _transaction(self, changes):
        """先落盘备份与清单，再替换文件；未完成的事务下次打开时恢复旧状态。"""
        folder = self._path("references/.transactions/" + uuid.uuid4().hex)
        folder.mkdir(parents=True)
        manifest = {"state": "prepared", "files": []}
        try:
            for number, (relative, payload) in enumerate(changes.items()):
                target = self._path(relative)
                row = {"path": relative, "existed": target.exists(), "backup": f"{number}.old", "staging": f"{number}.new"}
                if row["existed"]:
                    self._write_durable(folder / row["backup"], target.read_bytes())
                self._write_durable(folder / row["staging"], payload)
                manifest["files"].append(row)
            self._write_durable(folder / "manifest.json", _json_bytes(manifest))
            for row in manifest["files"]:
                target = self._path(row["path"])
                target.parent.mkdir(parents=True, exist_ok=True)
                self._replace(folder / row["staging"], target)
            manifest["state"] = "committed"
            self._write_durable(folder / "commit.tmp", _json_bytes(manifest))
            os.replace(folder / "commit.tmp", folder / "manifest.json")
        except BaseException:
            if (folder / "manifest.json").exists():
                self._rollback(folder, manifest)
            shutil.rmtree(folder)
            raise
        shutil.rmtree(folder)

    def _index(self):
        return _read_json(self._path("references/index.json"), {"schema_version": 1, "references": []})

    def _record(self, ref_id):
        if not isinstance(ref_id, str) or not REF_ID.fullmatch(ref_id):
            raise KeyError("参考编号无效")
        path = self._path(f"references/{ref_id}/record.json")
        if not path.exists():
            raise KeyError("找不到这份参考")
        return _read_json(path)

    @staticmethod
    def _item(record):
        return {key: deepcopy(value) for key, value in record.items() if key not in {"snapshots", "analyses", "adoptions"}}

    def _save_changes(self, record, additional=None):
        index = self._index()
        item = self._item(record)
        index["references"] = [item if row["id"] == record["id"] else row for row in index["references"]]
        if not any(row["id"] == record["id"] for row in index["references"]):
            index["references"].append(item)
        index["updated_at"] = _now()
        changes = dict(additional or {})
        changes[f"references/{record['id']}/record.json"] = _json_bytes(record)
        changes["references/index.json"] = _json_bytes(index)
        return changes

    def catalogue(self):
        with self._locked():
            return {"references": self._index()["references"], "categories": _read_json(self.root / "taxonomy.json", {"categories": []})["categories"]}

    @staticmethod
    def _source_key(source):
        span = source.get("extraction") or source.get("source_span")
        return source["repository"].lower(), source["path"], json.dumps(span, sort_keys=True, ensure_ascii=False)

    def _validate_source(self, source):
        source = deepcopy(source)
        for key in ("repository", "path", "commit", "url", "tracked_ref", "license", "license_status", "retrieved_at"):
            if key not in source or source[key] is None or source[key] == "":
                raise ValueError(f"来源缺少 {key}")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source["repository"]):
            raise ValueError("GitHub 仓库格式无效")
        path = PurePosixPath(source["path"])
        if path.is_absolute() or ".." in path.parts or "\\" in source["path"] or str(path) == ".":
            raise ValueError("来源文件路径无效")
        if not re.fullmatch(r"[a-fA-F0-9]{40}", source["commit"]):
            raise ValueError("来源必须固定到完整 commit")
        if source["license_status"] not in {"allowed", "unknown", "restricted"}:
            raise ValueError("许可状态无效")
        expected = f"https://github.com/{source['repository']}/blob/{source['commit']}/"
        if not source["url"].startswith(expected) or unquote(urlsplit(source["url"]).path).split("/blob/", 1)[-1] != source["commit"] + "/" + source["path"]:
            raise ValueError("来源网址必须指向对应仓库的固定 commit")
        return source

    def ingest(self, source, original, metadata=None):
        source = self._validate_source(source)
        metadata = deepcopy(metadata or {})
        check_failed = metadata.get("check_status") == "failed"
        if metadata.get("material_type", "prompt") not in {"prompt", "skill", "workflow", "method"}:
            raise ValueError("素材类型无效")
        if metadata.get("selection_status", "candidate") not in {"selected", "candidate", "observing", "rejected"}:
            raise ValueError("筛选状态无效")
        for field in ("tags", "related_ids"):
            if field in metadata and (not isinstance(metadata[field], list) or not all(isinstance(value, str) for value in metadata[field])):
                raise ValueError(f"{field} 必须是文本列表")
        if not isinstance(original, (str, bytes)):
            raise ValueError("原文必须是文本或原始字节")
        payload = original.encode("utf-8") if isinstance(original, str) else original
        if len(payload) > 256 * 1024:
            raise ValueError("单份原文不能超过 256 KiB")
        payload.decode("utf-8-sig")
        if not payload.strip():
            raise ValueError("空原文不能替换已有快照")
        digest = _digest(payload)
        with self._locked():
            categories = {row["id"] for row in _read_json(self.root / "taxonomy.json", {"categories": []})["categories"]}
            if metadata.get("category_id") and metadata["category_id"] not in categories:
                raise ValueError("参考分类不存在")
            rows = self._index()["references"]
            same = next((row for row in rows if self._source_key(row["source"]) == self._source_key(source)), None)
            if same is None:
                identical = next((row for row in rows if row.get("content_sha256") == digest), None)
                if identical:
                    record = self._record(identical["id"])
                    aliases = record.setdefault("alternate_sources", [])
                    if source not in aliases:
                        aliases.append(source)
                    self._transaction(self._save_changes(record))
                    return {"id": record["id"], "duplicate": True, "changed": False, "snapshot_id": record["current_snapshot_id"], "reason": "内容已存在，保留补充来源"}
            timestamp = _now()
            if same:
                record = self._record(same["id"])
                previous_success = record.get("last_success")
                old_permission = record["source"].get("license_status")
                permission_changed = (old_permission == "allowed" and source["license_status"] != "allowed") or (
                    old_permission != source["license_status"] and record["source"]["commit"] != source["commit"])
                record["source"] = source
                for key in ("quality_review", "selection_status"):
                    if key in metadata:
                        record[key] = metadata[key]
                if "related_ids" in metadata:
                    record["related_ids"] = sorted(set(record.get("related_ids", [])) | set(metadata["related_ids"]))
                record.update(last_attempt=source["retrieved_at"], last_success=previous_success if check_failed else source["retrieved_at"], last_error=metadata.get("check_error") if check_failed else None)
                if same.get("content_sha256") == digest and not permission_changed:
                    record["last_check_status"] = "failed" if check_failed else "unchanged"
                    snapshot = self._snapshot(record)
                    files = {}
                    if source["license_status"] == "allowed" and not snapshot["original_file"]:
                        snapshot["original_file"] = f"snapshots/{snapshot['id']}/original.md"
                        snapshot["original_unavailable_reason"] = None
                        files[f"references/{record['id']}/{snapshot['original_file']}"] = payload
                    if source["license_status"] == "allowed" and (snapshot["license_status"] != "allowed" or snapshot["commit"] == source["commit"]):
                        snapshot["license_status"] = "allowed"
                        for key in ("license", "license_status", "license_evidence", "license_file_url", "license_text"):
                            if key in source:
                                snapshot["source"][key] = source[key]
                        snapshot["license_reviewed_at"] = source["retrieved_at"]
                    self._transaction(self._save_changes(record, files))
                    return {"id": record["id"], "duplicate": True, "changed": False, "snapshot_id": record["current_snapshot_id"]}
            else:
                previous_success = None
                reserved = [int(path.name.split("-")[1]) for path in self.directory.glob("REF-*") if REF_ID.fullmatch(path.name)]
                serial = max([int(row["id"].split("-")[1]) for row in rows] + reserved + [0]) + 1
                record = {
                    "id": f"REF-{serial:04d}", "title": metadata.get("title") or source["path"],
                    "summary": metadata.get("summary", ""), "category_id": metadata.get("category_id", "uncategorized"),
                    "tags": metadata.get("tags", []), "material_type": metadata.get("material_type", "prompt"),
                    "selection_status": metadata.get("selection_status", "candidate"), "quality_review": metadata.get("quality_review", {}),
                    "related_ids": metadata.get("related_ids", []), "favorite": False, "followed": False,
                    "source": source, "created_at": timestamp, "snapshots": [], "analyses": [], "adoptions": [],
                }
            if record["material_type"] not in {"prompt", "skill", "workflow", "method"}:
                raise ValueError("素材类型无效")
            if record["selection_status"] not in {"selected", "candidate", "observing", "rejected"}:
                raise ValueError("筛选状态无效")
            snapshot_id = f"s{len(record['snapshots']) + 1:03d}"
            original_file = f"snapshots/{snapshot_id}/original.md" if source["license_status"] == "allowed" else None
            snapshot = {
                "id": snapshot_id, "commit": source["commit"], "sha256": digest, "byte_count": len(payload),
                "created_at": source["retrieved_at"], "source_url": source["url"], "source": deepcopy(source),
                "original_file": original_file, "license_status": source["license_status"],
                "original_unavailable_reason": None if original_file else "许可未明确允许复制，仅保留链接、元数据和必要摘要",
            }
            record["snapshots"].append(snapshot)
            record.update(current_snapshot_id=snapshot_id, content_sha256=digest, analysis_status="pending", evaluation_status="untested",
                          updated_at=timestamp, last_attempt=source["retrieved_at"], last_success=previous_success if check_failed else source["retrieved_at"],
                          last_check_status="failed" if check_failed else "changed", last_error=metadata.get("check_error") if check_failed else None)
            files = {f"references/{record['id']}/{original_file}": payload} if original_file else {}
            self._transaction(self._save_changes(record, files))
            return {"id": record["id"], "duplicate": False, "changed": bool(same), "snapshot_id": snapshot_id}

    def _snapshot(self, record, snapshot_id=None):
        snapshot_id = snapshot_id or record["current_snapshot_id"]
        if not isinstance(snapshot_id, str) or not SNAPSHOT_ID.fullmatch(snapshot_id):
            raise ValueError("快照编号无效")
        snapshot = next((row for row in record["snapshots"] if row["id"] == snapshot_id), None)
        if snapshot is None:
            raise KeyError("找不到该快照")
        return snapshot

    def _raw(self, record, snapshot):
        if not snapshot["original_file"]:
            return None
        payload = self._path(f"references/{record['id']}/{snapshot['original_file']}").read_bytes()
        if _digest(payload) != snapshot["sha256"]:
            raise ValueError("原文校验失败，请检查文件是否被外部修改")
        return payload

    def _analysis(self, record, snapshot):
        versions = [row for row in record["analyses"] if row["snapshot_id"] == snapshot["id"]]
        if not versions:
            return None
        version = versions[-1]
        payload = self._path(f"references/{record['id']}/{version['file']}").read_bytes()
        if _digest(payload) != version["sha256"]:
            raise ValueError("分析版本校验失败")
        return json.loads(payload)

    def _detail(self, record, snapshot_id=None):
        snapshot = self._snapshot(record, snapshot_id)
        raw = self._raw(record, snapshot)
        original = raw.decode("utf-8-sig") if raw is not None else None
        analysis = self._analysis(record, snapshot)
        previous_index = record["snapshots"].index(snapshot) - 1
        previous = record["snapshots"][previous_index] if previous_index >= 0 else None
        old_raw = self._raw(record, previous) if previous else None
        difference = ""
        if old_raw is not None and raw is not None:
            difference = "\n".join(difflib.unified_diff(old_raw.decode("utf-8-sig").splitlines(), original.splitlines(), fromfile=previous["id"], tofile=snapshot["id"], lineterm=""))
        return {
            "item": self._item(record), "snapshot": deepcopy(snapshot), "original": original, "analysis": analysis,
            "snapshots": [{**row, "analysis_status": "ready" if any(a["snapshot_id"] == row["id"] for a in record["analyses"]) else "pending"} for row in record["snapshots"]],
            "diff": {"text": difference, "from_snapshot": previous["id"] if previous else None, "to_snapshot": snapshot["id"],
                     "impact": (analysis or {}).get("change_impact") or ("本快照尚待分析，不能推断行为影响" if previous else "首份快照"), "analysis_status": "ready" if analysis else "pending"},
            "template": (analysis or {}).get("template", ""), "loop": (analysis or {}).get("loop"),
        }

    def detail(self, ref_id, snapshot_id=None):
        with self._locked():
            return self._detail(self._record(ref_id), snapshot_id)

    def set_analysis(self, ref_id, snapshot_id, analysis):
        if not isinstance(analysis, dict):
            raise ValueError("拆解必须是结构化对象")
        required = ("use_cases", "not_for", "structure", "key_sentences", "design_reasoning", "template", "example", "counterexample", "loop", "quality_review", "maturity", "fit", "evidence")
        missing = [key for key in required if key not in analysis]
        if missing or not isinstance(analysis.get("template"), str) or not analysis["template"].strip():
            raise ValueError("拆解缺少必要字段或可迁移模板：" + ", ".join(missing))
        for field in ("structure", "key_sentences"):
            if not isinstance(analysis[field], list) or not all(isinstance(row, dict) for row in analysis[field]):
                raise ValueError(f"{field} 必须是结构化列表")
        for field in ("design_reasoning", "example", "counterexample", "loop", "quality_review", "maturity", "fit", "evidence"):
            if not isinstance(analysis[field], dict):
                raise ValueError(f"{field} 必须是结构化对象")
        for field in ("example", "counterexample"):
            if analysis[field].get("status") != "illustrative":
                raise ValueError("改写示例与反例须明确标为 illustrative，不能冒充实测")
        with self._locked():
            record = self._record(ref_id)
            snapshot = self._snapshot(record, snapshot_id)
            if analysis.get("snapshot_id") not in (None, snapshot_id):
                raise ValueError("拆解绑定的快照不匹配")
            current = self._analysis(record, snapshot)
            content = deepcopy(analysis)
            for key in ("version", "created_at", "snapshot_id", "evaluation_status"):
                content.pop(key, None)
            content["evaluation_status"] = "untested"
            content.setdefault("author", "当前 Codex 对话助手")
            if current:
                previous = {key: value for key, value in current.items() if key not in {"version", "created_at", "snapshot_id"}}
                if previous == content:
                    return self._detail(record, snapshot_id)
            number = len(record["analyses"]) + 1
            version = f"a{number:03d}"
            content.update(version=version, snapshot_id=snapshot_id, created_at=_now())
            payload = _json_bytes(content)
            filename = f"analyses/{version}.json"
            record["analyses"].append({"version": version, "snapshot_id": snapshot_id, "file": filename, "sha256": _digest(payload), "created_at": content["created_at"]})
            if record["current_snapshot_id"] == snapshot_id:
                record["analysis_status"] = "ready"
            record["updated_at"] = _now()
            self._transaction(self._save_changes(record, {f"references/{ref_id}/{filename}": payload}))
            return self._detail(record, snapshot_id)

    def set_flags(self, ref_id, favorite=None, followed=None):
        for value in (favorite, followed):
            if value is not None and type(value) is not bool:
                raise ValueError("收藏和关注状态必须是布尔值")
        with self._locked():
            record = self._record(ref_id)
            if favorite is not None:
                record["favorite"] = favorite
            if followed is not None:
                record["followed"] = followed
            record["updated_at"] = _now()
            self._transaction(self._save_changes(record))
            return self._item(record)

    def record_check(self, ref_id, status, checked_at, error=None):
        if status not in {"unchanged", "changed", "failed"}:
            raise ValueError("检查状态无效")
        with self._locked():
            record = self._record(ref_id)
            record.update(last_attempt=checked_at, last_check_status=status, last_error=str(error) if error else None)
            if status != "failed":
                record["last_success"] = checked_at
                record["last_error"] = None
            self._transaction(self._save_changes(record))
            return self._item(record)

    def _personal_index(self):
        return _read_json(self.root / "index.json", {"schema_version": 1, "entry_count": 0, "entries": []})

    def _personal(self, entry_id):
        if not isinstance(entry_id, str) or not ENTRY_ID.fullmatch(entry_id):
            raise KeyError("素材编号无效")
        row = next((item for item in self._personal_index()["entries"] if item["id"] == entry_id), None)
        if not row:
            raise KeyError("目标素材不存在")
        record = _read_json(self._path(row["record_file"]))
        if not isinstance(record, dict):
            raise ValueError("目标素材记录缺失或损坏，请先修复索引")
        return row, record

    def _preview(self, record, target_id=None):
        snapshot = self._snapshot(record)
        analysis = self._analysis(record, snapshot)
        existing = next((row for row in self._personal_index()["entries"] if row.get("original_sha256") == snapshot["sha256"]), None)
        target_id = target_id or (existing["id"] if existing else None)
        if target_id:
            self._personal(target_id)
        allowed = record["source"]["license_status"] == "allowed" and snapshot["license_status"] == "allowed"
        can_adopt = allowed and analysis is not None and bool(analysis.get("template", "").strip())
        reason = "" if can_adopt else ("许可尚未明确允许采用原文" if not allowed else "此快照待分析，完成拆解和模板后才能采用")
        raw = self._raw(record, snapshot)
        return {
            "reference_id": record["id"], "snapshot_id": snapshot["id"], "analysis_version": (analysis or {}).get("version"),
            "title": record["title"], "category_id": record["category_id"], "original": raw.decode("utf-8-sig") if raw is not None else None,
            "template": (analysis or {}).get("template", ""), "license": record["source"]["license"], "license_status": record["source"]["license_status"],
            "source": snapshot["source"], "target_id": target_id, "existing_entry_id": existing["id"] if existing else None,
            "can_adopt": can_adopt, "reason": reason, "action": "new_version" if target_id else "new_entry",
        }

    def adoption_preview(self, ref_id, target_id=None):
        with self._locked():
            return self._preview(self._record(ref_id), target_id)

    @staticmethod
    def _analysis_markdown(analysis):
        def prose(value):
            if isinstance(value, str):
                return value
            if isinstance(value, list):
                return "\n".join("- " + prose(row) for row in value)
            if isinstance(value, dict):
                return "；".join(f"{key}：{prose(content)}" for key, content in value.items())
            return str(value) if value is not None else "未提供"

        lines = ["# 写法拆解", "", "## 适用场景", "", prose(analysis["use_cases"]), "", "不适用：" + prose(analysis["not_for"]), "", "## 结构地图", ""]
        for row in analysis["structure"]:
            lines.extend([f"- **{row.get('part', '结构')}**：{prose(row.get('observation'))}；依据：{prose(row.get('evidence'))}"])
        lines.extend(["", "## 关键句的作用", ""])
        for row in analysis["key_sentences"]:
            lines.extend(["> " + prose(row.get("quote")).replace("\n", "\n> "), "", "位置：" + prose(row.get("location")), "", "作用：" + prose(row.get("reason")), "", "删除后的风险：" + prose(row.get("without")), ""])
        reasoning = analysis["design_reasoning"]
        lines.extend(["## 设计依据", "", "作者公开说明：" + prose(reasoning.get("author_stated")), "", "整理者推断：" + prose(reasoning.get("inferred")), "", "证据边界：" + prose(reasoning.get("evidence")), "", "## 可迁移模板", "", analysis["template"], "", "## 改写示例（示意，未实测）", ""])
        example = analysis["example"]
        lines.extend(["任务：" + prose(example.get("task")), "", prose(example.get("prompt")), "", "改写理由：" + prose(example.get("changes")), "", "## 对照与反例（预期，未实测）", ""])
        counter = analysis["counterexample"]
        lines.extend(["改前：" + prose(counter.get("before")), "", "改后：" + prose(counter.get("after")), "", "只改变：" + prose(counter.get("changed_variable")), "", "预期作用：" + prose(counter.get("expected_effect")), "", "## Loop", "", prose(analysis["loop"].get("text")), "", "## 质量审查", ""])
        names = {"goal_clarity": "目标清楚", "input_clarity": "输入明确", "constraint_quality": "约束合理", "output_checkability": "输出可检查", "usage_evidence": "使用证据", "task_fit": "任务匹配"}
        lines.extend(f"- {names.get(key, key)}：{prose(value)}" for key, value in analysis["quality_review"].items())
        lines.extend(["", "实际效果：untested。示例和反例为说明性材料。", ""])
        return "\n".join(lines)

    def _markdown_index(self, index):
        names = {row["id"]: row["name"] for row in _read_json(self.root / "taxonomy.json", {"categories": []})["categories"]}
        escape = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
        lines = ["# 提示词目录", "", f"实际素材：**{len(index['entries'])} 条**。", "", "每条保留原文与独立优化版本。实际效果依据真实任务证据记录。", "", "| 编号 | 标题 | 分类 | 标签 | 最新优化版 | 效果状态 |", "| --- | --- | --- | --- | --- | --- |"]
        for row in index["entries"]:
            lines.append(f"| [{row['id']} 原文]({row['original_file']}) | {escape(row['title'])} | {escape(names.get(row['category_id'], row['category_id']))} | {escape('、'.join(row.get('tags', [])))} | [{row.get('latest_version', 'v001')}]({row['optimized_file']}) | {'待验证' if row.get('evaluation_status') == 'untested' else escape(row.get('evaluation_status', '待验证'))} |")
        lines.extend(["", "[参考库](references/README.md) · [返回使用说明](README.md)", ""])
        return "\n".join(lines).encode("utf-8")

    def adopt(self, ref_id, target_id=None, expected_snapshot=None, expected_analysis_version=None):
        if not expected_snapshot or not expected_analysis_version:
            raise ValueError("请先预览，并提交快照及拆解版本后再采用")
        with self._locked():
            record = self._record(ref_id)
            preview = self._preview(record, target_id)
            if preview["snapshot_id"] != expected_snapshot or preview["analysis_version"] != expected_analysis_version:
                raise ValueError("参考已更新，请重新预览后采用")
            if not preview["can_adopt"]:
                raise ValueError(preview["reason"])
            target_id = preview["target_id"]
            analysis = self._analysis(record, self._snapshot(record))
            template = analysis["template"]
            template_sha = _digest(template.encode("utf-8"))
            if target_id:
                existing_row, personal = self._personal(target_id)
                for version in personal.get("versions", []):
                    provenance = version.get("reference_provenance", {})
                    if provenance.get("reference_id") == ref_id and provenance.get("snapshot_id") == expected_snapshot and provenance.get("analysis_version") == expected_analysis_version:
                        return {"entry_id": target_id, "version": version["version"], "duplicate": True, "reference_id": ref_id}
                    if version.get("template_sha256") == template_sha:
                        return {"entry_id": target_id, "version": version["version"], "duplicate": True, "reference_id": ref_id, "reason": "该模板版本已存在"}
            timestamp = _now()
            index = self._personal_index()
            files = {}
            if not target_id:
                used = [int(row["id"].split("-")[1]) for row in index["entries"]]
                used.extend(int(path.name.split("-")[1]) for path in (self.root / "entries").glob("PRM-*") if ENTRY_ID.fullmatch(path.name))
                target_id = f"PRM-{max(used + [0]) + 1:04d}"
                folder = f"entries/{target_id}"
                raw = self._raw(record, self._snapshot(record))
                files[f"{folder}/original.md"] = raw
                personal = {
                    "schema_version": 1, "id": target_id, "title": record["title"], "summary": record["summary"], "category_id": record["category_id"],
                    "classification_status": "classified", "tags": record["tags"], "source": {"type": "reference_adoption", **preview["source"], "provenance_file": "SOURCE.md"},
                    "created_at": timestamp, "original": {"file": "original.md", "sha256": _digest(raw), "byte_count": len(raw), "encoding": "UTF-8"},
                    "related_ids": record.get("related_ids", []), "variables": [], "applicable_models": [], "open_questions": [], "versions": [], "feedback": [], "review_history": [],
                }
                existing_row = {"id": target_id, "title": record["title"], "summary": record["summary"], "category_id": record["category_id"], "tags": record["tags"],
                                "record_file": f"{folder}/record.json", "original_file": f"{folder}/original.md", "original_sha256": _digest(raw), "created_at": timestamp}
                index["entries"].append(existing_row)
            else:
                folder = str(PurePosixPath(existing_row["record_file"]).parent)
            number = max([int(v["version"][1:]) for v in personal.get("versions", []) if re.fullmatch(r"v\d+", v.get("version", ""))] + [0]) + 1
            while self._path(f"{folder}/optimized-v{number:03d}.md").exists():
                number += 1
            version_id = f"v{number:03d}"
            prior_version = next((row for row in personal.get("versions", []) if row.get("version") == existing_row.get("latest_version")), None)
            if prior_version:
                if personal.get("design_analysis_file"):
                    prior_version.setdefault("analysis_file", personal["design_analysis_file"])
                if personal.get("source", {}).get("provenance_file"):
                    prior_version.setdefault("source_file", personal["source"]["provenance_file"])
                previous_loop = personal.get("loop_review", {})
                if previous_loop.get("reviewed_version") == prior_version["version"]:
                    prior_version.setdefault("loop_review", deepcopy(previous_loop))
            new_loop = {"reviewed_version": version_id, "reviewed_at": timestamp, "applicability": analysis["loop"].get("applicability"),
                        "max_rounds": analysis["loop"].get("max_rounds"), "copyable_loop": analysis["loop"].get("text", ""),
                        "reminder": analysis["loop"].get("text", ""), "effectiveness_verified": False}
            provenance = {"reference_id": ref_id, "snapshot_id": expected_snapshot, "analysis_version": expected_analysis_version,
                          "source_commit": preview["source"]["commit"], "source_url": preview["source"]["url"], "source_sha256": self._snapshot(record)["sha256"]}
            optimized = template.encode("utf-8")
            analysis_file = f"reference-analysis-{version_id}.md"
            source_file = f"reference-source-{version_id}.md"
            files[f"{folder}/optimized-{version_id}.md"] = optimized
            files[f"{folder}/{analysis_file}"] = self._analysis_markdown(analysis).encode("utf-8")
            source_text = "# 来源与采用记录\n\n" + json.dumps({**provenance, "license": preview["license"], "source": preview["source"], "adopted_at": timestamp}, ensure_ascii=False, indent=2) + "\n\n本版本是基于参考拆解的改编；实际效果尚未验证。\n"
            files[f"{folder}/{source_file}"] = source_text.encode("utf-8")
            if not personal["versions"]:
                files[f"{folder}/SOURCE.md"] = source_text.encode("utf-8")
                if preview["source"].get("license_text"):
                    files[f"{folder}/LICENSE.txt"] = preview["source"]["license_text"].encode("utf-8")
            personal.setdefault("versions", []).append({"version": version_id, "file": f"optimized-{version_id}.md", "created_at": timestamp,
                "created_by": "用户确认采用参考模板", "based_on": f"{ref_id}/{expected_snapshot}/{expected_analysis_version}", "reason": "预览后明确采用参考版本", "changes": ["从绑定原文快照的拆解模板采用，保留原文及历史版本"],
                "evaluation_status": "untested", "sha256": _digest(optimized), "template_sha256": template_sha, "reference_provenance": provenance,
                "analysis_file": analysis_file, "source_file": source_file, "loop_review": deepcopy(new_loop)})
            personal.update(updated_at=timestamp, design_analysis_file=analysis_file,
                            quality_review={"reviewed_version": version_id, "reviewed_at": timestamp, "review_basis": "curated_reference_analysis", "criteria": analysis["quality_review"]},
                            loop_review=new_loop)
            files[f"{folder}/record.json"] = _json_bytes(personal)
            existing_row.update(latest_version=version_id, optimized_file=f"{folder}/optimized-{version_id}.md", analysis_file=f"{folder}/{analysis_file}", source_file=f"{folder}/{source_file}", evaluation_status="untested", updated_at=timestamp)
            index["entries"] = [existing_row if row["id"] == target_id else row for row in index["entries"]]
            index.update(entry_count=len(index["entries"]), updated_at=timestamp)
            record.setdefault("adoptions", []).append({**provenance, "entry_id": target_id, "version": version_id, "created_at": timestamp})
            record["related_ids"] = sorted(set(record.get("related_ids", [])) | {target_id})
            files = self._save_changes(record, files)
            files["INDEX.md"] = self._markdown_index(index)
            readme_path = self.root / "README.md"
            if readme_path.exists():
                readme = readme_path.read_text(encoding="utf-8-sig")
                count = str(len(index["entries"]))
                readme = re.sub(r"(已收录实际提示词\s*)\d+(\s*条)", lambda m: m[1] + count + m[2], readme)
                readme = re.sub(r"(当前已有\s*)\d+(\s*条素材)", lambda m: m[1] + count + m[2], readme)
                readme = re.sub(r"(当前状态[：:]\s*)\d+(\s*条个人素材)", lambda m: m[1] + count + m[2], readme)
                files["README.md"] = readme.encode("utf-8")
            files["index.json"] = _json_bytes(index)
            self._transaction(files)
            return {"entry_id": target_id, "version": version_id, "duplicate": False, "reference_id": ref_id, "snapshot_id": expected_snapshot, "analysis_version": expected_analysis_version}

    def recommendations(self, entry_id, limit=3):
        if type(limit) is not int or limit < 1:
            raise ValueError("推荐数量必须是正整数")
        with self._locked():
            entry, _ = self._personal(entry_id)
            ranked = []
            for row in self._index()["references"]:
                if row["selection_status"] == "rejected":
                    continue
                linked = entry_id in row.get("related_ids", [])
                common = sorted(set(entry.get("tags", [])) & set(row.get("tags", [])))
                same_category = entry["category_id"] == row["category_id"]
                if not (linked or common or same_category):
                    continue
                reasons = (["已有关联素材记录"] if linked else []) + (["同属当前任务分类"] if same_category else []) + (["共同标签：" + "、".join(common)] if common else [])
                ranked.append((int(linked) * 100 + len(common) * 10 + int(same_category), {**row, "reason": "；".join(reasons), "match_basis": "category_tags_and_explicit_links", "difference": row.get("summary", ""), "borrowable_module": "查看该参考写法拆解卡" if row["analysis_status"] == "ready" else "尚待分析，不能保证可迁移效果"}))
            ranked.sort(key=lambda value: (-value[0], value[1]["id"]))
            return [item for _, item in ranked[:min(limit, 3)]]
