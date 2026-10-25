# 留白 · 提示词素材库

一个保留原文、分类和来源的本机提示词库。简约白、中性灰和磨砂玻璃界面；支持手动保存、自定义分类、GitHub参考、版本记录，以及Codex本地MCP接入。

**Local-first prompt library with manual categories, immutable originals, reference snapshots, REST API and a local MCP server.**

![留白界面](docs/images/library.png)

## 开始使用

需要 **Python 3.11+**。运行程序只使用Python标准库，无需安装Node或模型依赖。

```sh
git clone https://github.com/Shanvision-star/liubai-prompt-library.git
cd liubai-prompt-library
python -X utf8 desktop/server.py
```

打开 [http://127.0.0.1:8767](http://127.0.0.1:8767)。首次启动自动创建空库与13个默认分类。

Windows可双击`Open-Desktop.cmd`，通过Edge/Chrome打开独立应用窗口。关闭窗口后本机服务继续运行；完全停止可执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\desktop\Stop-Desktop.ps1
```

需要把数据放在其他位置时：

```sh
python -X utf8 desktop/server.py --data-root /absolute/path/to/my-library --port 8767
```

服务仅监听本机回环地址。macOS/Linux可直接使用浏览器；Windows启动脚本是便利入口，项目目前不提供原生安装包。

## 保存与分类

1. 点击“新增素材”，填写标题、原文、分类和标签；优化版可选。
2. 选择已有分类，或填写一个新分类名称；也可单独新增分类。
3. 保存后立即检索、复制或导出；已有素材可修改分类和标签。

原文逐字保存并计算SHA-256，相同原文重复提交会返回已有条目。修改分类只改元数据，不改原文和版本。没有填写优化版时明确显示“保存版／尚未优化”；填写的优化版也保持效果待实测，不会假装已经经过模型或用户评估。

默认13类：开发与编程、UI设计、大模型设计、LangChain设计、审美Taste、产品与需求、商务与销售、内容与写作、视觉与视频、学习与研究、办公与效率、通用与角色、待分类。自定义分类与默认分类使用相同检索和保存流程。

## Codex与其他工具接入

项目同时提供：

- **本地MCP**：Codex按指令调用工具保存提示词、查询分类、检索、读取和修改分类。stdio连接，不需要独立模型API，也不会监听或读取Codex聊天数据库。
- **REST API**：`POST /api/prompts`保存，`POST /api/categories`新增分类，`POST /api/entries/{id}/metadata`改分类等元数据。

本机客户端通过Bearer令牌写入；令牌由HTTP服务保存在当前运行目录的`api-token`文件中，不返回网页、不写入Git。浏览器操作使用同源校验。MCP直接调用同一存储层，不依赖HTTP服务或Bearer令牌。

[接入步骤、工具参数与请求示例](docs/INTEGRATIONS.md) · [OpenAPI文档](docs/openapi.json)

注册MCP配置与当前会话已加载工具是两件事，连接状态需在客户端查看。保存不等于自动优化；如需优化，由当前授权的Codex或其他分析者生成内容后明确保存。

## 参考库

支持GitHub搜索与文件链接导入、收藏、关注、原文优先阅读、拆解卡、版本差异和采用预览。上游变化进入新的快照与待分析队列，个人版本不会被静默覆盖。

公开发行版从空库开始，不捆绑开发者个人素材或第三方提示词全文。导入材料时核对许可与具体使用条件，许可未知的候选只保留链接和元数据。分析者可记录结构、关键句作用、通用模板、改写示例、反例与有停止条件的Loop。

增量检查与调度支持见 [参考库维护说明](docs/REFERENCE-UPDATES.md)。**独立安装默认没有已注册的调度器**；登记调度编号不等于创建定时任务。实际分析能力不可用时保持“待分析”，不使用固定文案模拟AI分析。

## 文件与隐私

程序与资料分开：默认分类模板在`defaults/`，运行后生成的资料保存在所选数据目录。

```text
entries/PRM-xxxx/        原文、保存或优化版本、元数据
references/             来源快照、拆解、采用关系与运行记录
index.json / INDEX.md   素材索引
taxonomy.json           默认与自定义分类
desktop/.runtime/       本机令牌、收藏、日志和浏览器状态
```

以上个人数据和运行文件默认被`.gitignore`排除。代码不自动上传素材、不配置云同步；GitHub搜索和来源检查会请求GitHub，日常本地浏览与保存不调用模型。若将数据目录另放在其他Git仓库，请自行保持相应忽略规则。

## 开发

```sh
python -m pip install -r requirements-dev.txt
python -X utf8 -m pytest desktop/tests -q
```

测试使用临时目录与模拟网络响应，不消耗模型API额度。前端为HTML/CSS/JavaScript，无构建步骤。详见 [开发说明](docs/DEVELOPMENT.md)。

## 许可证

程序使用 [MIT License](LICENSE)。用户自行收录的提示词和参考材料保留各自来源与许可，不因放入本库而改为MIT。
