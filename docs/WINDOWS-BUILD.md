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
python tools\smoke_windows_installer.py --installer dist\windows\release\Liubai-Setup-0.7.0-windows-x64.exe --workdir dist\installer-smoke
```

验证真实安装、移除 Python 环境路径后的独立启动、中文模板与拆解、API 保存、独立 MCP 握手和保存、重复安装、卸载保留数据。测试只操作显式指定的新目录；若当前用户已有安装记录会停止，不接管日常安装。

该检查不能替代一台完全没有安装过 Python 的干净虚拟机验收。当前发行包未配置代码签名；不伪称已签名、通过 SmartScreen 或覆盖所有 Windows 设备。

## 更新素材

`python tools/export_collection.py --source <已获授权的库> --output <新的公开目录> --selection public-selection.json` 生成独立副本；不会覆盖现有输出目录。工具只处理本次已审核的素材格式，不是对任意来源的自动版权判断。发布前复核来源许可、脱敏清单、原文/译文/整理稿范围以及生成的清单哈希。任何用户新增的私人素材都不会自动进入构建。构建入口会先运行只读公开清单校验，失败即停止打包。

## 0.7.0 安装检查

安装脚本按应用版本和当前清单核验，保留正常开始菜单入口；检查实际安装后的说明页资源、中文复用版、全部教学资源哈希、8 个 MCP 工具及版本/来源/分析写入。`--keep-running` 可在重装后保留服务，继续对安装版做浏览器操作验证，完成后须停止测试实例并卸载。

2026-10-31 已在 [GitHub Windows runner](https://github.com/Shanvision-star/liubai-prompt-library/actions/runs/41159699957) 完成构建、安装、独立启动、重装和卸载，在本机 Windows 11 完成正常应用入口、桌面/390px 说明页和新功能检查。二者均不等于所有 Windows 10/11 设备或 5 位真实用户验收。安装包 SHA-256 见 Release 的 `SHA256SUMS.txt`，核验摘要见 `INSTALLATION-CHECKS.json`。
