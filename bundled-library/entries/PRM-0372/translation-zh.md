请使用“Wave text”（ウェーブテキスト），它是“Motion graphics moves, part 2”中的一个名称。
Motion Prompt #130

定义：字母依次升降，像波浪一样
示例展示：“WAVE TEXT”的字母逐个上下起伏，像波浪一样。
规格：
- “WAVE TEXT”字号70 px、粗体、字距4 px；4.7 s内三次波动，每次1.567 s。
- 第i个字母的垂直位移 = −28·sin(φ − 0.62i)，其中φ = 2π × 3 × 时间 ÷ 4.7；每个字母比前一个滞后0.62 rad。
- 上升字母纵向拉伸为1 + 0.06·s，并从白色趋向黄色；s为正弦值，颜色计算时将其限制在0–1。
- 每个字母下方都有椭圆阴影，字母升高时阴影缩小。
何时使用：用于标志、短标题或配合音乐的字幕，增添趣味与节奏。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/130.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
