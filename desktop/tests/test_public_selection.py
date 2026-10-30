"""验证公开导出默认拒绝、固定选择和只读发布校验边界。"""

from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.export_collection import export
from prompt_store import PromptStore


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(data):
    return sha256(data).hexdigest()


def refresh_manifest(root, name="manifest.json"):
    manifest = json.loads((root / name).read_text(encoding="utf-8")) if (root / name).exists() else {}
    manifest["files"] = [{"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": digest(path.read_bytes())}
                         for path in sorted(root.rglob("*")) if path.is_file() and path != root / name]
    write_json(root / name, manifest)


@pytest.fixture
def material_source(tmp_path):
    source = tmp_path / "source"
    rows = []
    for number in [1, 2]:
        entry = f"PRM-{number:04}"
        folder = source / "entries" / entry
        folder.mkdir(parents=True)
        original = f"已授权的教学素材{number}\r\n".encode("utf-8")
        optimized = f"明确输入与输出{number}\r\n".encode("utf-8")
        (folder / "original.md").write_bytes(original)
        (folder / "optimized-v001.md").write_bytes(optimized)
        write_json(folder / "record.json", {"id": entry, "title": f"教材{number}", "source": {},
            "related_ids": ["PRM-0002"] if number == 1 else [],
            "original": {"file": "original.md", "sha256": digest(original), "byte_count": len(original)},
            "versions": [{"version": "v001", "file": "optimized-v001.md", "sha256": digest(optimized), "evaluation_status": "untested"}]})
        rows.append({"id": entry, "title": f"教材{number}", "category_id": "learning", "tags": [],
            "record_file": f"entries/{entry}/record.json", "original_file": f"entries/{entry}/original.md",
            "original_sha256": digest(original), "optimized_file": f"entries/{entry}/optimized-v001.md",
            "latest_version": "v001", "evaluation_status": "untested"})
    write_json(source / "index.json", {"schema_version": 1, "entry_count": 2, "entries": rows})
    write_json(source / "taxonomy.json", {"categories": [{"id": "learning", "name": "学习"}]})
    (source / "references").mkdir()
    return source


def test_export_rejects_implicit_full_library_without_creating_output(material_source, tmp_path):
    output = tmp_path / "public"
    with pytest.raises(ValueError, match="显式"):
        export(material_source, output)
    assert not output.exists()


def test_export_only_writes_selected_ids_and_prunes_relations(material_source, tmp_path):
    output = tmp_path / "public"
    export(material_source, output, entry_ids=["PRM-0001"], reference_ids=[])
    index = json.loads((output / "index.json").read_text(encoding="utf-8"))
    assert index["entry_count"] == 1
    assert [item["id"] for item in index["entries"]] == ["PRM-0001"]
    assert not (output / "entries/PRM-0002").exists()
    assert json.loads((output / "entries/PRM-0001/record.json").read_text(encoding="utf-8"))["related_ids"] == []


@pytest.mark.parametrize("default_name", [None, "个人待归档"])
def test_exported_collection_can_save_without_category(material_source, tmp_path, default_name):
    taxonomy_path = material_source / "taxonomy.json"
    if default_name:
        taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
        taxonomy["categories"].append({"id": "uncategorized", "name": default_name})
        write_json(taxonomy_path, taxonomy)
    source_before = taxonomy_path.read_bytes()
    output = tmp_path / "public"
    export(material_source, output, entry_ids=["PRM-0001"], reference_ids=[])
    saved = PromptStore(output).save_prompt({"title": "安装后新素材", "original": "直接保存，未选择分类"})
    assert saved["item"]["category_id"] == "uncategorized"
    assert taxonomy_path.read_bytes() == source_before
    if default_name:
        categories = json.loads((output / "taxonomy.json").read_text(encoding="utf-8"))["categories"]
        assert next(item for item in categories if item["id"] == "uncategorized")["name"] == default_name


@pytest.mark.parametrize("entry_ids,reference_ids", [(["PRM-9999"], []), (["../escape"], []), (["PRM-0001", "PRM-0001"], []), (["PRM-0001"], ["REF-9999"]), (None, []), (["PRM-0001"], None)])
def test_export_rejects_unknown_invalid_or_duplicate_selection(material_source, tmp_path, entry_ids, reference_ids):
    output = tmp_path / "public"
    with pytest.raises(ValueError):
        export(material_source, output, entry_ids=entry_ids, reference_ids=reference_ids)
    assert not output.exists()


