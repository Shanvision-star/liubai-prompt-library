"""参考来源检查与定时入口：统一运行锁、限额、增量快照和失败恢复记录。"""

from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
import argparse
import json
import os
import threading
import uuid

from github_sources import GitHubClient, Budget, BudgetExceeded, SourceError
from reference_store import ReferenceStore

TZ = timezone(timedelta(hours=8))
LIMITS = {"max_repositories": 20, "max_files": 60, "max_bytes": 256 * 1024, "max_seconds": 900, "max_retries": 2, "max_analysis": 6}


def now():
    return datetime.now(TZ)


def iso(value=None):
    return (value or now()).isoformat(timespec="seconds")


def read_json(path, default):
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else default


def atomic_json(path, value):
    temporary = path.with_suffix(".tmp-" + uuid.uuid4().hex)
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class RunLock:
    """进程结束自动释放的操作系统锁，不依赖容易过期的 PID 标记。"""

    def __init__(self, path):
        self.path = path
        self.handle = None

    def acquire(self):
        file = self.path.open("a+b")
        file.seek(0, 2)
        if file.tell() == 0:
            file.write(b"0")
            file.flush()
        file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            file.close()
            return False
        self.handle = file
        return True

    def release(self):
        if self.handle:
            self.handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()
            self.handle = None


