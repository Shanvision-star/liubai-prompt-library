# Windows 安装包构建

在 Windows x64 上使用 Python 3.12、`requirements-build.txt` 指定的 PyInstaller 和 Inno Setup 6.7.3。最终用户不需要这些开发工具。编译器从 [Inno Setup 官方下载页](https://jrsoftware.org/isdl.php)取得并核对签名；冻结资源路径按 [PyInstaller 文档](https://pyinstaller.org/en/stable/runtime-information.html)处理。

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv-build\Scripts\python.exe tools\build_windows.py --iscc "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" --output dist\windows
```

产物位于 `dist/windows/release/`，包含安装程序和 SHA-256。构建脚本复制 Python、PyInstaller、OpenSSL、Inno Setup 许可；Python 的许可文件还包含随发行包提供的 Tcl/Tk 等说明。二进制版本信息由 `packaging/version_info.txt` 提供，发布时须与应用、安装脚本版本一致。

安装版包含无终端的 `Liubai.exe` 和用于 stdio 的 `mcp/Liubai-MCP.exe`。程序只读资源与可写资料分开。首次准备公开素材经清单哈希校验和文件事务写入；已有库绝不重新覆盖。发行资料只来自显式维护的 `bundled-library/`，不是构建时任意读取开发者的私人目录。

## 验证

在没有日常留白安装记录的测试用户下运行：

```powershell
python tools\smoke_windows_installer.py --installer dist\windows\release\Liubai-Setup-0.6.0-windows-x64.exe --workdir dist\installer-smoke
```

验证真实安装、移除 Python 环境路径后的独立启动、中文模板与拆解、API 保存、独立 MCP 握手和保存、重复安装、卸载保留数据。测试只操作显式指定的新目录；若当前用户已有安装记录会停止，不接管日常安装。

该检查不能替代一台完全没有安装过 Python 的干净虚拟机验收。当前发行包未配置代码签名；不伪称已签名、通过 SmartScreen 或覆盖所有 Windows 设备。

## 更新素材

`tools/export_collection.py --source <已获授权的库> --output <新的公开目录>` 生成独立副本；不会覆盖现有输出目录。工具只处理本次已审核的素材格式，不是对任意来源的自动版权判断。发布前复核来源许可、脱敏清单、原文/译文/整理稿范围以及生成的清单哈希。任何用户新增的私人素材都不会自动进入构建。
