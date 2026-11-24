# Apple / macOS 磨砂玻璃 · Codex 提示词与参考索引

整理日期：2026-11-24（北京时间）  
分类：UI 设计｜标签：Apple、macOS、Glasswork、磨砂玻璃、液态玻璃、边缘折射、可访问性

**先定内容层和操作层，再加材质。** 浅色内容面保持实底；搜索、选中胶囊、工具栏或浮动入口才用玻璃。磨砂是底层，边缘折射是可撤掉的增强，流光是单独的动效，不是材质本身。不要把全页模糊、石墨色工程文档模板、偏蓝正文、复杂壁纸或旋转亮边当成 macOS 风格。

## 1. 已脱敏的通用提示词

### 案例检索工作台 · 三栏与轻磨砂

> **案例检索界面：** 保留左侧状态筛选、中间案例列表、右侧整改证据。搜索栏和选中胶囊可用淡磨砂玻璃；结果、测试数值、截图和原文都用不透明底。拒绝石墨色工程文档模板和偏蓝正文。关键词、测试条件、结论、证据入口按重要性排，不靠颜色分层。Edge 可增强边缘折射；iPhone Safari 不支持时降级成同尺寸的磨砂，按钮和文字不能变淡。

### 论文阅读应用 · 保持阅读位置

> **论文阅读应用：** 参考 NetNewsWire 的「列表到原文」路径。玻璃只放在搜索和阅读工具栏，论文图表、引文和 PDF 保持在稳定的内容层。入口页可以有星空，进入阅读页后停止背景动效。切换论文、折叠侧栏和返回时，保留阅读位置、选中项与键盘焦点。

### 论文阅读应用 · 论文图表入口局部折射

请先检查现有组件和样式，只为目标应用的「论文图表」浮动入口做一版轻量液态玻璃。不改变组件位置、尺寸、点击行为和键盘操作；论文正文、公式和数据表保持现状。

用半透明底色、轻微背景模糊和一条细高光做出玻璃底色。在支持的浏览器上，只让卡片边缘附近的背景纹理轻微偏移，中心少变形；标题、图标和按钮始终清晰。不默认加流动渐变或强色散。用同一张有斜线的背景做「折射关／开」两版对照，除折射外其余参数保持一致。

