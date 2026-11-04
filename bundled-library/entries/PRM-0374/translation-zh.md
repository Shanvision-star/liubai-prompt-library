请使用“Variable font animation”（可変フォントアニメーション），它是“Motion graphics moves, part 2”中的一个名称。
Motion Prompt #132

定义：字母的字重平滑变化
示例展示：同一个单词在细体与特粗体之间平滑往返，下方滑块显示当前字重。
规格：
- “MOTION”字号112 px，system-ui字体，字距2 px。字重在4.7 s内往返两次：v = 0.5 − 0.5·cos(2π × 2 × 时间 ÷ 4.7)，两端均有缓动。
- 字重 = round(100 + 800v)，范围100至900，直接设为font weight。
- 下方滑块位于x = 112→427、y = 180，左侧标细、右侧标粗；黄色滑块圆点半径14，跟随v移动，上方显示当前字重。
何时使用：用于标题、标志或单个词，通过字母本身表达响度或情绪。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/132.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
