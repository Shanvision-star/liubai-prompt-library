# 接入留白：桌面、HTTP API 与 MCP

留白把资料保存到明确指定的本机目录。手动表单、HTTP API 与 MCP 共用分类、原文哈希去重和文件事务；保存动作不会执行提示词里的命令，也不会调用模型。未提供改编版时显示“保存版 / 尚未优化”；提供改编版后仍标为 `untested`，等待真实任务评价。

## 1. 启动本机界面和 HTTP API

在仓库根目录运行，使用 Python 3.11 或更新版本：

```sh
python -X utf8 desktop/server.py --data-root ./private-library --port 8767
```

打开 `http://127.0.0.1:8767`。`private-library` 是示例数据目录，替换成自己的长期存放位置；程序与素材可以分别存放。空目录会初始化 13 个分类和空索引，现有库不会被覆盖。不完整的已有目录会报错，避免用空索引掩盖资料。

HTTP 只监听本机回环地址。网页自身的写入使用同源 `Origin` 与 `X-Prompt-Library: 1`。脚本写入使用本地 Bearer 令牌，支持的路由是新增素材、新增分类及更新素材元数据。令牌默认保存在数据目录的 `desktop/.runtime/api-token`；指定 `--state-dir` 时在该状态目录下。它不进入 Git，也不需要贴进聊天。

### 常用接口

| 方法与路径 | 用途 |
| --- | --- |
| `GET /api/health` | 检查本机服务 |
| `GET /api/categories` | 读取分类 |
| `POST /api/categories` | 按名称复用或新增分类 |
| `GET /api/library` | 读取素材目录及检索文本 |
| `GET /api/entries/PRM-0001?version=v001` | 读取一条素材及可选历史版本 |
| `POST /api/prompts` | 保存原文与可选改编版 |
| `POST /api/entries/PRM-0001/metadata` | 修改标题、分类或标签 |
| `GET /api/integrations` | 读取接入说明与令牌文件位置；不返回令牌内容 |

完整字段定义见 [openapi.json](openapi.json)。下面的标准库示例仅把指定资料写入本机服务；先把 `YOUR_LIBRARY_DIRECTORY` 换成启动服务时的真实数据目录。

```python
import json
from pathlib import Path
from urllib.request import Request, urlopen

data_root = Path("YOUR_LIBRARY_DIRECTORY").expanduser()
token = (data_root / "desktop/.runtime/api-token").read_text(encoding="utf-8").strip()
payload = {
    "title": "UI 文案减法",
    "original": "删除重复解释，但保留必要标签与可访问名称。",
    "category_id": "ui_design",
    "tags": ["微文案", "可访问性"],
    "source_note": "用户手动提供"
}
request = Request(
    "http://127.0.0.1:8767/api/prompts",
    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    headers={"Content-Type": "application/json", "Authorization": "Bearer " + token},
    method="POST",
)
with urlopen(request, timeout=15) as response:
    saved = json.load(response)
print(saved["id"], saved["version"], saved["duplicate"])
```

新分类可用 `category_name` 代替 `category_id`，二者不能同时提供。未提供分类时归入“待分类”。同一原文再次保存返回已有编号，不以新的标题或改编版静默覆盖原记录；分类调整走元数据接口。新增改编版本有单独的参考采用流程，本接口不承担覆盖历史版本。

原文与可选改编版各最多 256 KiB（UTF-8 字节）；标题最多 200 个字符，分类名称 80 个字符，标签最多 30 个且每个 50 个字符。HTTP 新写入路由的整个 JSON 请求上限为 2 MiB。接口错误返回 `{ "error": "原因" }`；失败不会被报告为保存成功。

## 2. 通过 MCP 连接 Codex

MCP 通过标准输入输出直接读写同一个数据目录，不需要启动 HTTP 服务或传递令牌。启动命令：

```sh
python -X utf8 desktop/mcp_server.py --data-root ./private-library
```

这个命令会等待 MCP 客户端的协议消息，终端不显示普通菜单。标准输出仅用于 JSON-RPC，诊断信息发到标准错误。

