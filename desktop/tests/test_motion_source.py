"""核对来源原文完整性、双语正文校验与路径边界。"""
from hashlib import sha256
import pytest

from motion_source import source_prompt


def test_curation_never_claims_to_be_original(tmp_path):
    result = source_prompt(tmp_path, {"source":{"url":"https://prompt-motion.com/example"}})
    assert result["status"] == "missing"
    assert result["original"] == "" and not result["copyable"]


def test_complete_user_supplied_source_is_exact_and_bound_to_translation(tmp_path):
    raw = "Make a blue circle.\nThen fade it out."
    translated = "画一个蓝色圆形。\n然后让它淡出。"
    (tmp_path/'SOURCE-PROMPT.txt').write_bytes(raw.encode('utf-8'))
    (tmp_path/'SOURCE-PROMPT.zh.txt').write_bytes(translated.encode('utf-8'))
    record = {"source":{"url":"https://prompt-motion.com/example"},"motion_source":{
        "status":"complete","evidence_basis":"user_supplied_screenshot",
        "original_file":"SOURCE-PROMPT.txt","original_sha256":sha256(raw.encode()).hexdigest(),
        "translation_source_sha256":sha256(raw.encode()).hexdigest(),
        "translation_file":"SOURCE-PROMPT.zh.txt","translation_sha256":sha256(translated.encode()).hexdigest()}}
    result = source_prompt(tmp_path, record)
    assert result['original'] == raw and result['translation'] == translated and result['copyable']
    (tmp_path/'SOURCE-PROMPT.txt').write_text('Changed', encoding='utf-8')
    assert source_prompt(tmp_path, record)['status'] == 'unavailable'
    assert not source_prompt(tmp_path, record)['copyable']


def test_metadata_cannot_read_outside_entry(tmp_path):
    (tmp_path/'outside.txt').write_text('private',encoding='utf-8')
    folder=tmp_path/'entry'; folder.mkdir()
    result=source_prompt(folder, {"source":{"url":"https://prompt-motion.com/example"},"motion_source":{
        "status":"complete","original_file":"../outside.txt","original_sha256":sha256(b'private').hexdigest()}})
    assert result['status']=='unavailable' and result['original']==''


def test_regular_personal_prompt_keeps_existing_semantics(tmp_path):
    assert source_prompt(tmp_path, {"source":{"url":"https://example.org"}}) is None


def test_partial_excerpt_never_enables_original_copy(tmp_path):
    result=source_prompt(tmp_path,{"source":{"url":"https://prompt-motion.com/example"},"motion_source":{
        "status":"excerpt_only","excerpt":"A short quote","excerpt_translation":"一段摘录"}})
    assert result['excerpt']=='A short quote' and not result['copyable']


@pytest.mark.parametrize('broken', ['translation','analysis'])
def test_broken_auxiliary_file_keeps_verified_original_readable(tmp_path, broken):
    raw, translated = 'Animate a circle.', '让圆形运动。'
    (tmp_path/'source.txt').write_bytes(raw.encode())
    (tmp_path/'translation.txt').write_bytes(translated.encode())
    (tmp_path/'analysis.md').write_bytes(b'Notes')
    record={'source':{'url':'https://prompt-motion.com/example'},'motion_source':{
        'status':'complete','original_file':'source.txt','original_sha256':sha256(raw.encode()).hexdigest(),
        'translation_source_sha256':sha256(raw.encode()).hexdigest(),
        'translation_file':'translation.txt','translation_sha256':sha256(translated.encode()).hexdigest(),
        'analysis_file':'analysis.md','analysis_sha256':sha256(b'Notes').hexdigest()}}
    (tmp_path/('translation.txt' if broken=='translation' else 'analysis.md')).write_bytes(b'Broken')
    result=source_prompt(tmp_path,record)
    assert result['original']==raw and result['copyable']
    assert result['translation']==('' if broken=='translation' else translated)


def test_motion_translation_is_bound_to_source_not_just_its_own_hash(tmp_path):
    raw='Animate a square.'
    (tmp_path/'source.txt').write_bytes(raw.encode())
    (tmp_path/'translation.txt').write_bytes('让圆形运动。'.encode())
    record={'source':{'url':'https://prompt-motion.com/example'},'motion_source':{
        'status':'complete','original_file':'source.txt','original_sha256':sha256(raw.encode()).hexdigest(),
        'translation_source_sha256':sha256(b'Animate a circle.').hexdigest(),
        'translation_file':'translation.txt','translation_sha256':sha256('让圆形运动。'.encode()).hexdigest()}}
    result=source_prompt(tmp_path,record)
    assert result['original']==raw and result['copyable']
    assert result['translation']=='' and result['translation_status']=='source_changed'
