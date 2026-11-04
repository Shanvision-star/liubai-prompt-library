请使用“Fade-in on scroll”（スクロールでフェードイン），它是“Landing page & web effects”中的一个名称。
Motion Prompt #074

定义：元素滚入视野时淡入。
示例展示：滚动页面时，标题、卡片和正文进入视野后各自向上就位并淡入。
规格：
- 滚动量在0.35–1.0 s从0→95 px，1.5–2.1 s从95→200 px，3.2–4.4 s从200→0，均为cubic ease-in-out。
- 触发线位于视口高度85%处，即距顶部143 px；元素顶边越过此线上方时触发，体现Intersection Observer的思路。
- 触发后在0.7 s内，不透明度0→1，向下28 px的偏移→0，使用cubic ease-out。
- 三个元素分别是页面纵坐标172 px的标题、206 px处的一排三张卡片和334 px处的正文，初始都在视野下方；同排卡片同时出现。
- 向上回滚时，离开视口底部的元素在看不见处重置，下次再进入时重新播放。
何时使用：长落地页中，随读者滚动分批呈现内容。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/074.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
