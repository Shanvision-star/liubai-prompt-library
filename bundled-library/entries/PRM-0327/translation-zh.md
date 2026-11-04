请使用“Ripple effect”（リップルエフェクト），它是“Landing page & web effects”中的一个名称。
Motion Prompt #085

定义：涟漪从被按下的位置扩散。
示例展示：每次点击从点击点扩散一个白色圆，铺满按钮后淡出。
规格：
- 按钮280 × 56，橙色、圆角半径10；在0.7 s点击中心左侧，2.9 s点击中心右侧。
- 圆以点击点为中心，半径在0.6 s内从0增至点击点到按钮最远角的距离，使用cubic ease-out。
- 白色圆初始不透明度0.4，在点击后0.3–0.8 s淡至0。
- 圆被裁切在按钮内部，对应overflow:hidden；文字位于其上层。
何时使用：在按钮或列表项被按下的位置提供确认反馈。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/085.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
