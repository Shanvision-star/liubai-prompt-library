"""只读 GitHub 来源客户端：固定版本、受限抓取、条件缓存与可追溯范围提取。"""

import base64
import ast
import hashlib
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit, unquote
from urllib.request import Request, build_opener, HTTPRedirectHandler

TZ = timezone(timedelta(hours=8))
TEXT_SUFFIXES = {".md", ".txt", ".json", ".ipynb", ".yaml", ".yml", ".prompt", ".jinja", ".jinja2", ".toml", ".py", ".js", ".ts"}
SEARCH_TERMS = {
    "development": "coding agent prompt", "ui_design": "frontend design skills", "llm_design": "LLM prompt evaluation",
    "langchain_design": "langchain prompt templates", "taste": "design taste skill", "product": "product requirements prompt",
    "business": "business prompt templates", "writing": "writing prompt templates", "visual": "video generation prompt",
    "learning": "learning prompt templates", "productivity": "productivity prompt templates", "general": "prompt templates", "uncategorized": "prompt templates",
}


def now_iso():
    return datetime.now(TZ).isoformat(timespec="seconds")


class SourceError(ValueError):
    """可直接展示给用户的来源错误，不包含认证值。"""


class BudgetExceeded(SourceError):
    pass


class Budget:
    def __init__(self, max_repositories=20, max_files=60, max_bytes=256 * 1024, max_seconds=900):
        self.max_repositories = max_repositories
        self.max_files = max_files
        self.max_bytes = max_bytes
        self.max_seconds = max_seconds
        self.repositories = set()
        self.file_attempts = 0
        self.requests = 0
        self.started = time.monotonic()

    def check(self, repository=None, file_attempt=False):
        if time.monotonic() - self.started >= self.max_seconds:
            raise BudgetExceeded("达到本次运行时间上限，未完成内容保留到下一次")
        if repository:
            if repository not in self.repositories and len(self.repositories) >= self.max_repositories:
                raise BudgetExceeded("达到本次仓库数量上限")
            self.repositories.add(repository)
        if file_attempt:
            if self.file_attempts >= self.max_files:
                raise BudgetExceeded("达到本次文件检查额度（含重试）")
            self.file_attempts += 1


class GitHubRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname not in {"api.github.com", "raw.githubusercontent.com"}:
            raise SourceError("来源重定向到不支持的地址，已停止读取")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if parsed.hostname != "api.github.com":
            redirected.remove_header("Authorization")
        return redirected


