"""按显式发布规则生成公开素材副本；不修改私人库，不导出运行配置。"""
import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "desktop"))
from library_init import DEFAULT_TAXONOMY, render_index, validate_taxonomy


DROP_KEYS = {"thread_id", "message_selector", "source_path", "local_path", "last_attempt", "last_success", "last_check_status", "last_error", "seed_provenance_file"}
SECRET = re.compile(r"sk-[A-Za-z0-9_-]{28,}|gh[pousr]_[A-Za-z0-9]{28,}|Bearer [A-Za-z0-9._-]{24,}")
LOCAL_PATH = re.compile(r"[A-Z]:[\\/]+Users[\\/]+[^\s\n\"<>）)]+", re.I)
THREAD = re.compile(r"01a[0-9a-f]{5}-[0-9a-f-]{27,}")


def clean_text(text):
    if SECRET.search(text):
        raise ValueError("发现疑似访问凭据，停止公开导出；请人工核对，未输出具体值")
    text = re.sub(r"http://(?:localhost|127\.0\.0\.1):8767/download/(PRM-\d+)/(?:original|optimized)", r"https://github.com/Shanvision-star/liubai-prompt-library/blob/main/bundled-library/entries/\1/original.md", text)
    return THREAD.sub("[会话标识已移除]", LOCAL_PATH.sub("[本机路径已移除]", text))


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k not in DROP_KEYS}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return clean_text(value) if isinstance(value, str) else value


