"""验证教学卡只附加到匹配版本，缺损或用户改写不会污染个人资料。"""

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from learning_store import teaching_card
from prompt_store import PromptStore
from server import Library


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture
def lesson(tmp_path):
    root = tmp_path / "learning"
    root.mkdir()
    body = "# 让形变说明关系\n\n旧内容先退，新内容再进。\n"
    (root / "lesson.md").write_bytes(body.encode("utf-8"))
    data = {"entries": {"PRM-0001": {"file": "lesson.md", "sha256": digest(body), "revision": "v001", "bindings": [{"version": "v002", "original_sha256": digest("原文\r\n"), "optimized_sha256": digest("改编\n")}]}}}
    (root / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
    return root, data, body


def test_matches_both_texts_and_version_without_writing_library(lesson):
    root, _, body = lesson
    before = {p: p.read_bytes() for p in root.iterdir()}
    result = teaching_card("PRM-0001", "v002", "原文\r\n", "改编\n", root)
    assert result == {"status": "ready", "markdown": body, "revision": "v001"}
    assert before == {p: p.read_bytes() for p in root.iterdir()}


@pytest.mark.parametrize("version,original,optimized", [
    ("v001", "原文\r\n", "改编\n"),
    ("v002", "改过的原文\r\n", "改编\n"),
    ("v002", "原文\r\n", "用户自己的改编\n"),
])
def test_changed_or_historical_content_does_not_inherit_lesson(lesson, version, original, optimized):
    root, _, _ = lesson
    assert teaching_card("PRM-0001", version, original, optimized, root) == {"status": "version_mismatch", "markdown": ""}


def test_new_entry_has_no_synthetic_analysis(lesson):
    root, _, _ = lesson
    assert teaching_card("PRM-9999", "v001", "新", "新", root)["status"] == "missing"


def test_library_uses_only_its_own_private_teaching_bundle(tmp_path, monkeypatch):
    def install_lesson(root, text):
        directory = root / "private-learning-library"
        directory.mkdir()
        (directory / "lesson.md").write_bytes(text.encode("utf-8"))
        manifest = {"entries": {"PRM-0001": {"file": "lesson.md", "sha256": digest(text), "revision": "private-v1", "bindings": [{"version": "v001", "original_sha256": digest("原文\r\n"), "optimized_sha256": digest("初版\n")}]}}}
        (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    root = tmp_path / "private-library"
    store = PromptStore(root)
    store.save_prompt({"title": "个人资料", "original": "原文\r\n", "optimized": "初版\n"})
    install_lesson(root, "个人库自带教学")
    fallback = tmp_path / "app-resources"
    fallback.mkdir()
    install_lesson(fallback, "程序目录中的其他私人教学不能串读")
    monkeypatch.setattr("learning_store.resource_root", lambda: fallback)
    detail = Library(root).entry("PRM-0001")
    assert detail["analysis"] == "个人库自带教学" and detail["analysis_origin"] == "private"
    other = PromptStore(tmp_path / "other-library")
    other.save_prompt({"title": "另一个资料库", "original": "原文\r\n", "optimized": "初版\n"})
    assert Library(other.root).entry("PRM-0001")["analysis"] == ""
    store.save_analysis("PRM-0001", {"version": "v001", "original_sha256": detail["original_sha256"], "optimized_sha256": detail["optimized_sha256"], "analysis_markdown": "用户新保存的版本拆解"})
    assert Library(root).entry("PRM-0001")["analysis"] == "用户新保存的版本拆解"


@pytest.mark.parametrize("failure", ["hash", "missing_file", "escape", "invalid_json", "invalid_schema"])
def test_bad_lesson_never_blocks_original_reading(lesson, failure):
    root, data, _ = lesson
    if failure == "hash":
        (root / "lesson.md").write_text("损坏", encoding="utf-8")
    elif failure == "missing_file":
        (root / "lesson.md").unlink()
    elif failure == "escape":
        data["entries"]["PRM-0001"]["file"] = "../outside.md"
        (root / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
    else:
        (root / "manifest.json").write_text("{" if failure == "invalid_json" else "[]", encoding="utf-8")
    assert teaching_card("PRM-0001", "v002", "原文\r\n", "改编\n", root)["status"] == "unavailable"


@pytest.fixture(scope="module")
def public_library(tmp_path_factory):
    root = Path(__file__).resolve().parents[2]
    temporary = tmp_path_factory.mktemp("learning-collection")
    copied = temporary / "library"
    shutil.copytree(root / "bundled-library", copied, ignore=shutil.ignore_patterns(".store.lock"))
    return Library(copied, temporary / "state")


def test_public_collection_has_real_cards_and_guide_links_resolve(public_library):
    root = Path(__file__).resolve().parents[2]
    library = public_library
    manifest = json.loads((root / "learning-library/manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["entries"]) == {item["id"] for item in library.index_entries()}
    for item in library.index_entries():
        entry = library.entry(item["id"])
        assert entry["teaching_status"] == "ready", item["id"]
        assert len(entry["analysis"]) > 1000
        assert "Loop" in entry["analysis"]
        assert "只改一个条件" in entry["analysis"]
        assert "参考思路" in entry["analysis"]
    guide = (root / "learning-library/learning-route.md").read_text(encoding="utf-8")
    import re
    for linked in re.findall(r"entry=(PRM-\d+)", guide):
        assert linked in manifest["entries"]
    assert "PRM-0218" in guide
    assert "t=0.5" in library.entry("PRM-0218")["analysis"]


def test_existing_historical_analysis_is_not_replaced(public_library):
    library = public_library
    current = library.entry("PRM-0218")
    old = library.entry("PRM-0218", "v001")
    assert current["teaching_status"] == "ready"
    assert old["teaching_status"] == "version_mismatch"
    assert old["analysis"] != current["analysis"]
