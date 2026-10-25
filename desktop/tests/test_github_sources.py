"""GitHub 抓取客户端的离线契约测试：缓存、范围、限额与来源边界。"""

from pathlib import Path
from urllib.error import HTTPError, URLError
import base64
import json
import sys

import pytest

DESKTOP = Path(__file__).parents[1]
if str(DESKTOP) not in sys.path:
    sys.path.insert(0, str(DESKTOP))
import github_sources as sources
from github_sources import GitHubClient, Budget, BudgetExceeded, SourceError


class Response:
    def __init__(self, value):
        self.payload = json.dumps(value).encode("utf-8")
        self.headers = {"ETag": '"etag-1"'}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return self.payload[:size]


class Opener:
    def __init__(self, values):
        self.values = list(values)
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append((request, timeout))
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return Response(value)


def file_response(raw):
    return {"type": "file", "size": len(raw), "encoding": "base64", "content": base64.b64encode(raw).decode("ascii")}


def repository_response():
    return {"full_name": "Owner/Design", "default_branch": "main", "license": {"spdx_id": "MIT"}, "archived": False}


def test_immutable_cache_avoids_repeat_network_request(tmp_path):
    opener = Opener([{"message": "fixed response"}])
    client = GitHubClient(tmp_path, opener=opener)
    first = client.request("/test/immutable", immutable=True)
    assert client.request("/test/immutable", immutable=True) == first
    assert len(opener.requests) == 1


def test_etag_304_uses_previous_body(tmp_path):
    response_304 = HTTPError("https://api.github.com/test", 304, "Not Modified", {}, None)
    opener = Opener([{"message": "cached"}, response_304])
    client = GitHubClient(tmp_path, opener=opener)
    assert client.request("/test") == client.request("/test")
    assert opener.requests[1][0].get_header("If-none-match") == '"etag-1"'


def test_unknown_original_and_commit_patch_are_never_written_to_cache(tmp_path):
    marker = "DO_NOT_ARCHIVE_UNCONFIRMED_ORIGINAL_74631"
    opener = Opener([repository_response(), {"sha": "a" * 40, "files": [{"filename": "design.md", "patch": "+" + marker}]}, file_response(marker.encode())])
    client = GitHubClient(tmp_path, opener=opener)
    source, raw = client.fetch_file("owner/design", "design.md")
    assert raw.decode() == marker and source["license_status"] == "unknown"
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert marker not in path.read_text(encoding="utf-8"), path
            assert base64.b64encode(marker.encode()).decode() not in path.read_text(encoding="utf-8"), path


def test_file_license_is_not_inferred_from_repository_spdx(tmp_path):
    opener = Opener([repository_response(), {"sha": "a" * 40}, file_response(b"published instructions")])
    client = GitHubClient(tmp_path, opener=opener)
    source, _ = client.fetch_file("owner/design", "design.md")
    assert source["license"] == "MIT" and source["license_status"] == "unknown"
    assert source["repository"] == "Owner/Design"
    assert source["url"].startswith("https://github.com/Owner/Design/blob/")


def test_python_constant_extraction_does_not_execute_source(tmp_path):
    marker = tmp_path / "must-not-exist"
    script = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\nPROMPT = '''Keep labels.\nCheck twice.'''\n".encode()
    assert GitHubClient.extract(script, {"type": "python_literal", "name": "PROMPT"}) == b"Keep labels.\nCheck twice."
    assert not marker.exists()
    with pytest.raises(SourceError):
        GitHubClient.extract(b"PROMPT = build_prompt()", {"type": "python_literal", "name": "PROMPT"})


def test_notebook_cells_extract_only_explicit_selected_cells():
    notebook = {"cells": [{"source": ["first\n", "line\n"]}, {"source": "second\n"}, {"source": ["third\n"]}]}
    raw = json.dumps(notebook).encode()
    assert GitHubClient.extract(raw, {"type": "notebook_cells", "indexes": [0, 2]}) == b"first\nline\n\nthird\n"
    with pytest.raises(SourceError):
        GitHubClient.extract(raw, {"type": "notebook_cells", "indexes": [4]})


def test_heading_and_line_excerpts_preserve_selected_bytes():
    raw = b"# Root\r\n## Camera\r\nMove slowly.\r\n### Nested\r\nStill camera.\r\n## Lighting\r\nSoft.\r\n"
    assert GitHubClient.extract(raw, {"type": "heading", "heading": "Camera"}) == b"## Camera\r\nMove slowly.\r\n### Nested\r\nStill camera.\r\n"
    assert GitHubClient.extract(raw, {"type": "lines", "start": 2, "end": 3}) == b"## Camera\r\nMove slowly.\r\n"
    with pytest.raises(SourceError, match="标题"):
        GitHubClient.extract(raw, {"type": "heading", "heading": "Missing"})