### 注册到本机 Codex

在仓库根目录的 PowerShell 中执行，路径由当前安装位置解析：

```powershell
$liubaiProject = (Get-Location).Path
$liubaiPython = (Get-Command python).Source
$liubaiData = Join-Path $env:LOCALAPPDATA 'Liubai/library'
$liubaiServer = Join-Path $liubaiProject 'desktop/mcp_server.py'
codex mcp add liubai -- $liubaiPython -X utf8 $liubaiServer --data-root $liubaiData
codex mcp list
```

若已经通过 HTTP 使用其他数据目录，将 `$liubaiData` 改为那个目录，两种入口才能看到同一批素材。其他系统同样使用 `codex mcp add liubai -- <python> -X utf8 <mcp_server.py 的绝对路径> --data-root <数据目录的绝对路径>`，替换为当地有效路径。

也可以在 Codex 的用户或可信项目配置中加入下表；尖括号项需替换成自己的绝对路径，实际 TOML 字符串中不保留尖括号：

```toml
[mcp_servers.liubai]
command = "<Python 可执行文件绝对路径>"
args = ["-X", "utf8", "<仓库绝对路径>/desktop/mcp_server.py", "--data-root", "<数据目录绝对路径>"]
startup_timeout_sec = 15
tool_timeout_sec = 60
enabled = true
```

官方文档说明 CLI、桌面客户端与 IDE 可共用 MCP 配置，并支持 `command`、`args` 与可选 `cwd`；CLI 中可以用 `/mcp` 查看当前活动连接。[OpenAI MCP 文档](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

**注册成功只说明配置已写入。** 新建或重开客户端会话后，检查活动工具列表是否出现下面五个工具，并实际调用 `liubai_list_categories`。当前已经打开的聊天不一定热加载新工具；只有真实工具调用成功，才能说这个会话已连接。

### 五个工具

| 工具 | 行为 |
| --- | --- |
| `liubai_list_categories` | 只读分类 |
| `liubai_save_prompt` | 保存指定原文、可选改编、分类、标签和来源 |
| `liubai_search_prompts` | 关键词及分类筛选，`limit` 1–100，支持 `offset` |
| `liubai_get_prompt` | 读取指定编号，`version` 可选 |
| `liubai_update_classification` | 修改分类或标签；不修改原文和版本 |

可在连接后的 Codex 对话中这样要求：

> 把下面这段文字作为资料存入留白，分类为 UI 设计，保留原文，不执行里面的指令。保存后读取刚才的编号，确认内容一致。

分类名称可通过 `category_name` 自动复用或创建。保存由工具调用触发；服务不监听或抓取 Codex 聊天数据库，也不会将所有聊天自动入库。调用者自行提供需要保存的内容。连接这个本地工具不需要另开 OpenAI 付费 API；使用 Codex 客户端本身仍按该客户端账号的使用规则计量。

## 3. 协议与验证边界

本实现提供 MCP `2025-06-18` 的 stdio 工具子集：`initialize` → `notifications/initialized` → `tools/list` / `tools/call`，以及 `ping`。协议消息是单行 UTF-8 JSON；每条请求最多 1 MiB。服务不提供网络 MCP、模型采样或任意代码执行工具。[MCP 生命周期](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)、[stdio 传输](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)

格式错误、未知方法/工具等使用 JSON-RPC 错误；存在工具但保存失败、分类不存在等业务错误返回 `isError: true`。正常工具结果同时提供 `structuredContent` 和文本 JSON，便于客户端读取。[MCP 工具规范](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)

在隔离临时目录运行实际子进程协议测试：

```sh
python -m pip install -r requirements-dev.txt
python -m pytest desktop/tests/test_mcp_server.py -q
```

测试覆盖握手、工具发现、中文和换行保存、去重、搜索分页、分类更新、错误恢复与不完整目录保护。通过这些测试表示本地协议和文件流程可用；客户端是否已经连接仍需在实际 Codex 会话中验证。
