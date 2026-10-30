"""只读核验公开选择、文件清单、版本哈希与教学绑定，不修改素材或联网。"""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.export_collection import load_selection
from library_init import validate_taxonomy

IDENTIFIER = re.compile(r"(?:PRM|REF)-\d{4}")
FORBIDDEN = tuple("".join(chr(code) for code in codes) for codes in [
    (0x95EA, 0x52BF), (0x95EA, 0x52BF, 0x79D1, 0x6280),
])


def read_json(path):
    return json.loads(path.read_bytes().decode("utf-8-sig"))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def text_digest(path):
    return sha256(path.read_bytes().decode("utf-8-sig").encode("utf-8")).hexdigest()


def safe_file(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or Path(relative).is_absolute():
        raise ValueError("清单含无效文件路径")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"文件缺失或路径越界：{relative}")
    return path


def check_manifest(root, name, errors):
    manifest = read_json(root / name)
    expected = {}
    for row in manifest["files"]:
        relative = row["path"]
        if relative in expected:
            errors.append(f"{name} 重复登记：{relative}")
        path = safe_file(root, relative)
        expected[relative] = row["sha256"]
        if digest(path) != row["sha256"]:
            errors.append(f"文件 SHA-256 不匹配：{relative}")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p != root / name}
    if set(expected) != actual:
        errors.append(f"{name} 未完整覆盖目录文件")
    return manifest, len(actual)


def source_assets(value):
    result = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"license_file", "notice_file", "complete_source_file"} and isinstance(item, str) and item.startswith("references/assets/"):
                result.add(item)
            if key not in {"license_text", "notice_text"}:
                result |= source_assets(item)
    elif isinstance(value, list):
        for item in value:
            result |= source_assets(item)
    return result


