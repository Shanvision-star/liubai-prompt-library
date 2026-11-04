请使用“Scroll-down cue”（スクロールダウンの合図），它是“Landing page & web effects, part 2”中的一个名称。
Motion Prompt #167

定义：循环提示，引导用户向下滚动。
示例展示：首屏下方的“SCROLL”、鼠标轮廓内圆点和两侧箭头持续重复向下运动。
规格：
- 视口511×168，首屏下方居中放置“SCROLL”，字号11 px、字距3 px，以及24×38鼠标轮廓，圆角半径12、线宽2.2。每拍1.57 s，4.7 s内三拍、9.4 s包周期内六拍。
- 内部橙色点为5×9，在每拍前70%内以二次ease-in-out向下移动14 px，45%–75%期间淡出，下拍在顶部重现。
- 左右各距40 px，每侧两个向下箭头，线宽2.5，彼此错开半拍，向下漂移24 px；不透明度按正弦0→0.8→0变化。
何时使用：首屏铺满屏幕，需要提示页面下方还有内容时使用。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/167.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
