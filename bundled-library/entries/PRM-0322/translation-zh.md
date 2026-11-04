请使用“Highlighter animation”（マーカーアニメーション），它是“Landing page & web effects”中的一个名称。
Motion Prompt #080

定义：在关键词下方绘出荧光笔划。
示例展示：文案滚入视野时，黄色荧光笔划从左到右扫过关键词的下半部。
规格：
- 滚动量在0.35–1.0 s从0→90 px，1.6–2.2 s从90→180 px，3.3–4.4 s从180→0，使用cubic ease-in-out。
- 两行20 px粗体文案分别位于页面纵向190 px和290 px，初始藏在视野下方。
- 每行顶边经过触发线（视口高度80%，即134 px）时，其关键词下方开始绘制笔划。
- 笔划为黄色#FFE36B，高11，位于文字下半部（基线上方8 px至下方3 px）；宽度在0.8 s内从左侧0增至词宽，使用cubic ease-out，绘制在文字后面。
- 离开视口底部的行在视野外重置。
何时使用：落地页文案被读到时，突出最重要的短语。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/080.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