class ReferenceRunner:
    def __init__(self, root, client_factory=None):
        self.root = Path(root).resolve()
        self.store = ReferenceStore(self.root)
        self.operations = self.root / "references" / ".operations"
        self.operations.mkdir(parents=True, exist_ok=True)
        self.config_path = self.operations / "schedule.json"
        self.state_path = self.operations / "runs.json"
        self.discovery_path = self.operations / "discovery.json"
        self.mutex = threading.RLock()
        self.client_factory = client_factory or (lambda budget: GitHubClient(self.root / "desktop" / ".runtime" / "github-cache", budget))
        if not self.config_path.exists():
            atomic_json(self.config_path, {"enabled": True, "frequency": "daily", "weekday": 6, "hour": 9, "timezone": "Asia/Shanghai", "engine": "codex_heartbeat", "registration_status": "pending", "automation_id": None, "created_at": iso(), "limits": LIMITS})

    @contextmanager
    def _state_lock(self):
        lock = RunLock(self.operations / "state.lock")
        with self.mutex:
            for _ in range(100):
                if lock.acquire():
                    break
                import time
                time.sleep(.02)
            else:
                raise TimeoutError("更新状态正在写入，请稍后重试")
            try:
                yield
            finally:
                lock.release()

    def _state(self):
        return read_json(self.state_path, {"runs": [], "running": False, "periods": [], "attempts": {}, "last_attempt": None, "last_success": None, "last_error": None, "acceptance_completed": False})

    def configuration(self):
        return read_json(self.config_path, {})

    def configure(self, values):
        allowed = {"enabled", "frequency", "weekday"}
        if set(values) - allowed:
            raise ValueError("可调整采集开关、每日/每周频率与星期；唤醒时间固定为 09:00")
        with self._state_lock():
            config = self.configuration()
            if "enabled" in values and type(values["enabled"]) is not bool:
                raise ValueError("启用状态必须是布尔值")
            if "frequency" in values and values["frequency"] not in ("daily", "weekly"):
                raise ValueError("频率请选择每天或每周")
            if "weekday" in values and (type(values["weekday"]) is not int or not 0 <= values["weekday"] <= 6):
                raise ValueError("星期需要在 0 到 6 之间")
            config.update(values)
            config["updated_at"] = iso()
            atomic_json(self.config_path, config)
        return self.status()

    def register(self, automation_id, registration_status="active"):
        with self._state_lock():
            config = self.configuration()
            config.update(automation_id=automation_id, registration_status=registration_status, registered_at=iso())
            atomic_json(self.config_path, config)
        return self.status()

    @staticmethod
    def latest_slot(config, moment):
        slot = moment.astimezone(TZ).replace(hour=9, minute=0, second=0, microsecond=0)
        if config["frequency"] == "weekly":
            slot -= timedelta(days=(slot.weekday() - config["weekday"]) % 7)
            if slot > moment:
                slot -= timedelta(days=7)
        elif slot > moment:
            slot -= timedelta(days=1)
        return slot

    def due(self, moment=None):
        moment = (moment or now()).astimezone(TZ)
        config = self.configuration()
        state = self._state()
        slot = self.latest_slot(config, moment)
        key = config["frequency"] + ":" + slot.date().isoformat()
        if not config["enabled"]:
            return {"due": False, "reason": "paused", "period": key}
        if config["registration_status"] != "active":
            return {"due": False, "reason": "scheduler_not_registered", "period": key}
        if slot < datetime.fromisoformat(config["created_at"]):
            return {"due": False, "reason": "before_first_schedule", "period": key}
        if key in state["periods"]:
            return {"due": False, "reason": "already_checked", "period": key}
        if state.get("attempts", {}).get(key, 0) >= 2:
            return {"due": False, "reason": "recovery_limit", "period": key}
        return {"due": True, "reason": "scheduled_or_single_catch_up", "period": key}

    def next_run(self, config, moment=None):
        if not config["enabled"] or config["registration_status"] != "active":
            return None
        moment = (moment or now()).astimezone(TZ)
        candidate = moment.replace(hour=9, minute=0, second=0, microsecond=0)
        if candidate <= moment:
            candidate += timedelta(days=1)
        if config["frequency"] == "weekly":
            candidate += timedelta(days=(config["weekday"] - candidate.weekday()) % 7)
        return iso(candidate)

    def status(self):
        config = self.configuration()
        state = self._state()
        test_lock = RunLock(self.operations / "runner.lock")
        unlocked = test_lock.acquire()
        try:
            if state["running"] and unlocked:
                with self._state_lock():
                    state = self._state()
                    if state["running"]:
                        for record in state["runs"]:
                            if record["status"] == "running":
                                record.update(status="interrupted", finished_at=iso(), error="上次进程中断；旧快照仍保留，可恢复一次或手动检查")
                        state.update(running=False, last_error="上次检查中断")
                        atomic_json(self.state_path, state)
        finally:
            if unlocked:
                test_lock.release()
        catalogue = self.store.catalogue()["references"]
        pending = sum(row.get("analysis_status") == "pending" for row in catalogue)
        updates = [{"reference_id": r["id"], "title": r["title"], "status": r.get("last_check_status"), "checked_at": r.get("last_attempt"), "error": r.get("last_error"), "analysis_status": r.get("analysis_status")} for r in catalogue if r.get("last_attempt")]
        return {**config, "next_run": self.next_run(config), "last_attempt": state["last_attempt"], "last_success": state["last_success"], "last_error": state["last_error"], "running": bool(state["running"] and not unlocked), "pending_analysis": pending, "runs": state["runs"][-30:][::-1], "updates": sorted(updates, key=lambda u: u["checked_at"], reverse=True), "discovery": read_json(self.discovery_path, {"candidates": []}), "acceptance_completed": state.get("acceptance_completed", False), "dependency": "本机与 Codex 需可执行；每日 09:00 唤醒后按此处频率和暂停状态执行，恢复最多补跑一次"}

    def start(self, force=True, trigger="manual", acceptance=False):
        job = self._prepare(force, trigger, acceptance)
        if not job.get("started"):
            return job
        thread = threading.Thread(target=self._execute, args=(job["record"], job["lock"], acceptance), daemon=True)
        thread.start()
        return {"started": True, "job_id": job["record"]["id"]}

    def run(self, force=False, trigger="codex_heartbeat", acceptance=False):
        job = self._prepare(force, trigger, acceptance)
        if not job.get("started"):
            return job
        return self._execute(job["record"], job["lock"], acceptance)

    def _prepare(self, force, trigger, acceptance):
        lock = RunLock(self.operations / "runner.lock")
        if not lock.acquire():
            return {"started": False, "reason": "busy"}
        try:
            due = self.due()
            state = self._state()
            if acceptance and state.get("acceptance_completed"):
                lock.release()
                return {"started": False, "reason": "acceptance_already_completed"}
            if not force and not due["due"]:
                lock.release()
                return {"started": False, **due}
            record = {"id": "RUN-" + uuid.uuid4().hex[:12], "trigger": trigger, "status": "running", "started_at": iso(), "finished_at": None, "unchanged": 0, "changed": 0, "failed": 0, "discovered": 0, "errors": [], "period": None if force else due["period"]}
            with self._state_lock():
                state = self._state()
                for prior in state["runs"]:
                    if prior["status"] == "running":
                        prior.update(status="interrupted", finished_at=iso())
                if record["period"]:
                    state["attempts"][record["period"]] = state["attempts"].get(record["period"], 0) + 1
                state["runs"].append(record)
                state["runs"] = state["runs"][-60:]
                state.update(running=True, last_attempt=record["started_at"])
                atomic_json(self.state_path, state)
            return {"started": True, "record": record, "lock": lock}
        except Exception:
            lock.release()
            raise

    def _execute(self, record, lock, acceptance=False):
        budget = Budget()
        try:
            client = self.client_factory(budget)
            references = [r for r in self.store.catalogue()["references"] if r.get("followed")]
            for item in references:
                try:
                    budget.check()
                    old = item["source"]
                    source, raw = client.fetch_file(old["repository"], old["path"], old.get("tracked_ref") or None, old.get("extraction"), allow_archive_cache=False)
                    if old.get("extraction", {}).get("type") in ("lines", "notebook_cells") and source["commit"] != old["commit"] and source.get("tracking_full_sha256") != old.get("tracking_full_sha256"):
                        raise SourceError("按行号或单元位置节选的上游内容已变化，需要核对范围；旧快照保留")
                    full_unchanged = source.get("tracking_full_sha256") == old.get("tracking_full_sha256")
                    permission_check = None
                    permission_error = None
                    if source["commit"] != old["commit"] and full_unchanged and old.get("license_status") == "allowed":
                        if hasattr(client, "check_tracked_license"):
                            try:
                                permission_check = client.check_tracked_license(old, source)
                            except (ValueError, OSError, TimeoutError) as error:
                                permission_error = error
                                permission_check = {"matches": False, "status": "failed", "reason": "许可文件核对失败：" + str(error), "checked_at": iso()}
                        else:
                            permission_check = {"matches": False, "status": "unknown", "reason": "当前客户端未提供许可文件复核，需人工核验", "checked_at": iso()}
                    if source["commit"] == old["commit"] or full_unchanged:
                        source = {**old, **source}
                        for field in ("license", "license_status", "license_evidence", "license_file_url", "license_path", "license_file", "license_text", "notice_file", "notice_text", "complete_source_file", "source_span", "author"):
                            if old.get(field) is not None:
                                source[field] = old[field]
                        if permission_check:
                            source["license_check"] = permission_check
                            if permission_check["matches"]:
                                source["license_file_url"] = permission_check.get("license_file_url", source.get("license_file_url"))
                                source["license_evidence"] = permission_check["reason"]
                            else:
                                source["license_status"] = "unknown"
                                source["license_evidence"] = permission_check["reason"]
                    else:
                        source["license_status"] = "unknown"
                        source["license_evidence"] = "上游版本已变化，需要重新核对文件许可与第三方内容"
                        if old.get("source_span"):
                            source["source_span"] = old["source_span"]
                    result = self.store.ingest(source, raw, {"check_status": "failed", "check_error": str(permission_error)} if permission_error else {})
                    if permission_error:
                        raise permission_error
                    status = "changed" if result["changed"] else "unchanged"
                    self.store.record_check(item["id"], status, iso())
                    record[status] += 1
                except (ValueError, OSError, TimeoutError) as error:
                    self.store.record_check(item["id"], "failed", iso(), str(error))
                    record["failed"] += 1
                    record["errors"].append({"reference_id": item["id"], "error": str(error)})
                    if isinstance(error, BudgetExceeded) or "限流" in str(error):
                        record["stopped_reason"] = str(error)
                        break
            discovery_due = self.configuration()["frequency"] == "weekly" or now().weekday() == 6
            if discovery_due and not acceptance and not record.get("stopped_reason"):
                discovered = read_json(self.discovery_path, {"candidates": [], "last_success": None})
                candidates = {c["repository"]: c for c in discovered["candidates"]}
                for category in ("ui_design", "taste", "visual"):
                    try:
                        results = client.search(category_id=category, max_results=4)
                        for candidate in results["candidates"]:
                            if candidate["repository"] not in candidates:
                                record["discovered"] += 1
                            candidates[candidate["repository"]] = candidate
                    except (ValueError, OSError) as error:
                        record["errors"].append({"stage": "discovery", "category_id": category, "error": str(error)})
                        if isinstance(error, BudgetExceeded) or "限流" in str(error):
                            record["stopped_reason"] = str(error)
                            break
                discovered.update(candidates=list(candidates.values())[-60:], last_attempt=iso())
                if not any(e.get("stage") == "discovery" for e in record["errors"]):
                    discovered["last_success"] = iso()
                atomic_json(self.discovery_path, discovered)
            record["status"] = "partial" if record["errors"] and record["changed"] + record["unchanged"] else "failed" if record["errors"] else "success"
        except Exception as error:
            record.update(status="failed")
            record["errors"].append({"stage": "runner", "error": str(error)})
        finally:
            record.update(finished_at=iso(), file_attempts=budget.file_attempts, repositories_checked=len(budget.repositories), network_requests=budget.requests)
            try:
                with self._state_lock():
                    state = self._state()
                    state["runs"] = [record if r["id"] == record["id"] else r for r in state["runs"]]
                    state["running"] = False
                    state["last_error"] = record["errors"][0]["error"] if record["errors"] else None
                    if record["status"] == "success":
                        state["last_success"] = record["finished_at"]
                        if record["period"]:
                            state["periods"] = (state["periods"] + [record["period"]])[-60:]
                    if acceptance:
                        state["acceptance_completed"] = record["status"] == "success"
                    atomic_json(self.state_path, state)
            finally:
                lock.release()
        return {"started": True, **record, "pending_analysis": self.status()["pending_analysis"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status", "due", "run", "pending", "register", "analyze"])
    parser.add_argument("--root", "--data-root", dest="root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--acceptance", action="store_true")
    parser.add_argument("--trigger", default="codex_heartbeat")
    parser.add_argument("--automation-id")
    parser.add_argument("--reference-id")
    parser.add_argument("--snapshot-id")
    parser.add_argument("--analysis-file", type=Path)
    args = parser.parse_args()
    runner = ReferenceRunner(args.root)
    if args.command == "status":
        result = runner.status()
    elif args.command == "due":
        result = runner.due()
    elif args.command == "run":
        result = runner.run(args.force, args.trigger, args.acceptance)
    elif args.command == "register":
        if not args.automation_id:
            parser.error("register 需要 --automation-id")
        result = runner.register(args.automation_id)
    elif args.command == "pending":
        result = {"references": [row for row in runner.store.catalogue()["references"] if row.get("analysis_status") == "pending"][:6]}
    else:
        if not args.reference_id or not args.snapshot_id or not args.analysis_file:
            parser.error("analyze 需要参考编号、快照编号和实际分析 JSON 文件")
        result = runner.store.set_analysis(args.reference_id, args.snapshot_id, read_json(args.analysis_file, {}))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
