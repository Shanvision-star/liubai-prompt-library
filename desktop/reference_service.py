"""参考库 HTTP 用例：发现、导入、原文优先导出及统一运行状态。"""

from pathlib import Path
import json
import re

from github_sources import GitHubClient, Budget
from reference_runner import ReferenceRunner


class ReferenceService:
    def __init__(self, library):
        self.library = library
        self.runner = ReferenceRunner(library.root)
        self.store = self.runner.store

    def client(self):
        return GitHubClient(self.library.state_dir / "github-cache", Budget(max_seconds=120))

    def catalogue(self):
        catalogue = self.store.catalogue()
        for item in catalogue["references"]:
            detail = self.store.detail(item["id"])
            item["search_text"] = (detail.get("original") or "") + "\n" + json.dumps(detail.get("analysis") or {}, ensure_ascii=False)
        catalogue["schedule"] = self.runner.status()
        return catalogue

    def discover(self, body):
        query = body.get("query", "")
        category = body.get("category_id") or "general"
        if category == "all":
            category = "general"
        if body.get("entry_id"):
            entry = self.library.entry(body["entry_id"])
            category = entry["item"]["category_id"]
        return self.client().search(query, category)

    def import_url(self, body):
        category = body.get("category_id") or "uncategorized"
        categories = {c["id"] for c in self.store.catalogue()["categories"]}
        if category not in categories:
            raise ValueError("请选择库内分类")
        result = self.client().import_url(body.get("url"))
        if result.get("choose_file"):
            return result
        source = result["source"]
        title = body.get("title") or source["repository"].split("/")[-1] + " · " + Path(source["path"]).name
        if not isinstance(title, str) or len(title) > 250:
            raise ValueError("标题需在 250 字以内")
        metadata = {"title": title, "summary": "从 GitHub 添加的参考候选，待核对具体文件许可与写法。", "category_id": category, "tags": [], "material_type": "skill" if "skill" in source["path"].lower() else "method", "selection_status": "candidate"}
        return self.store.ingest(source, result["original"], metadata)

    def download(self, ref_id, variant, snapshot=None):
        detail = self.store.detail(ref_id, snapshot)
        item = detail["item"]
        selected = detail["snapshot"]
        if variant == "original":
            relative = selected.get("original_file")
            if not relative:
                raise ValueError(selected.get("original_unavailable_reason") or "原文许可尚未确认，暂不能导出")
            path = self.library.contained_path(f"references/{ref_id}/{relative}")
            return path.read_bytes()
        if variant == "template":
            if not detail.get("template"):
                raise ValueError("当前快照尚无已完成的模板拆解")
            return detail["template"].encode("utf-8")
        if variant != "card":
            raise KeyError("导出格式不存在")
        source = selected.get("source") or item["source"]
        original = detail.get("original")
        kind = {"prompt": "提示词原文", "skill": "技能指令原文", "workflow": "工作流原文", "method": "设计方法原文"}.get(item["material_type"], "原文")
        if source.get("extraction"):
            kind += "（节选）"
        text = f"# {item['title']}\n\n来源：{source['url']} · 快照 {selected['id']} · 效果待实测\n\n## {kind}\n\n"
        if original is None:
            text += (selected.get("original_unavailable_reason") or "原文未收录，请查看来源") + "\n"
        else:
            runs = re.findall(r"`+", original)
            fence = "`" * max(3, max((len(r) for r in runs), default=0) + 1)
            text += fence + "text\n" + original + "\n" + fence + "\n"
        provenance = "\n## 来源与许可\n\n" + self._readable({
            "仓库": source["repository"], "文件": source["path"], "固定 commit": selected["commit"],
            "SHA-256": selected["sha256"], "收录范围": source.get("source_span") or source.get("archived_content", "完整文件"),
            "作者或维护方": source.get("author", "见来源仓库"), "许可": source.get("license", "unknown"),
            "许可状态": selected["license_status"], "许可依据": source.get("license_evidence", "尚未核对"),
            "许可文件": source.get("license_file_url", "未提供"), "使用限制": source.get("usage_restrictions", "按来源许可和具体任务核对"),
            "适用模型": source.get("applicable_models", []), "依赖": source.get("dependencies", []),
            "抓取时间": source.get("retrieved_at"), "分析版本": (detail.get("analysis") or {}).get("version", "待分析"),
        }) + "\n"
        analysis = detail.get("analysis")
        if not analysis:
            return (text + "\n## 写法拆解\n\n待分析；没有以固定文案替代实际分析。\n" + provenance).encode("utf-8")
        fields = [("适用场景", "use_cases"), ("不适用情境", "not_for"), ("结构地图", "structure"), ("关键句的作用", "key_sentences"), ("设计依据", "design_reasoning"), ("通用模板", "template"), ("贴近任务的示例", "example"), ("对照与反例", "counterexample"), ("Loop", "loop"), ("质量依据", "quality_review")]
        for label, key in fields:
            value = analysis.get(key)
            text += "\n## " + label + "\n\n" + self._readable(value) + "\n"
        return (text + provenance).encode("utf-8")

    @staticmethod
    def _readable(value):
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "\n\n".join(ReferenceService._readable(row) for row in value)
        if isinstance(value, dict):
            names = {"part": "部分", "observation": "观察", "evidence": "依据", "quote": "原句", "location": "位置", "reason": "作用", "without": "删改后的影响", "author_stated": "作者公开说明", "inferred": "本次分析", "task": "任务", "prompt": "示例", "changes": "改写理由", "status": "状态", "before": "改动前", "after": "改动后", "changed_variable": "变化变量", "expected_effect": "预期差异", "text": "内容", "applicability": "适用条件", "max_rounds": "最多轮次"}
            return "\n".join(f"- {names.get(k,k)}：{ReferenceService._readable(v)}" for k, v in value.items())
        return "未说明" if value is None else str(value)
