请使用“Insert shot”（インサートショット），它是“Camera moves & transitions, part 2”中的一个名称。
Motion Prompt #185

定义：切入同一场景中的细节
示例展示：场景中插入人物腕上手表的大特写，持续1.3 s，然后返回同一个镜头。
规格：
- 剪接：两次硬切，转场为0帧；1.6 s切到细节，2.9 s切回场景，细节持续1.3 s。
- 主镜头A：固定摄像机，高度1.4 m；人物位于左侧0.6 m、距离6 m处，手腕上有以深色圆点表示的手表；立柱位于右侧2.2 m、距离4 m处。
- 细节INSERT：同一场景中的手腕大特写；浅蓝背景上，600×92 px蓝色袖子旋转-0.35 rad，白色表盘半径58 px，深色指针和蓝色秒针，秒针1.3 s转一圈。
- 底部条分为A（灰）、细节（蓝）、A（灰）三段并带播放头；插入的是同一场景的细节（原文“21 Cutaway”展示不同主体）。
- 右上角读数为“SHOT A” → “INSERT” → “SHOT A”；4.7 s时硬切回起点。
何时使用：展示小物件、手部动作，或强调重要道具。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/185.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
