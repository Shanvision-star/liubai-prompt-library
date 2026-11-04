请使用“FPV drone shot”（FPV），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #035

定义：快速、沉浸式地飞行穿越。
示例展示：第一人称视角低空高速飞过两排树之间，并左右倾斜。
规格：
- 相机以恒定 14 m/s 向前飞行，显示为 50km/h，不使用缓动；pitch 固定为 −0.05 rad。
- 摆动：T = 2π×u/4.7，每 4.7 s 摆动两次；横向位移为 0.6·sin(2T−0.4) m，高度为 1.4 + 0.5·sin(2T) m。
- 侧倾：roll = 0.22·sin(2T+0.6) rad，约 ±12.6°；yaw = 0.05·sin(2T) rad，约 ±2.9°。
- 没有独立主体。树高 4.2 m，位于左右各 3.6 m 处，每隔 8 m 一棵，两排相互错开 4 m，快速朝相机冲来。
- 速度线为 10 条半透明灰色放射线，长约 32–76 px，越靠两侧越长；向外流动并循环再生。
- 没有停留和交叉淡化复位；每 4.7 s 重新开始时，两排树的相位会发生变化。
何时使用：用于表现速度与沉浸感，或以一次连续运动穿过一个地点。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/035.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
