"""让隔离测试能够导入桌面应用的同目录模块。"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
