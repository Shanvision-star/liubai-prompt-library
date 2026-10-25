"""提示词与参考库的本机服务：原文读取、显式采用与受控来源检查。"""

import argparse
import json
import logging
import mimetypes
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qs

from reference_service import ReferenceService
from prompt_store import PromptStore
from library_init import ensure_library
from integration_auth import integration_token

APP_ID = "prompt-library-desktop"
WEB_ROOT = Path(__file__).parent / "web"
ENTRY_ID = re.compile(r"PRM-\d{4,}")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def prompt_body(markdown):
    match = re.search(r"```(?:text|plaintext)?\s*\n(.*?)\n```", markdown, re.S)
    return match.group(1).strip() if match else markdown.strip()


class Library:
    """从已有索引取材；任何元数据路径都必须留在素材库内。"""

    def __init__(self, root, state_dir=None):
        self.root = Path(root).resolve()
        ensure_library(self.root)
        self.state_dir = Path(state_dir or self.root / "desktop" / ".runtime").resolve()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.favorite_path = self.state_dir / "favorites.json"
        self.lock = threading.Lock()

    def contained_path(self, relative):
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError("素材路径越出了库目录")
        return target

    def index_entries(self):
        return read_json(self.root / "index.json")["entries"]

    def favorites(self):
        if not self.favorite_path.exists():
            return []
        stored = read_json(self.favorite_path)
        if not isinstance(stored, list) or not all(isinstance(x, str) for x in stored):
            raise ValueError("收藏文件格式异常，请保留文件并检查")
        return stored

    def entry(self, entry_id, version=None):
        if not ENTRY_ID.fullmatch(entry_id):
            raise KeyError("素材编号无效")
        item = next((x for x in self.index_entries() if x["id"] == entry_id), None)
        if item is None:
            raise KeyError("找不到这条素材")
        record_path = self.contained_path(item["record_file"])
        record = read_json(record_path)
        folder = record_path.parent

        def content(name, default=""):
            if not name:
                return default
            path = self.contained_path(str((folder / name).relative_to(self.root)))
            with path.open(encoding="utf-8-sig", newline="") as file:
                return file.read()

        selected_version = version or item.get("latest_version")
        chosen = next((v for v in record.get("versions", []) if v["version"] == selected_version), None)
        if version:
            if not chosen:
                raise KeyError("找不到这个优化版本")
            optimized_md = content(chosen["file"])
        else:
            with self.contained_path(item["optimized_file"]).open(encoding="utf-8-sig", newline="") as file:
                optimized_md = file.read()
        chosen = chosen or {}
        is_latest = selected_version == item.get("latest_version")
        analysis_file = chosen.get("analysis_file") or (record.get("design_analysis_file") if is_latest else None)
        source_file = chosen.get("source_file") or record.get("source", {}).get("provenance_file")
        loop = chosen.get("loop_review")
        if loop is None:
            latest_loop = record.get("loop_review", {})
            loop = latest_loop if is_latest or latest_loop.get("reviewed_version") == selected_version else {}
        return {
            "item": item, "record": record, "selected_version": selected_version,
            "original": content(record["original"]["file"]),
            "optimized_markdown": optimized_md, "optimized": optimized_md if chosen.get("optimization_status") in {"not_optimized", "provided"} or chosen.get("reference_provenance") else prompt_body(optimized_md),
            "analysis": content(analysis_file, "此历史版本未单独保存设计分析。" if not is_latest else ""),
            "source_markdown": content(source_file),
            "loop": loop,
        }

    def catalogue(self):
        rows = []
        for item in self.index_entries():
            entry = self.entry(item["id"])
            record = entry["record"]
            source = record.get("source", {})
            rows.append({
                **item, "source_label": source.get("repository") or "我的原创素材",
                "search_text": "\n".join([entry["original"], entry["optimized"], entry["analysis"]]),
            })
        valid_ids = {e["id"] for e in rows}
        return {
            "app": APP_ID, "entries": rows,
            "categories": read_json(self.root / "taxonomy.json")["categories"],
            "favorites": [f for f in self.favorites() if f in valid_ids],
            "entry_count": len(rows),
        }

    def set_favorite(self, entry_id, favorite):
        self.entry(entry_id)
        if type(favorite) is not bool:
            raise ValueError("收藏状态必须是布尔值")
        with self.lock:
            saved = set(self.favorites())
            saved.add(entry_id) if favorite else saved.discard(entry_id)
            result = sorted(saved)
            temporary = self.favorite_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
            temporary.replace(self.favorite_path)
        return result


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, library):
        self.library = library
        self.references = ReferenceService(library)
        self.prompts = PromptStore(library.root)
        self.api_token = integration_token(library.state_dir)
        super().__init__(address, RequestHandler)