@pytest.mark.parametrize("url", ["http://github.com/a/b", "https://example.com/a/b", "https://github.com:443/a/b", "https://user@github.com/a/b", "https://github.com/a/b/blob/main/../private.md", "https://github.com/a/b/blob/main/%2e%2e/private.md"])
def test_rejects_outside_or_ambiguous_source_urls(url):
    with pytest.raises(SourceError):
        GitHubClient.parse_url(url)


def test_url_decodes_file_and_explicit_line_span():
    repo, ref, path, excerpt = GitHubClient.parse_url("https://github.com/owner/repo/blob/main/My%20Prompt.md#L2-L4")
    assert (repo, ref, path, excerpt) == ("owner/repo", "main", "My Prompt.md", {"type": "lines", "start": 2, "end": 4})


def test_repository_and_file_budgets_are_enforced():
    budget = Budget(max_repositories=1, max_files=2)
    budget.check(repository="one/repo", file_attempt=True)
    budget.check(repository="one/repo", file_attempt=True)
    with pytest.raises(BudgetExceeded, match="仓库"):
        budget.check(repository="two/repo")
    with pytest.raises(BudgetExceeded, match="文件"):
        budget.check(file_attempt=True)


def test_retry_count_is_bounded_and_charged_to_file_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(sources.time, "sleep", lambda duration: None)
    opener = Opener([URLError("offline")] * 3)
    budget = Budget(max_files=3)
    client = GitHubClient(tmp_path, opener=opener, budget=budget)
    with pytest.raises(SourceError, match="网络"):
        client.request("/test", file_attempt=True, cache_response=False)
    assert len(opener.requests) == budget.file_attempts == 3


def test_rate_limit_stops_without_retry(tmp_path):
    opener = Opener([HTTPError("https://api.github.com/test", 429, "Too Many Requests", {}, None)])
    client = GitHubClient(tmp_path, opener=opener)
    with pytest.raises(SourceError, match="限流"):
        client.request("/test", file_attempt=True)
    assert len(opener.requests) == client.budget.file_attempts == 1


def test_remaining_time_controls_network_timeout(tmp_path, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(sources.time, "monotonic", lambda: clock[0])
    budget = Budget(max_seconds=10)
    clock[0] = 108.0
    opener = Opener([{"result": True}])
    client = GitHubClient(tmp_path, opener=opener, budget=budget)
    client.request("/test")
    assert opener.requests[0][1] <= 2.0
    clock[0] = 110.0
    with pytest.raises(BudgetExceeded, match="时间"):
        client.request("/other")


def test_oversized_file_response_is_not_accepted(tmp_path):
    opener = Opener([repository_response(), {"sha": "a" * 40}, {"type": "file", "size": 262145, "encoding": "base64", "content": ""}])
    client = GitHubClient(tmp_path, opener=opener)
    with pytest.raises(BudgetExceeded):
        client.fetch_file("Owner/Design", "huge.md")


def license_sources():
    old = {"repository": "Owner/Design", "commit": "a" * 40, "license_status": "allowed", "license_text": "MIT license\n", "license_file_url": "https://github.com/Owner/Design/blob/" + "a" * 40 + "/LICENSE"}
    return old, {**old, "commit": "b" * 40, "license_status": "unknown"}


def test_tracked_license_is_compared_exactly_and_memory_cached(tmp_path):
    old, new = license_sources()
    opener = Opener([file_response(b"MIT license\n")])
    client = GitHubClient(tmp_path, opener=opener)
    result = client.check_tracked_license(old, new)
    assert result["matches"] and result["status"] == "unchanged"
    assert "b" * 40 in result["license_file_url"]
    assert client.check_tracked_license(old, new)["matches"]
    assert len(opener.requests) == client.budget.file_attempts == 1
    assert not list(tmp_path.iterdir())


def test_tracked_license_change_is_not_normalized_away(tmp_path):
    old, new = license_sources()
    opener = Opener([file_response(b"MIT license\r\n")])
    client = GitHubClient(tmp_path, opener=opener)
    result = client.check_tracked_license(old, new)
    assert result["matches"] is False and result["status"] == "changed"
    assert not list(tmp_path.iterdir())


def test_same_commit_license_reuses_existing_verification_without_network(tmp_path):
    old, _ = license_sources()
    client = GitHubClient(tmp_path, opener=Opener([]))
    assert client.check_tracked_license(old, old)["matches"] is True
    assert client.budget.requests == 0


def test_tracked_license_network_failure_does_not_write_cache(tmp_path):
    old, new = license_sources()
    client = GitHubClient(tmp_path, opener=Opener([HTTPError("https://api.github.com/license", 404, "missing", {}, None)]))
    with pytest.raises(SourceError, match="不存在"):
        client.check_tracked_license(old, new)
    assert not list(tmp_path.iterdir())


def test_cross_repository_license_cannot_authorize_new_commit(tmp_path):
    old, new = license_sources()
    old["license_file_url"] = old["license_file_url"].replace("Owner/Design", "Another/Repo")
    client = GitHubClient(tmp_path, opener=Opener([]))
    assert client.check_tracked_license(old, new)["matches"] is False
    assert client.budget.requests == 0
