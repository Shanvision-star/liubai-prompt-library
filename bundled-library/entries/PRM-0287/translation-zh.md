请使用“Wipe”（ワイプ），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #045

定义：移动的边界替换镜头。
示例展示：一条竖直边界从左向右移动，边界经过后下一个画面替换当前画面。
规格：
- 衔接为 1.7–2.8 s，持续 1.1 s；边界从画面左外侧 x = −4 px 移到右外侧 x = 543 px。
- 采用三次 ease-in-out，约为 cubic-bezier(0.65,0,0.35,1)。
- 边界左侧显示下一画面，右侧显示前一画面；两幅画面自身都不移动，这是裁剪揭示，不是推移。
- 边界为宽 4 px 的蓝色竖线，仅在移动时可见。
- 两幅画面中相机固定，主体也都不动。
- 每 4.7 s 交替 A→B 与 B→A，完整往返为 9.4 s；右上角显示 A → B 或 B → A。
何时使用：用于明确标记场景或话题变化，或切换对比的两个方面。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/045.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