先实现不依赖折射的静态版本，再增强。若使用 [Glasswork](https://github.com/kubai087/glasswork)，固定所用版本，不把 `lens.js` 当成跨浏览器方案。不支持折射时保留静态可读的样式；用户开启减少动态效果时不要播放材质动画。

交付桌面端对照截图，核对浅色和复杂背景下的文字对比度、键盘焦点与点击行为。分别列出实际测过的浏览器、降级结果和未测项；不要把模拟预览写成 iPhone 实测。

### 胶囊动效与空状态审核

以下使用合成数据，是设计审核要求，不是生产上线或接口验证。

```text
@kubai-empty-states

审核一个案例检索工作台。用户的主路径是「搜索案例 → 筛选测试状态 → 打开证据 → 回到原表坐标」。只读现有代码和界面，先出方案，等我确认再改；仅用合成数据，不部署。

1. 拆状态。按位置输出「当前表现｜触发条件｜展示文案｜唯一首选动作｜验收」。区分：查询中、成功有结果、成功零匹配、请求失败、队列为空、证据未关联、证据加载失败。只有后端明确且允许披露时才显示不存在或无权限；不要按空数组把不同状态合并。
2. 定层级。固定搜索栏、状态栏、表头和列宽。结果零匹配用一行提示；失败在原处重试；证据缺项只影响证据抽屉，保留 Sheet、单元格和测试结论。把模拟切换收进独立审核区，不混入正常检索。
3. 定材质和动作。保留现有设计系统与系统字体。玻璃只给选中控件和抽屉顶栏；表格、波形、正文用实底。胶囊滑动从 210ms 试起；空态约 300ms 淡入上移 6px、约 180ms 淡出。系统要求减少动效时取消位移。不新加依赖、不做旋转流光。
4. 交验收方案。用合成的 示例 A 记录演示：切 PASS → 0 条，清除筛选 → 1 条且关键词保留；模拟失败 → 条数未知 → 重试成功；切换 A/B 查询时只接受最后一次响应；缺证据仍可定位原表。再验证 0↔1 条时表头和列宽不跳、键盘焦点不丢、读屏能播报结果、窄屏控件可操作。把已验证、待验证和纯模拟分开写。
```

## 2. 按近期使用结果整理的可复制补充词

下面是独立的复用整理，不是 Apple 官方提示词，也不是第三方教程的逐字转载。

### Apple / macOS 风格 · 通用排版与控件

> 把页面分成不透明的内容层和轻量的操作层。用白或柔和的浅底、近黑主字、字重和留白建立层级；不要冷蓝正文、石墨背景或大面积渐变。优先使用系统字体：Apple 设备交给系统字体及苹方回退，Windows 用本机 Segoe UI 和微软雅黑回退，优先对齐字号、字重、行高与控件密度，不嵌入或分发 Apple 字体。只有导航、搜索或当前选中控件可用玻璃；数据、公式、截图和原文不受模糊遮挡。保持键盘焦点、触控范围和阅读顺序。用相同内容给出实底、轻磨砂、轻折射三态，标明已测与未测设备。

### 按钮反馈 · 一次轻移（可选，不作默认）

> 保留搜索栏、左侧状态筛选和结果表布局。只在主动点击／选中时，让一小段高光在该胶囊上沿横向轻移一次并停住；不沿边绕圈、不循环、不把高光扩散到其他控件。光层不拦截操作，不替代静态键盘焦点。关闭动效后，选中仍有文字或边界提示；请求失败不显示成零条，证据加载失败只在证据位重试。若任务只验收磨砂与折射，关掉这层。此为按实际设计要求整理的轻移方案，不是对 Tirz 原件的逐帧复刻。

### Logo 材质 · 线条本身是玻璃

> 使用一个为演示选定的品牌基色绘制 Logo 线条。透光、轻磨砂和细边缘折射只发生在轮廓内；背景不染色、不模糊，字标固定。不通过左右摆头或整体旋转伪造本体翻转；小尺寸以清楚的线条为优先。用测试斜线验证轮廓内才发生偏折，正式素材移除测试线和背景。若交付的是预渲染加载素材，明确不是对网页背景的实时折射；给减少动效用户静态稿，并按实际显示尺寸验证清晰度。不把预览写成已部署。

## 3. 原出处、项目与库内现有条目

| 原出处 | 看什么 |
| --- | --- |
| [Apple HIG：Materials](https://developer.apple.com/design/human-interface-guidelines/materials) · [Typography](https://developer.apple.com/design/human-interface-guidelines/typography) | 内容和操作控件的材质区分、文本层级与清晰度。 |
| [Apple WWDC：Meet Liquid Glass](https://developer.apple.com/videos/play/wwdc2025/219/) · [Get to know the new design system](https://developer.apple.com/videos/play/wwdc2025/356/) · [Landmarks](https://developer.apple.com/documentation/swiftui/landmarks-building-an-app-with-liquid-glass) | 学原生导航与材质关系，不把 SwiftUI 当作网页实现。 |
| [NetNewsWire 7 for Mac](https://netnewswire.blog/2026/01/27/netnewswire-for-mac.html) · [源码](https://github.com/Ranchero-Software/NetNewsWire) | 参考来源、列表、正文的层级；切换时保住阅读上下文。 |
| [ThanasOS 源码](https://github.com/Thanas-R/thanas-os) | 只参考 Web 上的 macOS 式搜索、焦点和键盘体验，不照搬 Dock 或壁纸。 |
| [Glasswork 演示](https://www.kubai.design/glasswork/) · [源码](https://github.com/kubai087/glasswork) · [固定版本浏览器分支](https://github.com/kubai087/glasswork/blob/4f0b6744b898b3a9b98fbd913ab24fdb83c53162/playground.js#L773-L841) | CSS 磨砂、Chromium 边缘位移，以及基于受控背景的 WebGL2 路径。 |
| [Open Design：产品界面色值](https://github.com/nexu-io/open-design/blob/main/apps/web/src/styles/tokens.css) · [中文排版](https://github.com/nexu-io/open-design/blob/main/craft/typography.md#cjk-overrides--these-are-not-optional) | 区分产品界面与生成简报默认值；长文与中文排版单独检查。 |
| [Emil Kowalski 的 apple-design Skill](https://github.com/emilkowalski/skills/blob/main/skills/apple-design/SKILL.md) · [枯白空状态原文](https://vibedesign.tips/zh/022-empty-states/) | 两份都是第三方资料，不是 Apple 官方；用于设计检查与空态分流。 |
| [Microsoft Windows 材质](https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/materials) · [MDN backdrop-filter](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/backdrop-filter) | 原生 Mica／Acrylic 与网页磨砂各自的边界，不等同于边缘折射。 |
| [Magic UI Border Beam](https://magicui.design/docs/components/border-beam) | 仅作流光对照，不用于复刻当前的一次横向轻移。 |

**库内去重**：原 CSS、固定版本 JS 和许可见 [Glasswork 液态玻璃调用卡](Glasswork-999/Glasswork-液态玻璃材质-调用卡.md)；浏览器分支看 [第 06 课](Glasswork-999/2026-11-23-06-browser-refraction.md)；不打断阅读的侧栏进出场看 [第 02 课](Glasswork-999/2026-11-19-02-panel-glide.md)。原作者的素材、壁纸、字体和代码按各自条款使用，不能因为本卡链接它们就默认可重新分发。

**最低验收**：同一背景只切一个变量，观察边缘细线是否偏移而窗外仍清楚；在 Windows Edge 和 iPhone Safari 分开测，折射不可用时保留同尺寸磨砂，需要时回到实底；检索、表格、原文、键盘和触屏在动效禁用时仍可使用。仅作提示词与资料归档，不代表任何网站已修改、已发布或通过真机验证。
