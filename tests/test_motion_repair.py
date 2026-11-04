"""核对迁移保留旧原文、拒绝并发改写及逐词匹配分析依据。"""
import json
import sys
from hashlib import sha256
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import repair_motion_sources as repair


def test_design_reasons_use_words_not_substrings():
    text=repair.explanation('Build a machine with texture. Every note comes from a visible collision.','',True)
    assert '产品状态变化' not in text and '文字既是信息' not in text
    assert '声音与可见动作' in text and '初步建议' in text


@pytest.fixture
def source_and_target(tmp_path):
    source=tmp_path/'source';target=tmp_path/'target'
    raw='Animate a circle.'
    for root in (source,target):
        folder=root/'entries/PRM-0001';folder.mkdir(parents=True)
        record={'id':'PRM-0001','source':{'url':'https://prompt-motion.com/example'},'original':{'file':'original.md'},'versions':[{'version':'v001'}]}
        (folder/'record.json').write_text(json.dumps(record),encoding='utf-8')
        text='# Old curation' if root==target else f'## 原语言短引与中文\n\n> {raw}\n\n中文译文：一个圆形动画。\n\n## 来源\n原网站正文 SHA-256：{sha256(raw.encode()).hexdigest()}'
        (folder/'original.md').write_text(text,encoding='utf-8')
    (target/'index.json').write_text(json.dumps({'entries':[{'id':'PRM-0001','record_file':'entries/PRM-0001/record.json'}]}),encoding='utf-8')
    return source,target,tmp_path/'audit.json'


def test_repair_preserves_old_body_and_keeps_source_separate(source_and_target):
    source,target,report=source_and_target
    old=(target/'entries/PRM-0001/original.md').read_bytes()
    repair.repair(source,target,{},report,True)
    record=json.loads((target/'entries/PRM-0001/record.json').read_text(encoding='utf-8'))
    assert record['motion_source']['status']=='complete'
    assert (target/'entries/PRM-0001/original.md').read_bytes()==old
    assert record['versions']==[{'version':'v001'}]


def test_repair_rejects_record_changed_during_planning(source_and_target,monkeypatch):
    source,target,report=source_and_target
    real=repair.ReferenceStore
    def edited(root):
        path=target/'entries/PRM-0001/record.json';record=json.loads(path.read_text(encoding='utf-8'))
        record['versions'].append({'version':'v002'});path.write_text(json.dumps(record),encoding='utf-8')
        return real(root)
    monkeypatch.setattr(repair,'ReferenceStore',edited)
    with pytest.raises(ValueError,match='记录已被修改'):repair.repair(source,target,{},report,True)
    assert len(json.loads((target/'entries/PRM-0001/record.json').read_text(encoding='utf-8'))['versions'])==2