class GitHubClient:
    """凭据仅从环境读取；磁盘缓存只保存公开响应与 ETag。"""

    def __init__(self, cache_dir, budget=None, opener=None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.budget = budget or Budget()
        self.opener = opener or build_opener(GitHubRedirect())
        self.repository_cache = {}
        self.commit_cache = {}
        self.license_cache = {}

    @staticmethod
    def validate_repository(repository):
        if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise SourceError("需要有效的 GitHub owner/repository")
        return repository

    def request(self, endpoint, *, file_attempt=False, immutable=False, max_bytes=2 * 1024 * 1024, cache_response=True):
        url = "https://api.github.com" + endpoint
        cache = self.cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".json")
        previous = None
        if cache_response and cache.exists():
            try:
                previous = json.loads(cache.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                previous = None
        if immutable and previous:
            self.budget.check(file_attempt=file_attempt)
            return previous["body"]
        for attempt in range(3):
            self.budget.check(file_attempt=file_attempt)
            self.budget.requests += 1
            headers = {"User-Agent": "Liubai-Reference-Library/0.2", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
            token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
            if token:
                headers["Authorization"] = "Bearer " + token
            if previous and previous.get("etag"):
                headers["If-None-Match"] = previous["etag"]
            try:
                remaining = self.budget.max_seconds - (time.monotonic() - self.budget.started)
                with self.opener.open(Request(url, headers=headers), timeout=max(0.1, min(20, remaining))) as response:
                    raw = response.read(max_bytes + 1)
                    if len(raw) > max_bytes:
                        raise BudgetExceeded("GitHub 响应超过读取上限，请缩小来源范围")
                    body = json.loads(raw)
                    payload = {"url": url, "etag": response.headers.get("ETag"), "fetched_at": now_iso(), "body": body}
                    if cache_response:
                        temporary = cache.with_suffix(".tmp-" + uuid.uuid4().hex)
                        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                        temporary.replace(cache)
                    return body
            except HTTPError as error:
                if error.code == 304 and previous:
                    return previous["body"]
                if error.code in (403, 429):
                    reset = error.headers.get("X-RateLimit-Reset")
                    suffix = "；请稍后重试"
                    if reset and reset.isdigit():
                        suffix = "；可重试时间 " + datetime.fromtimestamp(int(reset), TZ).strftime("%m-%d %H:%M")
                    raise SourceError("GitHub 暂时限流或拒绝访问" + suffix) from None
                if error.code == 404:
                    raise SourceError("GitHub 来源不存在、已移动或当前无权读取") from None
                if error.code < 500 or attempt == 2:
                    raise SourceError(f"GitHub 读取失败（HTTP {error.code}）") from None
            except (URLError, TimeoutError, OSError) as error:
                if attempt == 2:
                    raise SourceError("GitHub 网络读取失败，请检查连接后重试") from None
            if attempt < 2:
                time.sleep(min(2 ** attempt, 2))
        raise SourceError("来源读取未完成")

    def repository(self, repository):
        self.validate_repository(repository)
        self.budget.check(repository=repository)
        if repository not in self.repository_cache:
            self.repository_cache[repository] = self.request("/repos/" + repository)
        return self.repository_cache[repository]

    def resolve_commit(self, repository, ref):
        if re.fullmatch(r"[0-9a-fA-F]{40}", ref):
            return ref.lower()
        key = (repository, ref)
        if key not in self.commit_cache:
            # commits 响应可能含源文件 patch，未核对许可时不得将正文写入缓存。
            commit = self.request(f"/repos/{repository}/commits/{quote(ref, safe='')}", cache_response=False)
            self.commit_cache[key] = commit["sha"]
        return self.commit_cache[key]

    def search(self, query="", category_id="general", max_results=8):
        if not isinstance(query, str) or len(query) > 300:
            raise SourceError("搜索词需在 300 字以内")
        phrase = query.strip() or SEARCH_TERMS.get(category_id, SEARCH_TERMS["general"])
        q = phrase + " archived:false"
        data = self.request("/search/repositories?" + urlencode({"q": q, "sort": "updated", "per_page": min(max_results, 20)}))
        candidates = []
        for repo in data.get("items", []):
            candidates.append({
                "repository": repo["full_name"], "title": repo["full_name"], "description": repo.get("description") or "",
                "url": repo["html_url"], "stars": repo.get("stargazers_count", 0), "updated_at": repo.get("pushed_at"),
                "license": (repo.get("license") or {}).get("spdx_id") or "unknown", "category_id": category_id,
                "reason": "GitHub 关键词匹配；尚需核对具体文件、许可和任务适用性", "selection_status": "candidate",
            })
        return {"candidates": candidates, "query": phrase, "total_count": data.get("total_count", len(candidates)), "searched_at": now_iso()}

    @staticmethod
    def parse_url(url):
        if not isinstance(url, str) or len(url) > 2048:
            raise SourceError("请提供 GitHub 仓库或文件链接")
        parsed = urlsplit(url.strip())
        if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username or parsed.password or parsed.port:
            raise SourceError("目前仅接收 https://github.com 的仓库或文件链接")
        parts = [unquote(v) for v in parsed.path.strip("/").split("/")]
        if len(parts) < 2 or any(v in (".", "..") for v in parts):
            raise SourceError("GitHub 链接格式不正确")
        repository = GitHubClient.validate_repository("/".join(parts[:2]))
        if len(parts) == 2:
            return repository, None, None, None
        if len(parts) < 5 or parts[2] not in ("blob", "tree"):
            raise SourceError("请粘贴仓库首页，或包含 blob/版本/文件路径 的链接")
        extraction = None
        match = re.fullmatch(r"L(\d+)(?:-L(\d+))?", parsed.fragment)
        if match:
            extraction = {"type": "lines", "start": int(match[1]), "end": int(match[2] or match[1])}
        return repository, parts[3], "/".join(parts[4:]), extraction

    def candidate_files(self, repository):
        repo = self.repository(repository)
        ref = repo["default_branch"]
        commit = self.resolve_commit(repository, ref)
        tree = self.request(f"/repos/{repository}/git/trees/{commit}?recursive=1", immutable=True)
        files = []
        for node in tree.get("tree", []):
            path = node["path"]
            low = path.lower()
            if node["type"] != "blob" or node.get("size", 0) > self.budget.max_bytes:
                continue
            if Path(path).suffix.lower() not in TEXT_SUFFIXES:
                continue
            score = sum(word in low for word in ("prompt", "skill", "guide", "design", "example", "workflow", "readme"))
            if score and not any(part in low.split("/") for part in ("node_modules", "vendor", ".git", "dist")):
                files.append({"path": path, "title": path, "url": f"https://github.com/{repository}/blob/{quote(ref, safe='')}/{quote(path, safe='/')}", "size": node.get("size", 0), "rank": score})
        files.sort(key=lambda f: (-f["rank"], len(f["path"])))
        return {"choose_file": True, "repository": repository, "candidates": files[:30], "truncated": bool(tree.get("truncated")), "reason": "选择实际指令或设计说明文件；仓库许可证仍需核对到具体材料"}

    @staticmethod
    def extract(data, extraction):
        data.decode("utf-8-sig")
        if not extraction:
            return data
        if extraction.get("type") == "python_literal":
            try:
                tree = ast.parse(data.decode("utf-8-sig"))
                for node in tree.body:
                    names = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
                    if any(isinstance(name, ast.Name) and name.id == extraction.get("name") for name in names):
                        value = ast.literal_eval(node.value)
                        if isinstance(value, str):
                            return value.encode("utf-8")
            except (ValueError, SyntaxError, TypeError):
                pass
            raise SourceError("原提示词常量已变化或不再是静态字符串，需要重新核对")
        if extraction.get("type") == "notebook_cells":
            notebook = json.loads(data.decode("utf-8-sig"))
            indexes = extraction.get("indexes")
            cells = notebook.get("cells", [])
            if not isinstance(indexes, list) or not indexes or any(type(i) is not int or i < 0 or i >= len(cells) for i in indexes):
                raise SourceError("Notebook 原文单元范围失效，需要重新核对")
            selected = []
            for i in indexes:
                source = cells[i].get("source", [])
                selected.append(source if isinstance(source, str) else "".join(source))
            return "\n".join(selected).encode("utf-8")
        lines = data.splitlines(keepends=True)
        if extraction.get("type") == "lines":
            start, end = extraction.get("start"), extraction.get("end")
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
                raise SourceError("原文节选范围已经失效，需要重新核对")
            return b"".join(lines[start - 1:end])
        if extraction.get("type") == "heading":
            heading = extraction.get("heading", "").strip()
            level = extraction.get("level")
            start = None
            for i, line in enumerate(lines):
                text = line.decode("utf-8-sig").strip()
                match = re.match(r"^(#{1,6})\s+(.+)$", text)
                if match and (text == heading or match[2].strip().rstrip("#").strip() == heading):
                    start, level = i, len(match[1])
                    break
            if start is None:
                raise SourceError("原节选标题已变化，需要人工核对；旧快照仍保留")
            end = len(lines)
            for i in range(start + 1, len(lines)):
                match = re.match(rb"^(#{1,6})\s+", lines[i])
                if match and len(match[1]) <= level:
                    end = i
                    break
            return b"".join(lines[start:end])
        raise SourceError("不支持的原文节选方式")

    def fetch_file(self, repository, path, ref=None, extraction=None, allow_archive_cache=False):
        repo = self.repository(repository)
        repository = repo.get("full_name", repository)
        if not path or ".." in Path(path).parts or path.startswith(("/", "\\")):
            raise SourceError("来源文件路径不正确")
        tracked_ref = ref or repo["default_branch"]
        commit = self.resolve_commit(repository, tracked_ref)
        endpoint = f"/repos/{repository}/contents/{quote(path, safe='/')}?ref={commit}"
        file = self.request(endpoint, file_attempt=True, immutable=True, max_bytes=512 * 1024, cache_response=allow_archive_cache)
        if not isinstance(file, dict) or file.get("type") != "file":
            raise SourceError("请选择具体文本文件")
        if file.get("size", 0) > self.budget.max_bytes or file.get("encoding") != "base64":
            raise BudgetExceeded("文件超过 256 KiB 上限或不是可读取的文本")
        data = base64.b64decode(file["content"])
        if len(data) > self.budget.max_bytes:
            raise BudgetExceeded("原文件超过单文件上限")
        try:
            selected = self.extract(data, extraction)
        except UnicodeError:
            raise SourceError("该文件不是 UTF-8 文本；不会下载或运行媒体、模型或二进制文件") from None
        license_id = (repo.get("license") or {}).get("spdx_id") or "unknown"
        source = {
            "repository": repo.get("full_name", repository), "path": path, "commit": commit,
            "tracked_ref": tracked_ref, "url": f"https://github.com/{repository}/blob/{commit}/{quote(path, safe='/')}",
            "retrieved_at": now_iso(), "license": license_id, "license_status": "unknown",
            "license_evidence": "仓库许可仅作线索，具体文件与第三方内容需经核对后才能采用",
            "tracking_full_sha256": hashlib.sha256(data).hexdigest(),
            "repository_metadata": {"stars": repo.get("stargazers_count"), "archived": repo.get("archived"), "pushed_at": repo.get("pushed_at"), "default_branch": repo.get("default_branch")},
        }
        if extraction:
            source.update(extraction=extraction, archived_content="excerpt")
        else:
            source["archived_content"] = "complete_file"
        return source, selected

    def check_tracked_license(self, old_source, new_source):
        """比较已核验许可与新提交中的同一文件；新许可正文仅在内存中短暂保留。"""
        result = {"matches": False, "status": "unknown", "checked_at": now_iso()}
        if old_source.get("license_status") != "allowed":
            return {**result, "reason": "此前许可未确认，仍需人工核验"}
        if old_source.get("commit") == new_source.get("commit"):
            return {**result, "matches": True, "status": "unchanged", "reason": "相同固定提交，沿用已核验许可"}
        text = old_source.get("license_text")
        url = old_source.get("license_file_url")
        if not isinstance(text, str) or not text or not isinstance(url, str):
            return {**result, "reason": "缺少已核验的许可原文或固定版本链接，无法自动继承许可"}
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port:
            return {**result, "reason": "许可链接不是可核验的 GitHub 固定版本"}
        parts = [unquote(part) for part in parsed.path.strip("/").split("/")]
        if parsed.hostname == "github.com" and len(parts) >= 5 and parts[2] == "blob":
            license_repository, license_commit, path = "/".join(parts[:2]), parts[3], "/".join(parts[4:])
        elif parsed.hostname == "raw.githubusercontent.com" and len(parts) >= 4:
            license_repository, license_commit, path = "/".join(parts[:2]), parts[2], "/".join(parts[3:])
        else:
            return {**result, "reason": "许可链接需要定位到仓库内的固定版本文件"}
        repository = new_source.get("repository", "")
        commit = new_source.get("commit", "")
        if (license_repository.lower() != repository.lower() or license_repository.lower() != old_source.get("repository", "").lower()
                or not re.fullmatch(r"[0-9a-fA-F]{40}", license_commit) or not re.fullmatch(r"[0-9a-fA-F]{40}", commit)
                or ".." in path.split("/") or "\\" in path or path.startswith("/")):
            return {**result, "reason": "许可文件不属于同一仓库的可追溯固定版本，需要人工核对"}
        key = (repository.lower(), commit, path)
        if key not in self.license_cache:
            self.budget.check(repository=repository)
            endpoint = f"/repos/{repository}/contents/{quote(path, safe='/')}?ref={commit}"
            file = self.request(endpoint, file_attempt=True, immutable=True, max_bytes=512 * 1024, cache_response=False)
            if not isinstance(file, dict) or file.get("type") != "file" or file.get("encoding") != "base64":
                raise SourceError("新版许可文件不存在或不是可核验的文本")
            if file.get("size", 0) > self.budget.max_bytes:
                raise BudgetExceeded("新版许可文件超过单文件上限，需人工核对")
            try:
                payload = base64.b64decode(file["content"])
                payload.decode("utf-8-sig")
            except (ValueError, UnicodeError, KeyError):
                raise SourceError("新版许可文件无法按 UTF-8 文本核对") from None
            if len(payload) > self.budget.max_bytes:
                raise BudgetExceeded("新版许可文件超过单文件上限，需人工核对")
            self.license_cache[key] = payload
        payload = self.license_cache[key]
        same = payload == text.encode("utf-8")
        return {
            **result, "matches": same, "status": "unchanged" if same else "changed",
            "reason": "已核对新提交的许可文件，与已存许可逐字节一致" if same else "许可文件内容发生变化，须重新核验使用范围",
            "license_file_url": f"https://github.com/{repository}/blob/{commit}/{quote(path, safe='/')}",
            "license_sha256": hashlib.sha256(payload).hexdigest(),
        }

    def import_url(self, url):
        repository, ref, path, extraction = self.parse_url(url)
        if path is None:
            return self.candidate_files(repository)
        source, data = self.fetch_file(repository, path, ref, extraction)
        # 固定 commit 链接仍跟踪默认分支，以便后续发现同一文件的新版本。
        if ref and re.fullmatch(r"[0-9a-fA-F]{40}", ref):
            source["tracked_ref"] = self.repository(repository)["default_branch"]
        return {"source": source, "original": data}
