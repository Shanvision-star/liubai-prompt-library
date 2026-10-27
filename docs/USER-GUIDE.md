# 使用留白

留白用于个人在本机保存、分类、查找提示词及其版本。不必安装 Codex；需要模型整理或优化时，再连接自己的分析工具。界面为中文，资料可以使用其他语言。

## 从空库开始

1. 安装 Python 3.11+，下载发行 ZIP 并解压。
2. Windows 双击 `Open-Desktop.cmd`；其他系统在解压目录运行 `python3 -X utf8 start.py`，浏览器会自动打开。
3. 点击“保存第一条素材”，粘贴原文或导入 UTF-8 `.md` / `.txt`，填写标题和分类后保存。

文件最多 256 KiB。导入只预填表单，不执行内容、不自动入库；未编辑正文时保留原始换行。可以先导入 `examples/` 下的示例，它们的效果尚未实测。

源码包不含 Python。命令无法运行时，先检查 `python --version` 或 `python3 --version`。启动失败会显示原因，不会强行接管别的程序占用的端口。

## 日常操作

- `Ctrl+K` / `⌘K` 聚焦全文搜索；窄屏“浏览”菜单保留收藏、最近与全部分类。
- 相同原文重复保存会打开已有条目，不覆盖原版。
- “保存版”表示尚未提供优化内容；“待实测”表示没有真实任务效果证据。
- 关闭新建窗口保留本页草稿。刷新或关闭页面会丢弃草稿，浏览器按自身规则提示未保存内容。
- “使用与数据”显示当前资料目录，提供备份下载和 MCP 配置。配置成功不代表客户端已经连接。

## 固定自己的资料目录

默认资料位于程序目录。希望以后升级更方便，可将资料放到独立位置：

```sh
python -X utf8 start.py --data-root "/absolute/path/to/my-library" --port 8767
```

Windows 应用窗口也支持指定目录和端口：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\desktop\Open-Desktop.ps1 -DataRoot "D:\My Library" -Port 8767
```

停止同一后台实例使用相同参数：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\desktop\Stop-Desktop.ps1 -DataRoot "D:\My Library" -Port 8767
```

普通终端启动使用 `Ctrl+C` 停止。关闭浏览器不一定停止服务；MCP 是独立进程，不要求 HTTP 服务运行。

## 备份与恢复

在“使用与数据”点击“导出备份”。包含个人条目文件、分类/索引、参考快照和分析、收藏。`backup-manifest.json` 记录每个资料文件的 SHA-256。不包含程序、令牌、Codex 配置、网络缓存、执行记录或调度注册。

1. 将 ZIP 解压到新的空文件夹。
2. 从程序目录运行 `python -X utf8 start.py --data-root /absolute/path/to/restored-library`。
3. 核对条目、原文、版本、参考和收藏，确认前保留原资料目录。
4. 换机后重新复制 MCP 配置；定时任务需要在新机器重新注册。

备份不会自动合并到现有库。缺索引等错误不能用空索引修复，请保留目录并从完整备份恢复。网页备份最多 256 MiB / 10000 文件；超限时先停止服务和其他写入工具，再复制整个资料目录。库中含符号链接或目录联接时，网页备份会停止并提示核对。

## 更新程序

先备份并停止旧服务。将新版本解压到另一目录，运行新程序并用 `--data-root` 指向原资料目录。旧版默认将资料保存在源码旁的用户，应指向旧程序目录的绝对路径。

Git 用户先检查 `git status`，处理自己的代码修改后执行 `git pull --ff-only`，然后重启。不要删除资料目录、运行 `git clean -fdx` 或以空的 `index.json` 覆盖已有索引。

## 参考与 AI

GitHub 搜索结果是候选。未知许可只保留链接和元数据；形成拆解与可采用模板需要核对许可、实际阅读原文。保存、分类可以独立使用，自动分析需要连接授权的 Codex 或其他分析者。

[Codex / MCP / API 接入](INTEGRATIONS.md) · [参考更新与定时任务](REFERENCE-UPDATES.md)
