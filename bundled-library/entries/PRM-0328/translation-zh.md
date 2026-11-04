请使用“Underline animation”（下線アニメーション），它是“Landing page & web effects”中的一个名称。
Motion Prompt #086

定义：悬停时，链接下划线从左侧伸长。
示例展示：光标所在链接下方，橙色线从左侧伸出；移开后，线向右侧收走。
规格：
- 三个20 px粗体链接，间隔56；光标从左到右各停约1 s，命中区域比文字左右各宽6 px。
- 下划线为橙色，厚3，位于基线下方8 px。
- 悬停时宽度在0.3 s内从左端0增至100%，使用cubic ease-out。
- 移开时左端在0.3 s内向右移动，线条从右侧退出，类似以右侧为transform-origin的scaleX。
何时使用：给菜单或文字链接提供安静的指针位置反馈。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/086.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
