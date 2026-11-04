"""验证翻译按当前原文绑定，损坏或越界时不显示错误的对应关系。"""

from hashlib import sha256

import pytest

from translation_store import reading_pair


@pytest.mark.parametrize("mutation,expected", [("source", "source_changed"), ("translation", "unavailable"), ("deleted", "unavailable")])
def test_changed_or_missing_file_hides_only_translation(tmp_path, mutation, expected):
    raw, translated = "Keep {{name}}.\r\nThen continue.", "保留 {{name}}。\r\n然后继续。"
    path = tmp_path / "translated.txt"
    path.write_bytes(translated.encode())
    original_sha = sha256(raw.encode()).hexdigest()
    record = {"translation": {"status": "ready", "source_sha256": original_sha,
                              "file": path.name, "sha256": sha256(translated.encode()).hexdigest()}}
    if mutation == "source":
        original_sha = sha256(b"new original").hexdigest()
    elif mutation == "translation":
        path.write_text("unrelated rewrite", encoding="utf-8")
    else:
        path.unlink()
    result = reading_pair(tmp_path, record, raw, original_sha)
    assert result["translation_status"] == expected
    assert result["translation"] == ""
    assert result["original"] == raw and result["copyable"]


def test_translation_cannot_read_parent_file(tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"unrelated private material")
    folder = tmp_path / "entry"
    folder.mkdir()
    result = reading_pair(folder, {"translation": {
        "status": "ready", "source_sha256": "source", "file": "../outside.txt",
        "sha256": sha256(outside.read_bytes()).hexdigest()}}, "Original", "source")
    assert result["translation_status"] == "unavailable" and result["translation"] == ""


def test_chinese_original_needs_no_fabricated_translation(tmp_path):
    record = {"translation": {"status": "already_chinese", "source_sha256": "source"}}
    result = reading_pair(tmp_path, record, "请检查 {{资料}}。", "source")
    assert result["translation_status"] == "already_chinese"
    assert result["translation"] == "" and result["copyable"]
    assert reading_pair(tmp_path, record, "New English source", "changed")["translation_status"] == "source_changed"


def test_english_translation_bound_to_source_and_legacy_chinese_retained(tmp_path):
    raw = '示例 {{name}}'
    source_hash = sha256(raw.encode()).hexdigest()
    en = 'Example {{name}}'
    (tmp_path / 'translation.en.md').write_text(en, encoding='utf-8')
    record = {'translations': {'en': {'status': 'ready', 'file': 'translation.en.md',
                'source_sha256': source_hash, 'sha256': sha256(en.encode()).hexdigest()}}}
    result = reading_pair(tmp_path, record, raw, source_hash, target_language='en')
    assert result['original'] == raw and result['translation'] == en
    assert result['translation_status'] == 'ready'
    assert reading_pair(tmp_path, record, raw, sha256(b'changed').hexdigest(), target_language='en')['translation'] == ''

def test_english_translation_notice_does_not_claim_chinese(tmp_path):
    original = '原文'
    result = reading_pair(tmp_path, {}, original, sha256(original.encode()).hexdigest(), target_language='en')
    assert 'English' in result['notice']
    assert result['translation'] == ''
