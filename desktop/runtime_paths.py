"""统一源码与独立可执行程序的只读资源位置。"""
from pathlib import Path
import sys


def resource_root():
    return Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]


def bundled_mcp():
    return Path(sys.executable).parent / "mcp" / "Liubai-MCP.exe"
