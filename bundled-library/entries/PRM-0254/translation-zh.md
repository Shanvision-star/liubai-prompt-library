请使用“Shape morph”（モーフィング），它是“Motion graphics moves”中的一个名称。
Motion Prompt #012

定义：一个形状平滑地变成另一个。
示例展示：图形及其颜色平滑地从圆变成方形、星形和心形。
规格：
- 四种图形各占 1.175 s：圆 → 角部略圆的方形 → 星形 → 心形 → 回到圆；基准半径 64。
- 每段先停留，然后从该段 0.62 s 起到结束前 0.04 s 之间变为下一个图形，规格标注这一变形段为 0.58 s。
- 每个轮廓保存为 240 个点；将相同索引的点做线性插值。进度采用 backOut（s = 1.6），所以会有轻微过冲。
- 颜色按蓝 → 珊瑚 → 黄 → 薄荷绿变化，以二次 ease-in-out 混合。
- 变形期间，缩放膨胀为 1 + 0.07 × sin(π × progress)。
- 下方有四个圆点，当前图形对应的圆点更大且带颜色。
何时使用：用于不经剪切地把一个图标或标志变成另一个。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/012.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
