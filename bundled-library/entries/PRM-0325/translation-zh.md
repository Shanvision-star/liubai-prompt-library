请使用“Cursor follower”（マウスストーカー），它是“Landing page & web effects”中的一个名称。
Motion Prompt #083

定义：形状延迟跟随鼠标指针。
示例展示：光标在页面上移动时，橙色圆稍有延迟地跟随。
规格：
- 光标路径为x = 255 + 175·sin(2πt/4.8)，y = 86 + 46·sin(4πt/4.8)，即横卧的8字形，每4.8 s一圈。
- 圆半径17，橙色，不透明度0.88，绘制在光标下方。
- 跟随规则：每帧（60 fps）移动剩余距离的12%，即x += (cursor x − x) × 0.12。
- 箭头光标始终可见。
何时使用：品牌站或作品集增加活泼、可直接操控的感觉。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/083.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
