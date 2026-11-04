请使用“Magnetic button”（マグネティックボタン），它是“Landing page & web effects”中的一个名称。
Motion Prompt #084

定义：按钮被拉向附近的光标。
示例展示：光标靠近时，按钮被吸向光标并跟随；光标离开后，按钮摇摆着回到原位。
规格：
- 中央橙色按钮168 × 52、圆角半径26；吸引范围为距按钮中心半径110 px。
- 范围内的目标偏移=(cursor − button centre) × 0.35；每帧（60 fps）按钮向目标移动剩余距离的18%。
- 离开范围时，从当前偏移在1.1 s内返回0，使用elastic.out(1,0.3)：2^(−10x)·sin((x − 0.075)·2π/0.3) + 1。
- 光标从左进入，绕按钮移动，再从右离开。
何时使用：突出最希望被点击的按钮，如注册或联系。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/084.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
