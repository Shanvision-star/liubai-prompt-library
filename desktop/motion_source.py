"""读取逐条核对的来源原文；整理稿、短摘录与完整正文分别呈现。"""
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit


def source_prompt(folder, record):
    url = record.get("source", {}).get("url") or ""
    if urlsplit(url).hostname not in ("prompt-motion.com", "www.prompt-motion.com"):
        return None
    metadata = record.get("motion_source") or {}
    if not isinstance(metadata, dict): metadata = {}
    result = {"status": metadata.get("status", "missing"), "original":"", "translation":"", "analysis":"",
              "copyable":False, "url":url, "post_url":metadata.get("post_url"), "author":metadata.get("author", ""),
              "excerpt":metadata.get("excerpt", ""), "excerpt_translation":metadata.get("excerpt_translation", ""),
              "evidence_basis":metadata.get("evidence_basis", ""), "checked_at":metadata.get("checked_at", ""),
              "notice":metadata.get("notice", "来源全文未收录；已有整理稿不作为作者原文。")}
    result["translation_status"] = "missing"
    folder = Path(folder).resolve()
    def verified(name):
        relative = metadata.get(name + "_file")
        if not relative: return ""
        if not isinstance(relative, str): raise ValueError("来源文件路径无效")
        path = (folder / relative).resolve()
        if not path.is_relative_to(folder): raise ValueError("来源文件越出条目目录")
        data = path.read_bytes()
        if sha256(data).hexdigest() != metadata.get(name + "_sha256"): raise ValueError("来源正文校验不一致")
        return data.decode("utf-8")
    if result["status"] == "complete":
        try:
            result["original"] = verified("original")
            if not result["original"]: raise ValueError("来源原文为空")
            result["copyable"] = True
        except (OSError, ValueError, UnicodeError, RuntimeError):
            result.update(status="unavailable", original="", copyable=False,
                          notice="来源原文缺失或校验不一致，请核对原稿；当前禁止复制为完整原文。")
            return result
        # 原文有效时不受附属文件损坏影响；译文必须另行绑定这份原文。
        if metadata.get("translation_source_sha256") != metadata.get("original_sha256"):
            result.update(translation_status="source_changed", notice="中文译文尚未与当前原文绑定，暂不显示；原文仍可复制。")
        else:
            try:
                translated = verified("translation")
                if not translated: raise ValueError("对应译文为空")
                result.update(translation=translated, translation_status="ready")
            except (OSError, ValueError, UnicodeError, RuntimeError):
                result.update(translation_status="unavailable", notice="对应译文缺失或校验未通过，暂不显示；原文仍可复制。")
    try:
        review = metadata.get("analysis_review")
        analysis_binding = review.get("source_sha256") if isinstance(review, dict) else None
        if not analysis_binding or analysis_binding == metadata.get("original_sha256"):
            result["analysis"] = verified("analysis")
    except (OSError, ValueError, UnicodeError, RuntimeError):
        result["analysis"] = ""
    return result
