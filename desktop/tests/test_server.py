"""覆盖文件库读取、收藏留存、原文字节导出和本机请求边界。"""

from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import importlib.util
import json
import threading
import urllib.error
import urllib.request

import pytest

spec = importlib.util.spec_from_file_location("prompt_library_server", Path(__file__).parents[1] / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "library"
    folder = root / "entries" / "PRM-0001"
    folder.mkdir(parents=True)
    original = "原文不改\r\n<svg onload=alert(1)>\r\n".encode("utf-8")
    (folder / "original.md").write_bytes(original)
    (folder / "optimized-v001.md").write_text("# 标题\n```text\n请分析 {{主题}}\n```\n", encoding="utf-8")
    record = {"id": "PRM-0001", "original": {"file": "original.md"}, "source": {"type": "user_submission"}, "loop_review": {"reminder": "最多两轮"}}
    (folder / "record.json").write_text(json.dumps(record), encoding="utf-8")
    item = {"id": "PRM-0001", "title": "示例", "summary": "说明", "category_id": "taste", "tags": [], "record_file": "entries/PRM-0001/record.json", "original_file": "entries/PRM-0001/original.md", "optimized_file": "entries/PRM-0001/optimized-v001.md"}
    (root / "index.json").write_text(json.dumps({"entries": [item]}), encoding="utf-8")
    (root / "taxonomy.json").write_text(json.dumps({"categories": [{"id": "taste", "name": "审美"}]}), encoding="utf-8")
    return server.Library(root, tmp_path / "state")


@pytest.fixture
def endpoint(library):
    instance = server.LocalServer(("127.0.0.1", 0), library)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{instance.server_port}"
    instance.shutdown()
    instance.server_close()
    thread.join(timeout=2)


def request(url, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        response = urllib.request.urlopen(req)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.read(), response.headers


def test_catalogue_reads_real_entries_and_full_text(library):
    catalogue = library.catalogue()
    assert catalogue["entry_count"] == 1
    assert "原文不改" in catalogue["entries"][0]["search_text"]
    assert library.entry("PRM-0001")["optimized"] == "请分析 {{主题}}"


def test_regular_material_has_original_bound_reading_pair(library):
    detail = library.entry("PRM-0001")
    assert detail["reading_pair"]["original"] == detail["original"]
    assert detail["reading_pair"]["translation_status"] == "missing"
    assert detail["reading_pair"]["translation"] == ""


def test_regular_translation_is_not_an_optimized_rewrite(library):
    folder = library.root / "entries" / "PRM-0001"
    path = folder / "record.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    translated = "对应的中文译文，保留原文中的 SVG 代码。"
    (folder / "translation.zh.md").write_bytes(translated.encode("utf-8"))
    record["translation"] = {"status": "ready", "file": "translation.zh.md",
                             "source_sha256": sha256((folder / "original.md").read_bytes()).hexdigest(),
                             "sha256": sha256(translated.encode()).hexdigest()}
    path.write_text(json.dumps(record), encoding="utf-8")
    detail = library.entry("PRM-0001")
    assert detail["reading_pair"]["translation"] == translated
    assert detail["reading_pair"]["translation"] != detail["optimized"]
    assert translated in library.catalogue()["entries"][0]["search_text"]


def test_favorite_persists_without_changing_sources(library):
    before = {p: sha256(p.read_bytes()).digest() for p in library.root.rglob("*") if p.is_file()}
    library.set_favorite("PRM-0001", True)
    reopened = server.Library(library.root, library.state_dir)
    assert reopened.favorites() == ["PRM-0001"]
    assert before == {p: sha256(p.read_bytes()).digest() for p in before}
    assert reopened.set_favorite("PRM-0001", False) == []


def test_invalid_state_does_not_overwrite_favorites(library):
    library.set_favorite("PRM-0001", True)
    with pytest.raises(ValueError):
        library.set_favorite("PRM-0001", "false")
    assert library.favorites() == ["PRM-0001"]


def test_metadata_cannot_escape_library(library):
    with pytest.raises(ValueError):
        library.contained_path("../outside.txt")


def test_original_download_preserves_bytes(endpoint, library):
    status, body, headers = request(endpoint + "/download/PRM-0001/original")
    assert status == 200
    assert body == (library.root / "entries/PRM-0001/original.md").read_bytes()
    assert "attachment" in headers["Content-Disposition"]


def test_motion_curation_cannot_be_exported_as_source(endpoint, library):
    path=library.root/'entries/PRM-0001/record.json'
    record=json.loads(path.read_text(encoding='utf-8'));record['source']['url']='https://prompt-motion.com/example'
    path.write_text(json.dumps(record),encoding='utf-8')
    assert library.entry('PRM-0001')['source_prompt']['copyable'] is False
    assert request(endpoint+'/download/PRM-0001/original')[0]==409


def test_motion_original_download_uses_exact_source_body(endpoint, library):
    path=library.root/'entries/PRM-0001/record.json'
    raw='Animate a circle.\nFade out.'
    for name,text in [('source.txt',raw),('translation.txt','圆形动画，随后淡出。')]:
        (path.parent/name).write_bytes(text.encode('utf-8'))
    record=json.loads(path.read_text(encoding='utf-8'));record['source']['url']='https://prompt-motion.com/example'
    record['motion_source']={'status':'complete','original_file':'source.txt','original_sha256':sha256(raw.encode()).hexdigest(),
                             'translation_file':'translation.txt','translation_sha256':sha256('圆形动画，随后淡出。'.encode()).hexdigest()}
    path.write_text(json.dumps(record),encoding='utf-8')
    status,body,_=request(endpoint+'/download/PRM-0001/original')
    assert status==200 and body.decode('utf-8')==raw


@pytest.mark.parametrize("path", ["/api/entries/PRM-9999", "/api/entries/../../index.json", "/desktop/.runtime/favorites.json", "/index.json"])
def test_unknown_and_private_paths_not_served(endpoint, path):
    assert request(endpoint + path)[0] == 404


def test_cross_site_mutation_is_rejected(endpoint, library):
    status, _, _ = request(endpoint + "/api/favorites", {"id": "PRM-0001", "favorite": True}, {"Origin": "https://example.org", "Content-Type": "application/json", "X-Prompt-Library": "1"})
    assert status == 403
    assert library.favorites() == []


def test_valid_mutation_roundtrip(endpoint):
    status, body, _ = request(endpoint + "/api/favorites", {"id": "PRM-0001", "favorite": True}, {"Origin": endpoint, "Content-Type": "application/json", "X-Prompt-Library": "1"})
    assert status == 200
    assert json.loads(body)["favorites"] == ["PRM-0001"]
    assert json.loads(request(endpoint + "/api/library")[1])["favorites"] == ["PRM-0001"]


def test_external_host_is_rejected(endpoint):
    assert request(endpoint + "/api/library", headers={"Host": "outside.invalid"})[0] == 403


def test_empty_library_is_valid(library):
    (library.root / "index.json").write_text('{"entries":[]}', encoding="utf-8")
    assert library.catalogue()["entry_count"] == 0


def test_local_server_starts_without_reverse_dns(library, monkeypatch):
    def unavailable_dns(*args):
        raise AssertionError("本机服务启动不应等待反向 DNS")
    monkeypatch.setattr("socket.getfqdn", unavailable_dns)
    instance = server.LocalServer(("127.0.0.1", 0), library)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    try:
        status, body, _ = request(f"http://127.0.0.1:{instance.server_port}/api/health")
        assert status == 200 and json.loads(body)["app"] == server.APP_ID
        assert instance.server_name == "127.0.0.1"
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=2)


def test_html_is_protected_by_content_security_policy(endpoint):
    status, body, headers = request(endpoint + "/")
    assert status == 200
    assert b"<script src=\"/app.js\" defer>" in body
    assert "script-src 'self'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"

def test_feedback_window_offers_user_initiated_private_and_public_channels(endpoint):
    status, page, _ = request(endpoint + "/")
    html = page.decode("utf-8")
    assert status == 200
    assert 'id="feedback-dialog"' in html
    assert 'mailto:rome@chatpaperhub.com' in html
    assert 'https://github.com/Shanvision-star/liubai-prompt-library/issues/new/choose' in html
    status, script, _ = request(endpoint + "/feedback.js")
    assert status == 200 and b'showModal' in script


def test_entry_exposes_english_translation_without_changing_chinese(library):
    folder = library.root / 'entries' / 'PRM-0001'
    path = folder / 'record.json'
    record = json.loads(path.read_text(encoding='utf-8'))
    en = b'English translation'
    (folder / 'translation.en.md').write_bytes(en)
    record['translations'] = {'en': {'status': 'ready', 'file': 'translation.en.md',
         'source_sha256': sha256((folder / 'original.md').read_bytes()).hexdigest(),
         'sha256': sha256(en).hexdigest()}}
    path.write_text(json.dumps(record), encoding='utf-8')
    detail = library.entry('PRM-0001')
    assert detail['reading_pair_en']['translation'] == en.decode()
    assert detail['reading_pair']['translation_status'] == 'missing'


def test_catalogue_can_find_verified_english_translation(library):
    folder = library.root / 'entries' / 'PRM-0001'
    path = folder / 'record.json'
    record = json.loads(path.read_text(encoding='utf-8'))
    en = b'unique english search phrase'
    (folder / 'translation.en.md').write_bytes(en)
    record['translations'] = {'en': {'status': 'ready', 'file': 'translation.en.md',
         'source_sha256': sha256((folder / 'original.md').read_bytes()).hexdigest(),
         'sha256': sha256(en).hexdigest()}}
    path.write_text(json.dumps(record), encoding='utf-8')
    assert en.decode() in library.catalogue()['entries'][0]['search_text']


def test_language_resources_and_system_locale_are_local(endpoint):
    status, payload, headers = request(endpoint + '/api/system-language')
    assert status == 200
    assert set(json.loads(payload)) == {'language'}
    status, script, _ = request(endpoint + '/language-choice.js')
    assert status == 200 and b'resolveLanguage' in script
    csp = headers['Content-Security-Policy']
    assert "connect-src 'self';" in csp and "ipwho.is" not in csp


def test_language_ui_resources_are_served(endpoint):
    status, html, _ = request(endpoint + '/')
    assert status == 200 and b'id="language-select"' in html
    status, script, _ = request(endpoint + '/i18n.js')
    assert status == 200 and b'LiubaiI18n' in script


def test_motion_english_catalogue_is_bound_to_the_verified_original(library):
    folder = library.root / 'entries' / 'PRM-0001'
    path = folder / 'record.json'
    record = json.loads(path.read_text(encoding='utf-8'))
    original = b'Please use "Montage" (example).\nWhat it is: A run of short shots.\n'
    (folder / 'original.md').write_bytes(original)
    record['original']['sha256'] = sha256(original).hexdigest()
    record['title'] = '示例'
    record['summary'] = '说明'
    record['source'] = {'type':'licensed_upstream','repository':'showheyohtaki/motion-prompt',
                        'url':'https://github.com/showheyohtaki/motion-prompt/blob/commit/api/v1/en/p/192.txt'}
    path.write_text(json.dumps(record), encoding='utf-8')
    row = library.catalogue()['entries'][0]
    assert row['english_catalogue'] == {'title':'Montage','summary':'A run of short shots.','original_language':'en'}
    (folder / 'original.md').write_bytes(original + b'changed')
    assert library.catalogue()['entries'][0]['english_catalogue'] is None


def test_language_preference_persists_in_local_runtime_and_validates(endpoint, library):
    headers = {'Origin':endpoint, 'X-Prompt-Library':'1', 'Content-Type':'application/json'}
    assert request(endpoint + '/api/language-preference')[0] == 200
    status, _, _ = request(endpoint + '/api/language-preference', {'language':'en'}, headers)
    assert status == 200
    assert json.loads(request(endpoint + '/api/language-preference')[1])['language'] == 'en'
    assert server.Library(library.root, library.state_dir).language_preference() == 'en'
    assert request(endpoint + '/api/language-preference', {'language':'fr'}, headers)[0] == 400
    assert request(endpoint + '/api/language-preference', {'language':'auto'}, headers)[0] == 200
    assert json.loads(request(endpoint + '/api/language-preference')[1])['language'] == 'auto'
    assert request(endpoint + '/api/language-preference', {'language':'zh'}, {'Content-Type':'application/json'})[0] == 403
    library.language_path.write_text('{"language":[]}', encoding='utf-8')
    assert request(endpoint + '/api/language-preference')[0] == 400
    assert json.loads(library.language_path.read_text(encoding='utf-8')) == {'language': []}


def test_curated_english_metadata_matches_original_hash(library, tmp_path, monkeypatch):
    folder = library.root / 'entries' / 'PRM-0001'
    original = (folder / 'original.md').read_bytes()
    metadata = {'PRM-0001': {'original_sha256':sha256(original).hexdigest(), 'title':'Example', 'summary':'Example summary', 'original_language':'en', 'title_source_sha256':sha256('示例'.encode()).hexdigest()}}
    (tmp_path / 'public-en.json').write_text(json.dumps(metadata),encoding='utf-8')
    monkeypatch.setattr(server, 'WEB_ROOT', tmp_path)
    assert library.catalogue()['entries'][0]['english_catalogue']['title'] == 'Example'
    (folder / 'original.md').write_bytes(original+b'!')
    assert library.catalogue()['entries'][0]['english_catalogue'] is None


def test_compact_settings_do_not_automatically_query_ip(endpoint):
    status, html, _ = request(endpoint + '/')
    assert status == 200 and b'id="settings-menu"' in html
    assert b'ipwho.is' not in html and b'IPWhois' not in html
    status, script, _ = request(endpoint + '/language-ui.js')
    assert status == 200 and b'lookupCountry' not in script


def test_bundled_english_catalogue_is_hash_bound_to_public_originals():
    project = Path(__file__).resolve().parents[2]
    curated = json.loads((project / 'desktop/web/public-en.json').read_text(encoding='utf-8'))
    catalogue = json.loads((project / 'bundled-library/index.json').read_text(encoding='utf-8'))
    by_id = {item['id']:item for item in catalogue['entries']}
    assert len(curated) == 60
    for entry_id, row in curated.items():
        original = (project / 'bundled-library' / by_id[entry_id]['original_file']).read_bytes()
        assert sha256(original).hexdigest() == row['original_sha256']
        assert sha256(by_id[entry_id]['title'].encode('utf-8')).hexdigest() == row['title_source_sha256']
        assert sha256(by_id[entry_id].get('summary','').encode('utf-8')).hexdigest() == row['summary_source_sha256']
        assert row['title'].strip() and row['summary'].strip()
        assert row['original_language'] in {'en','unknown'}
        assert row['original_language'] == 'en' or row.get('translation')
        if 'translation' in row:
            assert sha256(row['translation'].encode('utf-8')).hexdigest() == row['translation_sha256']


def test_bad_catalogue_translation_never_hides_user_originals(library, tmp_path, monkeypatch):
    (tmp_path / 'public-en.json').write_text('{invalid', encoding='utf-8')
    monkeypatch.setattr(server, 'WEB_ROOT', tmp_path)
    result = library.catalogue()
    assert result['entry_count'] == 1
    assert '原文不改' in result['entries'][0]['search_text']


def test_bundled_english_text_is_used_only_for_matching_original(library, tmp_path, monkeypatch):
    original=(library.root / 'entries/PRM-0001/original.md').read_bytes()
    english='Translated text'; data=english.encode('utf-8')
    curated={'PRM-0001':{'original_sha256':sha256(original).hexdigest(),'title':'Example','summary':'',
        'original_language':'unknown','translation':english,'translation_sha256':sha256(data).hexdigest()}}
    (tmp_path/'public-en.json').write_text(json.dumps(curated),encoding='utf-8')
    monkeypatch.setattr(server,'WEB_ROOT',tmp_path)
    assert library.entry('PRM-0001')['reading_pair_en']['translation'] == english
    curated['PRM-0001']['translation']='altered'
    (tmp_path/'public-en.json').write_text(json.dumps(curated),encoding='utf-8')
    assert library.entry('PRM-0001')['reading_pair_en']['translation'] == ''


def test_curated_title_does_not_hide_a_user_renamed_item(library, tmp_path, monkeypatch):
    original = (library.root / 'entries/PRM-0001/original.md').read_bytes()
    metadata = {'PRM-0001': {'original_sha256':sha256(original).hexdigest(),
        'title_source_sha256':sha256('旧标题'.encode()).hexdigest(), 'title':'Old title', 'summary':'', 'original_language':'unknown'}}
    (tmp_path / 'public-en.json').write_text(json.dumps(metadata),encoding='utf-8')
    monkeypatch.setattr(server,'WEB_ROOT',tmp_path)
    assert library.catalogue()['entries'][0]['english_catalogue'] is None


def test_upstream_title_extraction_does_not_replace_user_title(library):
    folder=library.root/'entries/PRM-0001'
    path=folder/'record.json'; record=json.loads(path.read_text(encoding='utf-8'))
    original=b'Please use "Montage".\nWhat it is: Short shots.\n'
    (folder/'original.md').write_bytes(original)
    record['title']='Source title'
    record['original']['sha256']=sha256(original).hexdigest()
    record['source']={'type':'licensed_upstream','repository':'showheyohtaki/motion-prompt','url':'https://github.com/showheyohtaki/motion-prompt/blob/commit/api/v1/en/p/1.txt'}
    path.write_text(json.dumps(record),encoding='utf-8')
    assert library.catalogue()['entries'][0]['english_catalogue'] is None


def test_curated_summary_does_not_hide_user_edited_summary(library, tmp_path, monkeypatch):
    original=(library.root/'entries/PRM-0001/original.md').read_bytes()
    metadata={'PRM-0001':{'original_sha256':sha256(original).hexdigest(),
       'title_source_sha256':sha256('示例'.encode()).hexdigest(),
       'summary_source_sha256':sha256('旧说明'.encode()).hexdigest(),
       'title':'Example','summary':'Old description','original_language':'unknown'}}
    (tmp_path/'public-en.json').write_text(json.dumps(metadata),encoding='utf-8')
    monkeypatch.setattr(server,'WEB_ROOT',tmp_path)
    assert library.catalogue()['entries'][0]['english_catalogue']['summary'] is None


def test_public_translations_preserve_source_links_and_numeric_tokens():
    import re
    project=Path(__file__).resolve().parents[2]
    curated=json.loads((project/'desktop/web/public-en.json').read_text(encoding='utf-8'))
    for entry_id,row in curated.items():
        if 'translation' not in row:
            continue
        original=(project/'bundled-library/entries'/entry_id/'original.md').read_text(encoding='utf-8')
        translated=row['translation']
        for url in re.findall(r'https?://[^\s)]+', original):
            assert url in translated, (entry_id,url)
        for number in re.findall(r'(?<!\w)\d+(?:\.\d+)?', original):
            assert number in translated, (entry_id,number)
