# Windows 独立运行程序：界面进程不显示终端，MCP 保留标准输入输出。
from pathlib import Path
root = Path(SPECPATH).parent
assets = [(str(root / 'desktop/web'), 'desktop/web'), (str(root / 'defaults'), 'defaults'), (str(root / 'bundled-library'), 'bundled-library')]

app = Analysis([str(root / 'desktop/windows_main.py')], pathex=[str(root / 'desktop')], datas=assets, hiddenimports=[], excludes=['pytest'])
app_pyz = PYZ(app.pure)
app_exe = EXE(app_pyz, app.scripts, [], exclude_binaries=True, name='Liubai', console=False, icon=str(root / 'desktop/app.ico'), version=str(root / 'packaging/version_info.txt'))
COLLECT(app_exe, app.binaries, app.datas, name='Liubai')

mcp = Analysis([str(root / 'desktop/mcp_frozen.py')], pathex=[str(root / 'desktop')], datas=assets, hiddenimports=[], excludes=['pytest'])
mcp_pyz = PYZ(mcp.pure)
mcp_exe = EXE(mcp_pyz, mcp.scripts, [], exclude_binaries=True, name='Liubai-MCP', console=True, icon=str(root / 'desktop/app.ico'), version=str(root / 'packaging/version_info.txt'))
COLLECT(mcp_exe, mcp.binaries, mcp.datas, name='Liubai-MCP')