def section(text, heading):
    matched = re.search(r"^## " + re.escape(heading) + r"\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return matched.group(1).strip() if matched else ""


def selection_ids(entry_ids, reference_ids):
    """必须同时给出两份清单；空参考列表也是显式选择。"""
    if entry_ids is None or reference_ids is None:
        raise ValueError("公开导出必须显式提供 entry_ids 和 reference_ids，禁止默认全库导出")
    selected = []
    for values, prefix in [(entry_ids, "PRM"), (reference_ids, "REF")]:
        if (not isinstance(values, list)
                or any(not isinstance(value, str) or not re.fullmatch(prefix + r"-\d{4}", value) for value in values)
                or len(values) != len(set(values))):
            raise ValueError("公开选择清单必须是无重复的有效编号列表")
        selected.append(set(values))
    if not any(selected):
        raise ValueError("公开选择清单不能全部为空")
    return selected


def load_selection(path):
    """读取 schema_version=1、entry_ids、reference_ids 的发布选择文件。"""
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("公开选择文件需要 schema_version=1")
    selection_ids(data.get("entry_ids"), data.get("reference_ids"))
    return data


def selected_relations(value, allowed):
    if isinstance(value, dict):
        return {key: [item for item in item_value if item in allowed] if key == "related_ids"
                else selected_relations(item_value, allowed)
                for key, item_value in value.items()
                if key != "linked_prompt" or item_value in allowed}
    if isinstance(value, list):
        return [selected_relations(item, allowed) for item in value]
    return value


def export(source, output, *, entry_ids=None, reference_ids=None):
    selected_entries, selected_refs = selection_ids(entry_ids, reference_ids)
    allowed = selected_entries | selected_refs
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("输出目录已存在；请使用新的目录，不能覆盖既有发布副本")
    files = {}
    published_at = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    index = clean(json.loads((source / "index.json").read_text(encoding="utf-8-sig")))
    known_entries = {item["id"] for item in index["entries"]}
    known_refs = {folder.name for folder in (source / "references").glob("REF-*") if (folder / "record.json").is_file()}
    if selected_entries - known_entries or selected_refs - known_refs:
        raise ValueError("公开选择清单包含源库不存在的编号，未创建输出")
    index["entries"] = [selected_relations(item, allowed) for item in index["entries"] if item["id"] in selected_entries]
    index["entry_count"] = len(index["entries"])
    taxonomy = validate_taxonomy(json.loads((source / "taxonomy.json").read_text(encoding="utf-8-sig")))
    if not any(category["id"] == "uncategorized" for category in taxonomy["categories"]):
        # 默认保存依赖该分类；源库可裁剪分类，但公开包必须保留这条运行契约。
        defaults = validate_taxonomy(json.loads(DEFAULT_TAXONOMY.read_text(encoding="utf-8-sig")))
        default_category = next((category for category in defaults["categories"] if category["id"] == "uncategorized"), None)
        if default_category is None:
            raise ValueError("应用默认分类模板缺少 uncategorized，停止公开导出")
        taxonomy["categories"].append(deepcopy(default_category))
    def put(name, value):
        files[name] = value if isinstance(value, bytes) else value.encode("utf-8")
    def put_json(name, value):
        put(name, json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    transformed = []
    notices = []
    for item in index["entries"]:
        folder = source / "entries" / item["id"]
        record = selected_relations(clean(json.loads((folder / "record.json").read_text(encoding="utf-8-sig"))), allowed)
        record["feedback"] = []
        original = (folder / "original.md").read_bytes().decode("utf-8")
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.suffix in {".md", ".txt", ".json"}:
                put(f"entries/{item['id']}/{path.name}", clean_text(path.read_bytes().decode("utf-8")))
        url = record.get("source", {}).get("url") or ""
        if "prompt-motion.com" in url and section(original, "原创复用提示词（本次新写，非作者原文）"):
            reuse = section(original, "原创复用提示词（本次新写，非作者原文）")
            chinese = reuse.split("中文：", 1)[-1].strip()
            design = section(original, "设计思路拆解")
            sources = section(original, "来源、完整性及许可")
            attribution = "\n".join(line for line in sources.splitlines() if line.startswith("- @"))
            original = f"# {record['title']}\n\n本公开版为整理者的原创复用方案与设计拆解；非网站提示词原文或逐句翻译，效果未实测。\n\n## 设计思路拆解\n\n{design}\n\n## 原创复用提示词\n\n{chinese}\n\n## 来源与署名\n\n{attribution}\n\n上游许可未明确，原文及译文不在本公开版中；请到来源查看。\n"
            put(f"entries/{item['id']}/original.md", original)
            put(f"entries/{item['id']}/optimized-v001.md", original)
            prompt = chinese + "\n\n开始前确认：{{主体或项目}}、{{画幅}}、{{时长}}、{{可用素材及授权}}、{{制作工具}}。缺少关键输入时先询问，不编造素材或制作结果。\n\n先给出分镜与时间轴，再按已确认输入制作。检查下列设计要点，最多修正两轮；达到要求或没有新证据时停止，说明仍未解决的问题。\n\n" + design
            put(f"entries/{item['id']}/optimized-v002.md", prompt)
            put(f"entries/{item['id']}/ANALYSIS.md", "# 设计思路拆解\n\n" + design + "\n\n原：来源文本描述的事实；建议：整理者的分析与取舍。未测试实际成片效果。\n")
            for version in record["versions"]:
                version["sha256"] = sha256(original.encode()).hexdigest()
            record["versions"].append({"version": "v002", "file": "optimized-v002.md", "created_at": published_at, "reason": "公开版提取已有中文原创复用方案，补输入检查与有限修订；非来源全文翻译", "optimization_status": "provided", "public_template": True, "evaluation_status": "untested", "analysis_file": "ANALYSIS.md", "sha256": sha256(prompt.encode()).hexdigest()})
            record["design_analysis_file"] = "ANALYSIS.md"
            record["loop_review"] = {"reviewed_version": "v002", "applicability": "conditional", "max_rounds": 2, "reminder": "按本条设计要点检查；最多修正两轮，达标或没有新证据时停止，列出未解决项。", "effectiveness_verified": False}
            record["optimization_status"] = item["optimization_status"] = "provided"
            item["latest_version"] = "v002"
            item["optimized_file"] = f"entries/{item['id']}/optimized-v002.md"
            record["source"]["note"] = "公开版只含整理者的原创复用方案、分析和来源；未授权转载的上游原文和逐句译文不发布。"
            put(f"entries/{item['id']}/SOURCE.md", "# 来源与公开范围\n\n" + attribution + "\n\n" + record["source"]["note"])
            transformed.append(item["id"])
        elif "prompt-motion.com" in url:
            mapping = section(original, "全部234入口映射")
            original = "# Prompt Motion 来源入口索引\n\n本公开库提供187条中文原创复用方案与拆解，及本来源索引；不分发未获许可的上游提示词原文和逐句译文。来源按原站标注，未独立复核每个原帖，所有方案效果待实测。\n\n## 来源入口映射\n\n" + mapping
            for name in ("original.md", "optimized-v001.md"):
                put(f"entries/{item['id']}/{name}", original)
            record["source"]["note"] = "公开版来源索引；不含未获许可的来源提示词正文。"
            put(f"entries/{item['id']}/SOURCE.md", f"来源：{url}\n\n" + record["source"]["note"])
            transformed.append(item["id"])
        elif "yihui-dev/awesome-opus5-5-videos" in url and section(original, "中文翻译"):
            translated = section(original, "中文翻译")
            match = re.search(r"```(?:text)?\s*\n(.*?)\n```", translated, re.S)
            prompt = match.group(1).strip() if match else translated
            design = section(original, "制作思路（本次分析，非原文要求）")
            put(f"entries/{item['id']}/optimized-v002.md", prompt)
            put(f"entries/{item['id']}/ANALYSIS.md", "# 制作思路\n\n" + design)
            record["versions"].append({"version": "v002", "file": "optimized-v002.md", "created_at": published_at, "reason": "从已有汉化整理中提取中文提示词，拆解单独呈现；原文与许可证保留", "optimization_status": "provided", "public_template": True, "analysis_file": "ANALYSIS.md", "evaluation_status": "untested"})
            record["design_analysis_file"] = "ANALYSIS.md"
            record["optimization_status"] = item["optimization_status"] = "provided"
            item["latest_version"] = "v002"
            item["optimized_file"] = f"entries/{item['id']}/optimized-v002.md"
        # 公开副本的原文摘要必须指向实际公开字节，不继续沿用私人原文哈希。
        original_bytes = files[f"entries/{item['id']}/original.md"]
        record["original"]["sha256"] = sha256(original_bytes).hexdigest()
        record["original"]["byte_count"] = len(original_bytes)
        item["original_sha256"] = record["original"]["sha256"]
        for version in record.get("versions", []):
            version["sha256"] = sha256(files[f"entries/{item['id']}/{version['file']}"]).hexdigest()
        record["publication"] = {"authorized_by_owner": True, "edition": "public-2026-10-28", "private_original_preserved": True, "original_kind": "curation" if "prompt-motion.com" in url else "original"}
        put_json(f"entries/{item['id']}/record.json", record)
        notices.append({"id": item["id"], "url": url or None, "license": record.get("source", {}).get("license") or ("MIT; see SOURCE.md" if "yihui-dev/awesome-opus5-5-videos" in url else "original curation only; upstream rights retained" if "prompt-motion.com" in url else "owner-authorized contribution")})
    refs = []
    for folder in sorted((source / "references").glob("REF-*")):
        if not folder.is_dir() or folder.name not in selected_refs:
            continue
        record = selected_relations(clean(json.loads((folder / "record.json").read_text(encoding="utf-8-sig"))), allowed)
        if any(snap.get("license_status") != "allowed" for snap in record["snapshots"]):
            raise ValueError(f"{record['id']} 包含许可未核对快照，停止发布")
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                raw = path.read_bytes().decode("utf-8")
                cleaned = clean_text(raw)
                if path.name == "original.md" and raw != cleaned:
                    raise ValueError("参考原文需要脱敏，必须先人工核对哈希关系")
                put(path.relative_to(source).as_posix(), cleaned)
        record["followed"] = record["favorite"] = False
        record["adoptions"] = []
        put_json(f"references/{record['id']}/record.json", record)
        refs.append({k: v for k, v in record.items() if k not in {"snapshots", "analyses", "adoptions"}})
    put_json("index.json", index)
    put_json("taxonomy.json", taxonomy)
    put("INDEX.md", render_index(index, taxonomy))
    put_json("references/index.json", {"schema_version": 1, "references": refs})
    manifest = {"version": "2026.10.28", "entry_count": len(index["entries"]), "reference_count": len(refs), "adapted_entries": transformed, "notices": notices, "files": [{"path": name, "sha256": sha256(data).hexdigest()} for name, data in sorted(files.items())]}
    output.mkdir(parents=True)
    for name, data in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"entries": manifest["entry_count"], "references": len(refs), "adapted": len(transformed), "files": len(files)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True,
                        help="JSON: schema_version=1、entry_ids=[PRM编号]、reference_ids=[REF编号]；两份列表必须显式给出")
    args = parser.parse_args()
    chosen = load_selection(args.selection)
    export(args.source, args.output, entry_ids=chosen["entry_ids"], reference_ids=chosen["reference_ids"])