class RequestHandler(BaseHTTPRequestHandler):
    """仅提供白名单资源；浏览器同源写入与本机令牌集成分别校验。"""

    def log_message(self, fmt, *args):
        logging.info(fmt, *args)

    def reply(self, status, content, mime="application/json; charset=utf-8", filename=None):
        payload = json.dumps(content, ensure_ascii=False).encode("utf-8") if isinstance(content, (dict, list)) else content
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(payload)

    def valid_host(self):
        return self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def do_GET(self):
        if not self.valid_host():
            return self.reply(403, {"error": "仅允许本机入口"})
        path = unquote(urlsplit(self.path).path)
        query = parse_qs(urlsplit(self.path).query)
        version = query.get("version", [None])[0]
        snapshot = query.get("snapshot", [None])[0]
        try:
            if path == "/api/health":
                return self.reply(200, {"app": APP_ID, "library_root": str(self.server.library.root), "version": "0.3.0"})
            if path == "/api/library":
                return self.reply(200, self.server.library.catalogue())
            if path == "/api/categories":
                return self.reply(200, {"categories": self.server.prompts.categories()})
            if path == "/api/integrations":
                return self.reply(200, {
                    "api_version": "1", "save_endpoint": "/api/prompts", "local_only": True,
                    "authentication": "同源浏览器，或非浏览器客户端使用本机Bearer令牌",
                    "token_file": str(self.server.library.state_dir / "api-token"),
                    "mcp": {"transport": "stdio", "entrypoint": "desktop/mcp_server.py", "connection_state": "client_managed", "description": "MCP客户端配置并连接；服务存在不代表当前Codex会话已连接"},
                })
            if path.startswith("/api/entries/"):
                return self.reply(200, self.server.library.entry(path.removeprefix("/api/entries/"), version))
            if path == "/api/references":
                return self.reply(200, self.server.references.catalogue())
            if path == "/api/references/status":
                return self.reply(200, self.server.references.runner.status())
            if path.startswith("/api/references/related/"):
                entry_id = path.removeprefix("/api/references/related/")
                return self.reply(200, {"references": self.server.references.store.recommendations(entry_id, limit=3)})
            if re.fullmatch(r"/api/references/REF-\d{4,}", path):
                return self.reply(200, self.server.references.store.detail(path.rsplit("/", 1)[1], snapshot))
            reference_download = re.fullmatch(r"/download/reference/(REF-\d{4,})/(original|card|template)", path)
            if reference_download:
                ref_id, variant = reference_download.groups()
                return self.reply(200, self.server.references.download(ref_id, variant, snapshot), "text/markdown; charset=utf-8", f"{ref_id}-{variant}.md")
            download = re.fullmatch(r"/download/(PRM-\d{4,})/(original|optimized)", path)
            if download:
                entry_id, variant = download.groups()
                entry = self.server.library.entry(entry_id, version)
                item = entry["item"]
                relative = item["original_file"] if variant == "original" else item["optimized_file"]
                if variant == "optimized" and version:
                    chosen = next(v for v in entry["record"]["versions"] if v["version"] == version)
                    relative = str(Path(item["record_file"]).parent / chosen["file"])
                data = self.server.library.contained_path(relative).read_bytes()
                return self.reply(200, data, "text/markdown; charset=utf-8", f"{entry_id}-{variant}{'-'+version if version and variant=='optimized' else ''}.md")
            static = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css", "/icon.svg": "icon.svg", "/references.js": "references.js", "/references.css": "references.css", "/prompts.js": "prompts.js", "/prompts.css": "prompts.css"}
            if path in static:
                file = WEB_ROOT / static[path]
                mime = {".js": "text/javascript", ".css": "text/css", ".html": "text/html", ".svg": "image/svg+xml"}.get(file.suffix, mimetypes.guess_type(file.name)[0])
                return self.reply(200, file.read_bytes(), mime + "; charset=utf-8")
            return self.reply(404, {"error": "找不到这个页面"})
        except KeyError:
            self.reply(404, {"error": "找不到这条素材，请刷新列表"})
        except ValueError as error:
            self.reply(400, {"error": str(error)})
        except (OSError, TimeoutError) as error:
            logging.exception("读取素材失败")
            self.reply(500, {"error": f"读取素材失败：{error}"})

    def do_POST(self):
        origin = self.headers.get("Origin")
        allowed_origins = {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}
        metadata_route = re.fullmatch(r"/api/entries/(PRM-\d{4,})/metadata", self.path)
        integration_route = self.path in {"/api/prompts", "/api/categories"} or bool(metadata_route)
        browser_allowed = origin in allowed_origins and self.headers.get("X-Prompt-Library") == "1"
        authorization = self.headers.get("Authorization", "")
        supplied_token = authorization.removeprefix("Bearer ")
        token_allowed = integration_route and origin is None and authorization.startswith("Bearer ") and secrets.compare_digest(supplied_token.encode("utf-8"), self.server.api_token.encode("utf-8"))
        if not self.valid_host() or not (browser_allowed or token_allowed):
            return self.reply(403, {"error": "请从本机素材库操作，或为本机API提供有效的Bearer令牌"})
        routes = {"/api/favorites", "/api/references/flags", "/api/references/discover", "/api/references/import", "/api/references/adopt-preview", "/api/references/adopt", "/api/references/check", "/api/references/schedule"}
        if self.path not in routes and not integration_route:
            return self.reply(404, {"error": "未知操作"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > (2 * 1024 * 1024 if integration_route else 16384):
                raise ValueError("请求大小不正确")
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                raise ValueError("需要 JSON 请求")
            body = json.loads(self.rfile.read(size).decode("utf-8"))
            if not isinstance(body, dict):
                raise ValueError("请求需要 JSON 对象")
            references = self.server.references
            if self.path == "/api/prompts":
                result = self.server.prompts.save_prompt(body)
            elif self.path == "/api/categories":
                if set(body) - {"name", "description"}:
                    raise ValueError("分类只接受名称和说明")
                result = self.server.prompts.create_category(body.get("name"), body.get("description", ""))
            elif metadata_route:
                result = self.server.prompts.update_metadata(metadata_route[1], body)
            elif self.path == "/api/favorites":
                if not isinstance(body.get("id"), str):
                    raise ValueError("素材编号缺失")
                result = {"favorites": self.server.library.set_favorite(body["id"], body.get("favorite"))}
            elif self.path == "/api/references/flags":
                result = {"item": references.store.set_flags(body.get("id"), favorite=body.get("favorite"), followed=body.get("followed"))}
            elif self.path == "/api/references/discover":
                result = references.discover(body)
            elif self.path == "/api/references/import":
                result = references.import_url(body)
            elif self.path == "/api/references/adopt-preview":
                result = references.store.adoption_preview(body.get("id"), body.get("target_id") or None)
            elif self.path == "/api/references/adopt":
                result = references.store.adopt(body.get("id"), target_id=body.get("target_id") or None, expected_snapshot=body.get("expected_snapshot"), expected_analysis_version=body.get("expected_analysis_version"))
            elif self.path == "/api/references/check":
                result = references.runner.start(force=True, trigger="manual")
            else:
                result = references.runner.configure(body)
            self.reply(200, result)
        except KeyError:
            self.reply(404, {"error": "找不到这条素材"})
        except (ValueError, UnicodeError) as error:
            self.reply(400, {"error": str(error)})
        except (OSError, TimeoutError):
            logging.exception("本机操作未完成")
            self.reply(500, {"error": "本机操作未完成，请检查目录权限或稍后重试；已有资料仍保留"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--data-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--state-dir", type=Path)
    args = parser.parse_args()
    library = Library(args.data_root, args.state_dir)
    logging.basicConfig(filename=library.state_dir / "server.log", encoding="utf-8", level=logging.INFO, format="%(asctime)s %(message)s")
    server = LocalServer(("127.0.0.1", args.port), library)
    if server.references.runner.due()["due"]:
        server.references.runner.start(force=False, trigger="startup_catch_up")
    logging.info("服务启动 http://127.0.0.1:%s", server.server_port)
    server.serve_forever()


if __name__ == "__main__":
    main()
