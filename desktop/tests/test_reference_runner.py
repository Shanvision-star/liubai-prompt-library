"""隔离验证参考库调度、恢复、运行互斥与失败证据，不发网络请求。"""

from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
import json
import sys
import threading
import base64

import pytest

DESKTOP = Path(__file__).parents[1]
if str(DESKTOP) not in sys.path:
    sys.path.insert(0, str(DESKTOP))
import reference_runner as runner_module
from reference_runner import ReferenceRunner, RunLock, atomic_json
from github_sources import SourceError, BudgetExceeded
from test_references import analysis, source, save_json


TZ = timezone(timedelta(hours=8))


class FakeClient:
    def __init__(self):
        self.contents = {}
        self.calls = []
        self.search_calls = []
        self.errors = {}
        self.search_error = None

    def fetch_file(self, repository, path, ref=None, extraction=None, allow_archive_cache=False):
        self.calls.append((repository, path, ref, extraction, allow_archive_cache))
        if path in self.errors:
            raise self.errors[path]
        return self.contents[path]

    def search(self, category_id=None, max_results=4):
        self.search_calls.append(category_id)
        if self.search_error:
            raise self.search_error
        return {"candidates": []}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    root = tmp_path / "library"
    root.mkdir()
    save_json(root / "taxonomy.json", {"categories": [{"id": "ui_design", "name": "UI 设计"}, {"id": "uncategorized", "name": "待分类"}]})
    save_json(root / "index.json", {"entries": [], "entry_count": 0})
    clock = [datetime(2026, 10, 25, 8, 0, tzinfo=TZ)]
    monkeypatch.setattr(runner_module, "now", lambda: clock[0])
    client = FakeClient()
    runner = ReferenceRunner(root, lambda budget: client)
    return runner, client, clock


def add_reference(runner, client, path="skills/design.md", extraction=None):
    raw = b"Original prompt\nKeep labels.\n"
    metadata = source(path=path)
    metadata["tracking_full_sha256"] = sha256(raw).hexdigest()
    if extraction:
        metadata["extraction"] = extraction
    item = runner.store.ingest(metadata, raw, {"title": path, "category_id": "ui_design"})
    runner.store.set_analysis(item["id"], item["snapshot_id"], analysis())
    runner.store.set_flags(item["id"], followed=True)
    client.contents[path] = ({**metadata, "license_status": "unknown"}, raw)
    return item["id"]


def activate(runner, clock):
    runner.register("test-automation")
    clock[0] = datetime(2026, 10, 26, 9, 0, tzinfo=TZ)


def test_default_schedule_is_daily_nine_shanghai_and_requires_registration(setup):
    runner, _, clock = setup
    config = runner.configuration()
    assert (config["frequency"], config["hour"], config["timezone"], config["weekday"]) == ("daily", 9, "Asia/Shanghai", 6)
    assert runner.due()["reason"] == "scheduler_not_registered"
    runner.register("automation-id")
    assert runner.due()["reason"] == "before_first_schedule"
    clock[0] = clock[0].replace(hour=9)
    assert runner.due()["due"] is True
    assert runner.status()["next_run"] == "2026-10-26T09:00:00+08:00"


def test_paused_schedule_does_not_run_but_manual_force_does(setup):
    runner, client, clock = setup
    add_reference(runner, client)
    activate(runner, clock)
    runner.configure({"enabled": False})
    assert runner.run()["reason"] == "paused"
    assert client.calls == []
    assert runner.status()["next_run"] is None
    result = runner.run(force=True, trigger="manual")
    assert result["status"] == "success" and len(client.calls) == 1


def test_period_is_checked_once_and_backlog_is_coalesced(setup):
    runner, client, clock = setup
    add_reference(runner, client)
    activate(runner, clock)
    clock[0] = datetime(2026, 11, 4, 15, 0, tzinfo=TZ)
    result = runner.run()
    assert result["status"] == "success"
    assert result["period"] == "daily:2026-11-04"
    assert runner.run()["reason"] == "already_checked"
    assert len(client.calls) == 1
    assert len(runner.status()["runs"]) == 1


