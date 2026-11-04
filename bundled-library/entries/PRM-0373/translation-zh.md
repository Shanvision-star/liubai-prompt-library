请使用“Text on a path”（テキストオンパス），它是“Motion graphics moves, part 2”中的一个名称。
Motion Prompt #131

定义：文字沿直线或曲线流动
示例展示：一行文字沿波浪线流动，每个字母都转向跟随路径。
规格：
- 路径为y = 118 + 42·sin(2πx ÷ 330 + 0.6)，x范围−70至609；其下方6 px显示深蓝色虚线，虚线14/10、线宽5。
- 重复文字“ALONG THE LINE • ”，字号42 px、粗体、字距2 px。每个字符放在路径上对应弧长的位置，并旋转到路径方向。
- 每4.7 s文字沿路径推进一个完整字符串的长度，因此循环可以无缝衔接。
- 字母为白色，圆点为黄色。
何时使用：用于沿图形排布文字，例如环绕标志、沿道路、河流或波浪，或作为循环文字带。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/131.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
