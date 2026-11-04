"""读取与原文文件校验值绑定的中文译文，不把优化版当作翻译。"""

from hashlib import sha256
from pathlib import Path


def reading_pair(folder, record, original, original_sha256, target_language="zh"):
    """原文始终保留；只有来源与译文校验均通过时才显示对应译文。"""
    if target_language not in {"zh", "en"}:
        raise ValueError("不支持的译文语言")
    notices = ({"missing": "English translation unavailable for this original.",
                "unavailable": "The English translation is unavailable or failed verification.",
                "source_changed": "The original changed; the English translation needs review.",
                "ready": "English translation; the primary copy action copies the original."}
               if target_language == "en" else None)
    result = {
        "original": original,
        "translation": "",
        "translation_status": "missing",
        "copyable": bool(original.strip()),
        "notice": "尚无与这份原文对应的中文译文；复用改写和分析不作为翻译。",
    }
    if notices:
        result["notice"] = notices["missing"]
    translations = record.get("translations")
    metadata = translations.get(target_language) if isinstance(translations, dict) else None
    if metadata is None and target_language == "zh":
        metadata = record.get("translation")
    if not metadata:
        return result
    if not isinstance(metadata, dict):
        result.update(translation_status="unavailable", notice=notices["unavailable"] if notices else "译文记录格式异常，请核对后补充。")
        return result
    if metadata.get("source_sha256") != original_sha256:
        result.update(translation_status="source_changed", notice=notices["source_changed"] if notices else "原文已变化，旧译文已隐藏；需要按当前原文重新核对。")
        return result
    if target_language == "zh" and metadata.get("status") == "already_chinese":
        result.update(translation_status="already_chinese", notice="这条原文已为中文，可直接阅读上方内容，无需另译。")
        return result
    try:
        folder = Path(folder).resolve()
        relative = metadata["file"]
        if not isinstance(relative, str) or not relative:
            raise ValueError("译文路径无效")
        path = (folder / relative).resolve()
        if not path.is_relative_to(folder):
            raise ValueError("译文路径越出素材目录")
        data = path.read_bytes()
        if sha256(data).hexdigest() != metadata.get("sha256"):
            raise ValueError("译文校验值不一致")
        translated = data.decode("utf-8-sig")
        if not translated.strip() or metadata.get("status") != "ready":
            raise ValueError("译文尚未完成")
        result.update(translation=translated, translation_status="ready",
                      notice=notices["ready"] if notices else "原文在上，中文在下；主复制按钮只复制原文提示词。")
    except (KeyError, OSError, ValueError, UnicodeError, RuntimeError):
        result.update(translation_status="unavailable", notice=notices["unavailable"] if notices else "对应译文缺失或校验未通过，暂不显示；原文仍可阅读和复制。")
    return result
