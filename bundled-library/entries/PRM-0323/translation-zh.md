请使用“Hover lift”（ホバーで浮き上がる），它是“Landing page & web effects”中的一个名称。
Motion Prompt #081

定义：悬停时元素升起，阴影加深。
示例展示：只有光标下的卡片略微抬起，阴影扩散；光标移开后回落。
规格：
- 三张卡片各146 × 128、圆角半径10；光标按从左到右顺序在每张卡片上停留约1 s。
- 悬停时卡片在0.3 s内上升10 px，使用cubic ease-out；移开后用相同0.3 s回位，类似CSS transition。
- 阴影随抬升一起变化：模糊6→22 px，y偏移2→12 px，不透明度0.08→0.22。
- 页面浅灰、卡片白色，以便看清阴影。
何时使用：让卡片和按钮显得可以点击。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/081.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