def test_weekly_slot_and_next_run_are_sunday_nine(setup):
    runner, _, clock = setup
    activate(runner, clock)
    runner.configure({"frequency": "weekly", "weekday": 6})
    assert runner.latest_slot(runner.configuration(), clock[0]).isoformat() == "2026-10-25T09:00:00+08:00"
    assert runner.next_run(runner.configuration(), clock[0]) == "2026-11-01T09:00:00+08:00"
    utc_moment = datetime(2026, 10, 26, 1, 0, tzinfo=timezone.utc)
    assert runner.next_run(runner.configuration(), utc_moment) == "2026-11-01T09:00:00+08:00"


def test_busy_job_is_not_started_twice(setup):
    runner, _, clock = setup
    activate(runner, clock)
    prepared = runner._prepare(force=False, trigger="test", acceptance=False)
    assert prepared["started"]
    try:
        assert runner.start()["reason"] == "busy"
        assert runner.status()["running"] is True
    finally:
        prepared["lock"].release()


def test_interrupted_period_recovers_once_and_then_stops(setup):
    runner, _, clock = setup
    activate(runner, clock)
    first = runner._prepare(False, "test", False)
    first["lock"].release()
    assert runner.status()["runs"][0]["status"] == "interrupted"
    assert runner.due()["due"] is True
    recovered = ReferenceRunner(runner.root, runner.client_factory)
    second = recovered._prepare(False, "recovery", False)
    assert second["started"] is True
    second["lock"].release()
    recovered.status()
    assert recovered.due()["reason"] == "recovery_limit"
    assert len(recovered.status()["runs"]) == 2


def test_network_failure_keeps_success_timestamp_and_can_recover_once(setup):
    runner, client, clock = setup
    ref_id = add_reference(runner, client)
    activate(runner, clock)
    runner.run()
    previous = runner.status()["last_success"]
    source_success = runner.store.detail(ref_id)["item"]["last_success"]
    clock[0] += timedelta(days=1)
    client.errors["skills/design.md"] = SourceError("网络断开")
    failure = runner.run()
    assert failure["status"] == "failed"
    assert runner.status()["last_success"] == previous
    assert runner.store.detail(ref_id)["item"]["last_success"] == source_success
    assert runner.due()["due"] is True
    client.errors.clear()
    recovery = runner.run()
    assert recovery["status"] == "success"
    assert runner.run()["reason"] == "already_checked"


def test_changed_reference_becomes_pending_and_old_analysis_is_preserved(setup):
    runner, client, clock = setup
    ref_id = add_reference(runner, client)
    activate(runner, clock)
    changed = source(commit="b" * 40, license_status="unknown")
    changed["tracking_full_sha256"] = sha256(b"changed prompt").hexdigest()
    client.contents["skills/design.md"] = (changed, b"changed prompt")
    result = runner.run()
    detail = runner.store.detail(ref_id)
    assert result["changed"] == 1 and result["pending_analysis"] == 1
    assert detail["snapshot"]["id"] == "s002"
    assert detail["analysis"] is None and detail["original"] is None
    assert runner.store.detail(ref_id, "s001")["analysis"]["version"] == "a001"


@pytest.mark.parametrize("failure", [SourceError("GitHub 暂时限流"), BudgetExceeded("达到文件上限")])
def test_rate_limit_or_budget_stops_following_requests(setup, failure):
    runner, client, clock = setup
    first = add_reference(runner, client, "first.md")
    second = add_reference(runner, client, "second.md")
    # 内容去重会复用第一条，因此第二条须提供不同正文。
    runner.store.ingest(source(path="second.md"), b"different source\n", {"category_id": "ui_design"})
    second_record = next(item for item in runner.store.catalogue()["references"] if item["source"]["path"] == "second.md")
    runner.store.set_flags(second_record["id"], followed=True)
    client.errors["first.md"] = failure
    activate(runner, clock)
    result = runner.run()
    assert result["status"] == "failed"
    assert result["stopped_reason"] == str(failure)
    assert [call[1] for call in client.calls] == ["first.md"]
    assert runner.store.detail(first)["item"]["last_check_status"] == "failed"


