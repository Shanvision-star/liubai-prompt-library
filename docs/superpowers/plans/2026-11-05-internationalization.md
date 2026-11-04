# 留白国际化实施计划

**目标：** 实现 PRD 的完整中英文体验与可控的语言检测。
**架构：** 将语言决策、语言偏好和翻译资源与用户素材分离；保留本地服务边界和原文哈希绑定。默认不执行 IP 查询；浏览器语言、系统语言和英文依次回退。
**技术：** 原生 JavaScript、Python 标准库、pytest、Node 测试。
**规格：** docs/INTERNATIONALIZATION-PRD.md

## 实施顺序
- [x] 语言决策：按浏览器偏好、可读取的系统语言、英文回退。请求有短超时；手动选择立即生效并使晚到的自动结果失效。
- [x] 语言检测无 IP 查询，CSP 保持同源。单测覆盖不可用存储、语言数据格式异常和系统语言获取失败。
- [x] 导航、素材详情、表单、参考、指南及主要动态状态已接入中英文文案。浏览器验证覆盖键盘、无障碍名称、语言标记与 390 像素宽度。
- [x] 在既有翻译模型上按目标语言和原文哈希绑定。原文和译文独立复制，原文变更时隐藏失配译文。
- [x] 公开集的英文目录与正文资料补齐，核验译文中的来源链接、数字及哈希。翻译覆盖公开可读内容，未获许可的上游全文继续留在来源站点。
- [x] 中英文 README、安装和恢复指南已同步；通过自动测试、真实浏览器与本机 Windows 安装和恢复验证。

## 风险检查
系统语言晚返回不得覆盖手动选择；不进行 IP 查询；CSP 保持同源；翻译无效时不掩盖原文；公共翻译未核验不得宣称完整；兼容已有用户数据。

## Feedback delivery
- Ruling: use user-initiated mailto and public issue links; no backend or automatic submission. Email delivery depends on the user's configured mail application, while GitHub Issues are public and may require login.
- Test: verified keyboard focus and Escape, both destinations, and the feedback dialog at 390px in Chromium. The check inspected the destinations without submitting feedback.
- Research: i18next detector supports custom ordering and persisted language; Fluent distinguishes message resources from locale formatting. Project is local-first, so dependency choice must preserve bundled offline operation.

## 国际化研究与当前决策（2026-11-05）
- i18next 支持 BCP 47、语言回退、复数及可定制检测；其浏览器检测器支持 navigator 和 localStorage，并可定制顺序。参考 https://github.com/i18next/i18next 与 https://github.com/i18next/i18next-browser-languageDetector 。
- Project Fluent 将自然语言资源与区域格式能力分离，参考 https://github.com/projectfluent/fluent 。留白需要固定词条、变量和复数检查；不能对用户正文做全局 DOM 替换。
- 留白现为零第三方运行依赖的本地应用。当前先实现小型独立语言决策模块；未引入第三方代码。最终词条框架需在完整资源清单和打包验证后决定，禁止声称已经完成切换。
- IPWhois 文档说明无密钥免费端点可用于商业，但无 SLA、有请求限制；隐私政策说明可能将 IP 等用量数据记录在日志。候选为固定 HTTPS 端点，仅请求国家字段，超时及拒绝凭据；尚未接入界面、未验证真实网络和发行条件。参考 https://ipwhois.io/documentation 、https://ipwhois.io/privacy 和 https://ipwhois.io/terms 。
- 实测主线公开集初始显示 252 项；其中来源全文、摘录和索引的授权及翻译状态不同，必须逐条审计，不能统一声称已有英文全文。
- Public catalogue audit: 252 index records, 192 have legacy translation metadata and none have a `translations.en` record. This counts metadata only; it is not an inventory of valid English originals or full-text licensing. English coverage and source rights need a separate content-level audit.

## 2026-11-05 用户变更
原 IP 方案及相关研究为历史记录；按用户新指令停止实现 IP、移除自动请求和界面说明。入口收纳为毛玻璃小折叠菜单；语言切换使用可减弱的水波动效。

## 执行记录
- 252 条公开素材均提供英文阅读。202 条已有英文原文，另 50 条提供哈希绑定的英文译文。192 条目录标题和简介从固定英文原文提取，60 条单独补齐。上游许可未明确的条目仅翻译公开整理稿，并保留来源链接。译文已做自动校验，尚未独立人工审校。
- 一次译文批处理在 PowerShell 启动阶段被策略拒绝，回执未披露具体规则。另两次编辑命令被 CC Safety Net 的 `analysis.strict-unparseable` 规则拒绝。后续采用结构化补丁写入资料，短命令单独读取并验证哈希。
- 默认不进行 IP 查询。语言与反馈收纳在同一个毛玻璃折叠菜单中，语言偏好保存在本机。动效尊重减少动画设置。
- 界面、指南、备份说明和安装向导均有中英文文案。私有正文、参考快照、版本和分析作为用户内容保留原有语言。未知的服务错误在英文界面提供可读的上下文提示。
- 源码和安装包使用各自的验证记录。安装候选包通过本机隔离测试后仍需单独发布，GitHub Releases 展示已发布版本。

## 验证记录
- 252 条素材通过公开集合完整性校验。Python 全套测试 262 通过、1 跳过。9 项 Node 测试覆盖语言优先级、存储失败、格式异常、竞态和阅读模式。
- Chromium 实测语言切换、英文折叠、两种复制操作、反馈链接、参考库、指南、新建和分类、收藏持久化及备份下载。另注入设置读取失败、本地存储禁用和系统语言延迟。两轮共观测 188 次同源请求，未捕获浏览器异常。
- 将 Chromium 下载的备份解压至独立目录后用源码启动，读回测试条目的原文、版本、分类、收藏及公开参考。
- Windows 11 x64 隔离验收通过。英文安装、简体中文重装、移除 Python 路径后的独立启动、8 个 MCP 工具、备份恢复、语言持久化和卸载保留资料均已验证。16 个内置网页文件与验证时源码哈希一致。候选安装包 SHA-256 为 `a12aae11117da8871a835f2b9ddb63d2cceb80a39f7b36066272cd9a32b235dc`。
