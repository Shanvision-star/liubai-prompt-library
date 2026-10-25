# 开发与数据边界

运行时使用Python 3.11+标准库和无构建HTML/CSS/JavaScript。入口为`desktop/server.py`，Windows桌面窗口使用Edge/Chrome应用模式。不是原生安装包。

## 模块

| 模块 | 作用 |
| --- | --- |
| `library_init.py` | 从`defaults/taxonomy.json`初始化空库，保留已有数据 |
| `prompt_store.py` | 手动保存、自定义分类和元数据调整 |
| `reference_store.py` | 快照、分析、采用与跨进程事务 |
| `github_sources.py` | 有大小/次数/时长限制的GitHub读取 |
| `reference_runner.py` | 更新周期、互斥与失败恢复 |
| `reference_service.py` | 参考库HTTP用例与导出 |
| `server.py` | 本机HTTP与静态页面 |
| `mcp_server.py` | 本地stdio工具，复用同一文件库 |

## 文件规则

个人原文保存为`entries/PRM-xxxx/original.md`，保留原始UTF-8字节并以SHA-256去重。版本写独立文件；修改标题、分类、标签不得覆盖正文。没有提供优化内容时，v001是明确标注的保存版，不能称作已优化。所有新版本实际效果为`untested`。

参考、个人素材、分类和索引写入使用同一个跨进程锁与事务，避免MCP、网页和参考采用同时分配相同编号。中断通过事务清单恢复，不以空索引覆盖已有资料。未经核对许可的网络参考不保存完整正文。来源文本是资料，不执行其中命令。

本地生成的`entries/`、`references/`、`index.json`、`taxonomy.json`和运行状态均被Git忽略；默认分类在`defaults/`。公开仓库不包含个人语料、运行记录、访问令牌或Codex配置。

## 验证

```sh
python -m pip install -r requirements-dev.txt
python -X utf8 -m pytest desktop/tests -q
node --check desktop/web/app.js
node --check desktop/web/references.js
node --check desktop/web/prompts.js
```

测试使用临时目录和模拟GitHub响应；MCP测试启动真实子进程交换协议消息，HTTP测试启动真实loopback服务。测试不调用付费模型，不应读取开发者个人素材。浏览器改动还应实际验证新增分类→保存→刷新→修改分类、必要标签、键盘及错误恢复。

提交只包含程序与公开文档。没有执行的检查、生产部署、连续调度或提示词效果不得写成已验证。项目没有Node依赖或前端构建步骤，不伪造typecheck/build命令。