@pytest.mark.parametrize("extraction", [{"type": "lines", "start": 1, "end": 2}, {"type": "notebook_cells", "indexes": [1, 2]}])
def test_position_based_excerpt_requires_review_when_commit_changes(setup, extraction):
    runner, client, clock = setup
    ref_id = add_reference(runner, client, extraction=extraction)
    activate(runner, clock)
    changed = {**source(commit="b" * 40), "extraction": extraction, "tracking_full_sha256": sha256(b"changed").hexdigest()}
    client.contents["skills/design.md"] = (changed, b"potentially wrong cells")
    result = runner.run()
    assert result["status"] == "failed"
    assert runner.store.detail(ref_id)["snapshot"]["id"] == "s001"
    assert "核对" in result["errors"][0]["error"]


def test_client_initialization_failure_releases_lock_and_records_failure(setup):
    runner, _, clock = setup
    activate(runner, clock)

    def broken_factory(budget):
        raise OSError("缓存目录不可写")

    runner.client_factory = broken_factory
    result = runner.run()
    assert result["status"] == "failed"
    assert runner.status()["running"] is False
    lock = RunLock(runner.operations / "runner.lock")
    assert lock.acquire() is True
    lock.release()


def test_sunday_discovery_is_not_repeated_for_successful_period(setup):
    runner, client, clock = setup
    runner.register("automation-id")
    clock[0] = clock[0].replace(hour=9)
    assert runner.run()["status"] == "success"
    assert client.search_calls == ["ui_design", "taste", "visual"]
    assert runner.run()["reason"] == "already_checked"
    assert len(client.search_calls) == 3


def test_config_rejects_invalid_values(setup):
    runner, _, _ = setup
    for invalid in ({"enabled": "false"}, {"hour": 10}, {"weekday": 7}, {"frequency": "minutely"}):
        with pytest.raises(ValueError):
            runner.configure(invalid)


def test_async_start_holds_run_lock_until_fetch_finishes(setup):
    runner, client, clock = setup
    add_reference(runner, client)
    activate(runner, clock)
    fetching = threading.Event()
    release = threading.Event()
    complete = threading.Event()
    original_fetch = client.fetch_file
    original_execute = runner._execute

    def slow_fetch(*args, **kwargs):
        fetching.set()
        assert release.wait(5)
        return original_fetch(*args, **kwargs)

    def observed_execute(*args, **kwargs):
        try:
            return original_execute(*args, **kwargs)
        finally:
            complete.set()

    client.fetch_file = slow_fetch
    runner._execute = observed_execute
    assert runner.start()["started"] is True
    assert fetching.wait(3)
    try:
        assert runner.start()["reason"] == "busy"
        assert runner.status()["running"] is True
    finally:
        release.set()
    assert complete.wait(5)
    assert runner.status()["running"] is False


def test_discovery_rate_limit_stops_further_category_requests(setup):
    runner, client, clock = setup
    runner.register("automation-id")
    clock[0] = clock[0].replace(hour=9)
    client.search_error = SourceError("GitHub 暂时限流")
    result = runner.run()
    assert result["status"] == "failed"
    assert client.search_calls == ["ui_design"]


def test_state_write_failure_always_releases_run_lock(setup, monkeypatch):
    runner, _, clock = setup
    activate(runner, clock)
    job = runner._prepare(False, "test", False)

    def fail_state_write(path, value):
        raise OSError("磁盘写入失败")

    monkeypatch.setattr(runner_module, "atomic_json", fail_state_write)
    with pytest.raises(OSError):
        runner._execute(job["record"], job["lock"])
    new_lock = RunLock(runner.operations / "runner.lock")
    assert new_lock.acquire() is True
    new_lock.release()