def validate(collection, learning, selection):
    """返回结构化结果；选择文件固定本次允许的 ID，函数从不写入任何目录。"""
    collection, learning = Path(collection).resolve(), Path(learning).resolve()
    errors = []
    counts = {"entries": 0, "references": 0, "versions": 0, "teaching_ready": 0, "bundle_files": 0, "learning_files": 0}
    try:
        selected = load_selection(selection)
        entries, refs = set(selected["entry_ids"]), set(selected["reference_ids"])
        allowed = entries | refs
        manifest, counts["bundle_files"] = check_manifest(collection, "manifest.json", errors)
        _, counts["learning_files"] = check_manifest(learning, "checksums.json", errors)
        taxonomy = validate_taxonomy(read_json(collection / "taxonomy.json"))
        if not any(category["id"] == "uncategorized" for category in taxonomy["categories"]):
            errors.append("缺少默认 uncategorized 分类，新素材无法不选分类直接保存")
        index = read_json(collection / "index.json")
        reference_index = read_json(collection / "references/index.json")
        rows, reference_rows = index["entries"], reference_index["references"]
        counts["entries"], counts["references"] = len(rows), len(reference_rows)
        if len(rows) != len(entries) or {row["id"] for row in rows} != entries:
            errors.append("公开素材索引不等于固定选择清单")
        if len(reference_rows) != len(refs) or {row["id"] for row in reference_rows} != refs:
            errors.append("公开参考索引不等于固定选择清单")
        if index["entry_count"] != len(entries) or manifest["entry_count"] != len(entries) or manifest["reference_count"] != len(refs):
            errors.append("公开计数与固定选择不一致")
        entry_dirs = {p.name for p in (collection / "entries").iterdir() if p.is_dir()} if (collection / "entries").exists() else set()
        ref_dirs = {p.name for p in (collection / "references").iterdir() if p.is_dir() and p.name != "assets"}
        if entry_dirs != entries or ref_dirs != refs:
            errors.append("目录含未选择、缺失或无效编号的素材")
        teaching = read_json(learning / "manifest.json")
        if set(teaching["entries"]) != entries:
            errors.append("教学清单必须与公开素材选择完全一致")
        registered_cards = set()
        for item in rows:
            entry = item["id"]
            record_path = safe_file(collection, item["record_file"])
            base = record_path.parent
            if base != (collection / "entries" / entry).resolve():
                errors.append(f"索引记录路径与编号不同：{entry}")
            record = read_json(record_path)
            if record["id"] != entry:
                errors.append(f"索引与记录 ID 不同：{entry}")
            original = safe_file(base, record["original"]["file"])
            if original != safe_file(collection, item["original_file"]):
                errors.append(f"原文路径与记录不一致：{entry}")
            if digest(original) != record["original"]["sha256"] or digest(original) != item["original_sha256"]:
                errors.append(f"原文哈希不一致：{entry}")
            versions = record["versions"]
            if len({v["version"] for v in versions}) != len(versions):
                errors.append(f"保存版本编号重复：{entry}")
            for version in versions:
                counts["versions"] += 1
                if digest(safe_file(base, version["file"])) != version["sha256"]:
                    errors.append(f"保存版本哈希不一致：{entry}/{version['version']}")
            selected_versions = [v for v in versions if v["version"] == item["latest_version"]]
            optimized = safe_file(collection, item["optimized_file"])
            if len(selected_versions) != 1 or optimized != safe_file(base, selected_versions[0]["file"]):
                errors.append(f"索引最新版本与记录不一致：{entry}")
            card = teaching["entries"].get(entry)
            if not card:
                continue
            card_path = safe_file(learning, card["file"])
            registered_cards.add(card_path)
            if card_path != (learning / "cards" / entry / (card["revision"] + ".md")).resolve():
                errors.append(f"教学路径、编号或修订号不一致：{entry}")
            signature = {"version": item["latest_version"], "original_sha256": text_digest(original), "optimized_sha256": text_digest(optimized)}
            if digest(card_path) != card["sha256"] or signature not in card["bindings"]:
                errors.append(f"教学内容哈希或版本绑定不匹配：{entry}")
            else:
                counts["teaching_ready"] += 1
            for signature in card["bindings"]:
                matches = [v for v in versions if v["version"] == signature["version"]]
                if (len(matches) != 1 or signature["original_sha256"] != text_digest(original)
                        or signature["optimized_sha256"] != text_digest(safe_file(base, matches[0]["file"]))):
                    errors.append(f"教学包含不属于公开版本的额外绑定：{entry}")
        actual_cards = {p.resolve() for p in (learning / "cards").rglob("*") if p.is_file()}
        if actual_cards != registered_cards:
            errors.append("教学目录含未登记的旧卡或缺失的当前卡")
        needed_assets = set()
        for item in reference_rows:
            base = collection / "references" / item["id"]
            record = read_json(base / "record.json")
            if record["id"] != item["id"]:
                errors.append("参考目录、索引和记录编号不一致")
            for snapshot in record["snapshots"]:
                if snapshot.get("license_status") != "allowed":
                    errors.append(f"参考快照许可未核对：{item['id']}")
                if digest(safe_file(base, snapshot["original_file"])) != snapshot["sha256"]:
                    errors.append(f"参考快照哈希不一致：{item['id']}")
            for analysis in record["analyses"]:
                if digest(safe_file(base, analysis["file"])) != analysis["sha256"]:
                    errors.append(f"参考分析哈希不一致：{item['id']}")
            needed_assets |= source_assets(record) | source_assets(item)
        for relative in needed_assets:
            path = safe_file(collection, relative)
            if digest(path) != path.name.split(".")[0]:
                errors.append(f"来源附件文件名与哈希不一致：{relative}")
        actual_assets = {p.relative_to(collection).as_posix() for p in (collection / "references/assets").rglob("*") if p.is_file()}
        if actual_assets != needed_assets:
            errors.append("来源附件目录含未选中或缺失文件")
        for root in [collection, learning]:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                text = path.read_bytes().decode("utf-8-sig")
                if path.suffix == ".json":
                    text += json.dumps(json.loads(text), ensure_ascii=False)
                if any(word in text for word in FORBIDDEN):
                    errors.append(f"禁止品牌字符命中：{path.relative_to(root).as_posix()}")
                if any(value not in allowed for value in IDENTIFIER.findall(text)):
                    errors.append(f"残留未选中 ID：{path.relative_to(root).as_posix()}")
                relative = path.relative_to(root).as_posix()
                parts = path.relative_to(root).parts
                if root == collection:
                    known_path = (relative in {"index.json", "INDEX.md", "README.md", "manifest.json", "taxonomy.json", "references/index.json"}
                                  or len(parts) >= 3 and parts[0] == "entries" and parts[1] in entries
                                  or len(parts) >= 3 and parts[0] == "references" and parts[1] in refs
                                  or relative in needed_assets)
                else:
                    known_path = (relative in {"README.md", "learning-route.md", "manifest.json", "checksums.json", "methods.json", "editorial-notes.psv", "token-bucket-worked-example.md"}
                                  or path.resolve() in registered_cards)
                if not known_path:
                    errors.append(f"不属于公开素材的文件：{relative}")
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        errors.append(f"无法完成校验：{error}")
    return {"status": "fail" if errors else "pass", "counts": counts, "errors": errors,
            "scope": "只读内容核验；不证明模型效果、完整依赖或安装验收"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", type=Path, default=ROOT / "bundled-library")
    parser.add_argument("--learning", type=Path, default=ROOT / "learning-library")
    parser.add_argument("--selection", type=Path, default=ROOT / "public-selection.json",
                        help="schema_version=1、entry_ids 和 reference_ids 两份明确列表")
    args = parser.parse_args()
    report = validate(args.collection, args.learning, args.selection)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
