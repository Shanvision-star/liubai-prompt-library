# Windows 独立运行程序：界面进程不显示终端，MCP 保留标准输入输出。
from pathlib import Path
import json
root = Path(SPECPATH).parent
assets = [(str(root / 'desktop/web'), 'desktop/web'), (str(root / 'defaults'), 'defaults')]
# 只分发公开清单列出的资料，排除本地读取时产生的锁或其他运行状态。
collection = json.loads((root / 'bundled-library/manifest.json').read_text(encoding='utf-8'))
for name in sorted({'manifest.json', 'README.md'} | {row['path'] for row in collection['files']}):
    source = root / 'bundled-library' / name
    assets.append((str(source), str(Path('bundled-library') / Path(name).parent)))
teaching = json.loads((root / 'learning-library/checksums.json').read_text(encoding='utf-8'))
for name in ['checksums.json'] + [row['path'] for row in teaching['files']]:
    source = root / 'learning-library' / name
    assets.append((str(source), str(Path('learning-library') / Path(name).parent)))

app = Analysis([str(root / 'desktop/windows_main.py')], pathex=[str(root / 'desktop')], datas=assets, hiddenimports=[], excludes=['pytest'])
app_pyz = PYZ(app.pure)
app_exe = EXE(app_pyz, app.scripts, [], exclude_binaries=True, name='Liubai', console=False, icon=str(root / 'desktop/app.ico'), version=str(root / 'packaging/version_info.txt'))
COLLECT(app_exe, app.binaries, app.datas, name='Liubai')

mcp = Analysis([str(root / 'desktop/mcp_frozen.py')], pathex=[str(root / 'desktop')], datas=assets, hiddenimports=[], excludes=['pytest'])
mcp_pyz = PYZ(mcp.pure)
mcp_exe = EXE(mcp_pyz, mcp.scripts, [], exclude_binaries=True, name='Liubai-MCP', console=True, icon=str(root / 'desktop/app.ico'), version=str(root / 'packaging/version_info.txt'))
COLLECT(mcp_exe, mcp.binaries, mcp.datas, name='Liubai-MCP')
