请使用“Smooth scroll”（スムーススクロール），它是“Landing page & web effects”中的一个名称。
Motion Prompt #093

定义：同页链接平滑滑至目标，而不是直接跳转。
示例展示：点击菜单“价格”后，页面平滑滑至价格区；右下角向上箭头再将页面平滑带回顶部。
规格：
- 0.9 s点击“Pricing”菜单项；0.95–2.0 s滚动量从0→296 px，持续1.05 s，使用cubic ease-in-out。
- 停留位置=价格区顶部330 px − 固定页头高度34 px。
- 滚动超过60 px后，右下角半径15的圆形回顶按钮在接下来的40 px滚动区间内淡入。
- 3.1 s点击该按钮；3.15–4.2 s滚动量从296→0，使用cubic ease-in-out。
- 价格区在视野内时，菜单里的“Pricing”变橙色。
何时使用：菜单或目录在同页跳转时，让读者看清目标位置的关系。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/093.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