@pytest.fixture
def public_fixture(material_source, tmp_path):
    bundle = tmp_path / "candidate" / "bundled-library"
    export(material_source, bundle, entry_ids=["PRM-0001"], reference_ids=[])
    learning = bundle.parent / "learning-library"
    card = learning / "cards/PRM-0001/v002.md"
    card.parent.mkdir(parents=True)
    card.write_text("# 输入与输出的教学\n", encoding="utf-8")
    original = (bundle / "entries/PRM-0001/original.md").read_bytes().decode("utf-8-sig")
    optimized = (bundle / "entries/PRM-0001/optimized-v001.md").read_bytes().decode("utf-8-sig")
    write_json(learning / "manifest.json", {"schema_version": 1, "revision": "v002", "entries": {"PRM-0001": {
        "file": "cards/PRM-0001/v002.md", "revision": "v002", "sha256": digest(card.read_bytes()),
        "bindings": [{"version": "v001", "original_sha256": digest(original.encode()), "optimized_sha256": digest(optimized.encode())}]}}})
    refresh_manifest(learning, "checksums.json")
    selection = bundle.parent / "public-selection.json"
    write_json(selection, {"schema_version": 1, "entry_ids": ["PRM-0001"], "reference_ids": []})
    return bundle, learning, selection


def validator():
    module = importlib.import_module("tools.validate_public_collection")
    return module.validate


def test_validator_accepts_matching_files_and_is_read_only(public_fixture):
    bundle, learning, selection = public_fixture
    before = {str(p): p.read_bytes() for p in bundle.parent.rglob("*") if p.is_file()}
    result = validator()(bundle, learning, selection)
    assert result["status"] == "pass", result
    assert result["counts"]["entries"] == 1 and result["counts"]["teaching_ready"] == 1
    assert before == {str(p): p.read_bytes() for p in bundle.parent.rglob("*") if p.is_file()}


@pytest.mark.parametrize("fault", ["extra_entry", "hash", "binding", "brand", "escaped_brand", "loose_file", "old_card", "record_version", "default_missing", "default_invalid", "default_duplicate"])
def test_validator_rejects_material_outside_selection_or_integrity_failure(public_fixture, fault):
    bundle, learning, selection = public_fixture
    if fault == "extra_entry":
        path = bundle / "entries/PRM-0002/original.md"
        path.parent.mkdir(parents=True)
        path.write_text("未经选择", encoding="utf-8")
        refresh_manifest(bundle)
    elif fault == "hash":
        (bundle / "entries/PRM-0001/original.md").write_text("已被更换", encoding="utf-8")
    elif fault == "binding":
        path = learning / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["entries"]["PRM-0001"]["bindings"][0]["optimized_sha256"] = "0" * 64
        write_json(path, manifest)
        refresh_manifest(learning, "checksums.json")
    elif fault == "brand":
        forbidden = "".join(chr(code) for code in [0x95EA, 0x52BF, 0x79D1, 0x6280])
        (bundle / "README.md").write_text(forbidden, encoding="utf-8")
        refresh_manifest(bundle)
    elif fault == "old_card":
        (learning / "cards/PRM-0001/v001.md").write_text("未登记的旧教学", encoding="utf-8")
        refresh_manifest(learning, "checksums.json")
    elif fault == "escaped_brand":
        path = bundle / "entries/PRM-0001/record.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["note"] = "".join(chr(code) for code in [0x95EA, 0x52BF])
        path.write_text(json.dumps(record, ensure_ascii=True), encoding="utf-8")
        refresh_manifest(bundle)
    elif fault == "loose_file":
        (bundle / "entries/unselected.md").write_text("未登记目录下的资料", encoding="utf-8")
        refresh_manifest(bundle)
    elif fault.startswith("default_"):
        path = bundle / "taxonomy.json"
        taxonomy = json.loads(path.read_text(encoding="utf-8"))
        taxonomy["categories"] = [item for item in taxonomy["categories"] if item["id"] != "uncategorized"]
        if fault == "default_invalid":
            taxonomy["categories"].append({"id": "uncategorized", "name": " "})
        elif fault == "default_duplicate":
            taxonomy["categories"].extend([{"id": "uncategorized", "name": "未分类"}, {"id": "uncategorized", "name": "待归档"}])
        write_json(path, taxonomy)
        refresh_manifest(bundle)
    else:
        path = bundle / "entries/PRM-0001/record.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["versions"][0]["sha256"] = "0" * 64
        write_json(path, record)
        refresh_manifest(bundle)
    result = validator()(bundle, learning, selection)
    assert result["status"] == "fail", result
    assert result["errors"]
