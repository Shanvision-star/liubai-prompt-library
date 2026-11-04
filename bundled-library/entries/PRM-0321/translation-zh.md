请使用“Scroll progress bar”（スクロールプログレスバー），它是“Landing page & web effects”中的一个名称。
Motion Prompt #079

定义：顶部进度条显示你已读到哪里。
示例展示：文章分段滚动阅读时，顶部线条从左侧逐渐增长，到页面底部时延伸至最右端。
规格：
- 文章从0→430 px滚动，分为四个110 px步进，每次移动0.45 s、暂停0.4 s，使用cubic ease-in-out。
- 3.75–4.55 s从430→0返回。
- 视口顶部为6 px高的进度条，浅灰轨道、橙色填充。
- 填充宽度=511 px × scroll / 430，直接取滚动比例，等同于CSS animation-timeline: scroll()。
何时使用：长文章中显示尚有多少内容未读。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/079.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
