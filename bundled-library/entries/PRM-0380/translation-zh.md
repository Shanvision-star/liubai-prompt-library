请使用“Blinds transition”（ブラインド），它是“Motion graphics moves, part 2”中的一个名称。
Motion Prompt #138

定义：下一场景通过细条带逐渐打开
示例展示：一排细条中的开口逐渐变宽，直至完全显露下一个场景。
规格：
- 日景→夜景→日景，每段2.35 s。画面划为七条水平条带，每条高208 ÷ 7，约29.7 px。
- 0.4–1.65 s内用二次ease-in-out完成1.25 s切换：所有条带同时从各自顶部向下显露下个场景，开口高度由0增至整条高度。
- 上一个场景保留在底下，两张画面都不移动。
何时使用：用于日夜、前后对比等清晰的双场景切换，也适合复古感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/138.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