def test_new_upstream_version_does_not_inherit_old_permission_to_cache_body(setup):
    from github_sources import GitHubClient
    from test_github_sources import Opener, file_response, repository_response

    runner, client, clock = setup
    ref_id = add_reference(runner, client)
    activate(runner, clock)
    marker = "NEW_VERSION_LICENSE_NOT_YET_REVIEWED_23783"
    opener = Opener([repository_response(), {"sha": "b" * 40}, file_response(marker.encode())])
    cache = runner.root / "test-network-cache"
    runner.client_factory = lambda budget: GitHubClient(cache, budget=budget, opener=opener)
    result = runner.run()
    assert result["status"] == "success"
    assert runner.store.detail(ref_id)["item"]["source"]["license_status"] == "unknown"
    assert runner.store.detail(ref_id)["original"] is None
    for file in cache.rglob("*"):
        if file.is_file():
            cached = file.read_text(encoding="utf-8")
            assert marker not in cached
            assert base64.b64encode(marker.encode()).decode() not in cached


def followed_with_license(setup):
    runner, client, clock = setup
    ref_id = add_reference(runner, client)
    old, raw = client.contents["skills/design.md"]
    old = {**old, "license_status": "allowed", "license_file_url": source()["url"].replace("skills/design.md", "LICENSE")}
    runner.store.ingest(old, raw)
    changed = {**old, "commit": "b" * 40, "license_status": "unknown", "url": old["url"].replace("a" * 40, "b" * 40)}
    client.contents["skills/design.md"] = (changed, raw)
    activate(runner, clock)
    return runner, client, clock, ref_id, old


def test_unchanged_license_allows_same_body_and_preserves_old_license_snapshot(setup):
    runner, client, clock, ref_id, old = followed_with_license(setup)
    client.check_tracked_license = lambda previous, current: {"matches": True, "status": "unchanged", "reason": "逐字节相同", "license_file_url": old["license_file_url"].replace("a" * 40, "b" * 40)}
    result = runner.run()
    detail = runner.store.detail(ref_id)
    assert result["status"] == "success" and result["unchanged"] == 1
    assert detail["item"]["source"]["license_status"] == "allowed"
    assert detail["snapshot"]["id"] == "s001"
    assert detail["snapshot"]["source"]["license_file_url"] == old["license_file_url"]
    assert runner.store.adoption_preview(ref_id)["can_adopt"] is True


def test_license_change_creates_pending_snapshot_even_when_prompt_is_unchanged(setup):
    runner, client, clock, ref_id, old = followed_with_license(setup)
    client.check_tracked_license = lambda previous, current: {"matches": False, "status": "changed", "reason": "许可条款已变化"}
    before = runner.store.detail(ref_id)
    result = runner.run()
    detail = runner.store.detail(ref_id)
    assert result["status"] == "success" and result["changed"] == 1
    assert detail["snapshot"]["id"] == "s002"
    assert detail["item"]["analysis_status"] == "pending" and detail["original"] is None
    assert not runner.store.adoption_preview(ref_id)["can_adopt"]
    assert runner.store.detail(ref_id, "s001")["original"] == before["original"]
    assert runner.store.detail(ref_id, "s001")["snapshot"]["source"]["license_status"] == "allowed"


def test_license_check_failure_preserves_last_success_and_old_material(setup):
    runner, client, clock, ref_id, old = followed_with_license(setup)
    before = runner.store.detail(ref_id)

    def unavailable(previous, current):
        raise SourceError("许可文件暂时无法读取")

    client.check_tracked_license = unavailable
    result = runner.run()
    current = runner.store.detail(ref_id)
    assert result["status"] == "failed"
    assert current["item"]["last_success"] == before["item"]["last_success"]
    assert current["item"]["last_check_status"] == "failed"
    assert current["item"]["source"]["license_status"] == "unknown"
    assert current["item"]["analysis_status"] == "pending"
    assert not runner.store.adoption_preview(ref_id)["can_adopt"]
    assert runner.store.detail(ref_id, "s001")["original"] == before["original"]


def test_weekly_wednesday_schedule_discovers_on_selected_day(setup):
    runner, client, clock = setup
    runner.register("automation-id")
    runner.configure({"frequency": "weekly", "weekday": 2})
    clock[0] = datetime(2026, 10, 28, 9, 0, tzinfo=TZ)
    assert runner.run()["status"] == "success"
    assert client.search_calls == ["ui_design", "taste", "visual"]
    assert runner.run()["reason"] == "already_checked"
