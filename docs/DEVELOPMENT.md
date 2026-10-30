# 开发与数据边界

源码运行时使用 Python 3.11+ 标准库和无构建 HTML/CSS/JavaScript。入口为 `desktop/server.py`，Windows 桌面窗口使用 Edge/Chrome 应用模式；Windows 安装包捆绑运行环境。

## 模块

| 模块 | 作用 |
| --- | --- |
| `library_init.py` | 从`defaults/taxonomy.json`初始化空库，保留已有数据 |
| `prompt_store.py` | 手动保存、分类、追加版本、来源补充与哈希绑定的分析修订 |
| `reference_store.py` | 快照、分析、采用与跨进程事务 |
| `github_sources.py` | 有大小/次数/时长限制的GitHub读取 |
| `reference_runner.py` | 更新周期、互斥与失败恢复 |
| `reference_service.py` | 参考库HTTP用例与导出 |
| `server.py` | 本机HTTP与静态页面 |
| `mcp_server.py` | 本地stdio工具，复用同一文件库 |
| `library_export.py` | 当前实例配置与可迁移 ZIP 备份，不导出机器授权/调度 |
| `../start.py` | 跨平台终端启动、服务身份核对与浏览器打开 |

## 文件规则

个人原文保存为`entries/PRM-xxxx/original.md`，保留原始UTF-8字节并以SHA-256去重。版本写独立文件；修改标题、分类、标签不得覆盖正文。没有提供优化内容时，v001是明确标注的保存版，不能称作已优化。所有新版本实际效果为`untested`。

参考、个人素材、分类和索引写入使用同一个跨进程锁与事务，避免MCP、网页和参考采用同时分配相同编号。中断通过事务清单恢复，不以空索引覆盖已有资料。未经核对许可的网络参考不保存完整正文。来源文本是资料，不执行其中命令。

本地生成的`entries/`、`references/`、`index.json`、`taxonomy.json`和运行状态均被Git忽略；默认分类在`defaults/`。`bundled-library/` 是库主人明确授权、经脱敏与许可范围整理的公开副本，包含汉化、原创复用版本及拆解。持续使用的私人工作目录与后续新增内容不自动上传，运行记录、访问令牌与 Codex 私人配置继续排除。

Windows 安装版使用 `runtime_paths.py` 定位只读资源，`bundled_library.py` 首次事务安装公开内容，`windows_main.py` 管理独立资料目录及单实例。MCP 使用单独控制台程序，参数和存储层保持一致。`/api/application/quit` 是显式停止动作，要求同源页面或本机 Bearer 授权。构建与真实安装验证见 [WINDOWS-BUILD.md](WINDOWS-BUILD.md)。

## 验证

```sh
python -m pip install -r requirements-dev.txt
python -X utf8 -m pytest desktop/tests -q
node --check desktop/web/app.js
node --check desktop/web/references.js
node --check desktop/web/prompts.js
node --check desktop/web/guide.js
node --check desktop/web/lifecycle.js
python tools/validate_public_collection.py
```

测试使用临时目录和模拟GitHub响应；MCP测试启动真实子进程交换协议消息，HTTP测试启动真实loopback服务。测试不调用付费模型，不应读取开发者个人素材。浏览器改动还应实际验证新增分类→保存→刷新→修改分类、必要标签、键盘及错误恢复。

提交只包含程序与公开文档。没有执行的检查、生产部署、连续调度或提示词效果不得写成已验证。项目没有Node依赖或前端构建步骤，不伪造typecheck/build命令。

## 公开选择与自有模型

公开范围固定在根目录 `public-selection.json`，明确列出 `entry_ids` 和 `reference_ids`。重新导出时必须显式传 `--selection`；无清单不得默认导出私人全库。导出后检查每条全部版本、来源、许可与教学，再运行只读校验器。教学打包也按校验清单取文件，防止旧卡残留。

`private-learning-library/` 属于私人数据并被 Git 忽略，随资料备份保存，不随程序公开。新分析由用户自己的模型产生；存储层只验证版本、正文哈希与修订关系，不调用供应商、不据此标记效果已测试。每次修改版本、来源或文档边界，应同步 README、用户指南、接入说明、OpenAPI 和本验证记录。
