"""安装版 MCP 控制台入口；标准输入输出专用于协议，不需要用户安装 Python。"""
from mcp_server import main
from bundled_library import install_collection
from pathlib import Path
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--data-root", type=Path)
    args, _ = parser.parse_known_args()
    if args.data_root:
        install_collection(args.data_root)
    raise SystemExit(main())
