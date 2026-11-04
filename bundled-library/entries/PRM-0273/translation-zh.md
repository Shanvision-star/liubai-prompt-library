请使用“Crane up”（クレーンアップ），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #031

定义：将相机向上升起。
示例展示：相机升高的同时向下俯转，最终俯视人物。
规格：
- 相机高度从 1.4 m 升至 9 m，同时向前移动 0 m → 1.5 m。
- 镜头向下转以保持前方 8 m 的人物在画内；pitch = −0.86 × atan2(height − 1.0, 8 − forward)，约从 −2.5° 到 −44°。
- 0.5–3.4 s 运动，历时 2.9 s，采用三次 ease-in-out，约为 cubic-bezier(0.65,0,0.35,1)。
- 人物不动；相机升高时人物变小，地面网格占满画面，地平线从顶部离开。
- 复位：3.4–4.2 s 停留，最后 0.5 s 交叉淡化回起点；一遍为 4.7 s。
- 右上角高度读数为 ↑ 1.4m → ↑ 9.0m。
何时使用：用于在场景结尾从人物拉开，或揭示地点的广阔程度。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/031.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
