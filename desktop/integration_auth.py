"""生成仅供本机集成读取的写入令牌，不将令牌返回网页或写入日志。"""

from pathlib import Path
import os
import re
import secrets


def integration_token(state_dir):
    path = Path(state_dir) / "api-token"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        token = path.read_text(encoding="utf-8").strip()
    else:
        token = secrets.token_urlsafe(32)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(token + "\n")
            file.flush()
            os.fsync(file.fileno())
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", token):
        raise ValueError("本机API令牌文件格式异常，请检查运行目录中的 api-token")
    return token
