请使用“Orbit (Arc shot)”（オービット），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #030

定义：围绕主体绕行。
示例展示：相机围绕主体沿圆周运动；人物保持居中，背后的树和建筑横向掠过。
规格：
- 相机以位于前方 9 m 的人物为圆心，在半径 6 m 的圆周上从 −0.95 rad 移到 +0.95 rad，即 −54° 到 +54°，总计约 109°。
- 方向始终朝向圆心，yaw = −angle；相机高度 1.7 m，pitch 固定为 −0.07 rad，约向下 4°。
- 0.5–3.6 s 运动，历时 3.1 s，采用三次 ease-in-out，约为 cubic-bezier(0.65,0,0.35,1)。
- 人物不动；脸上的白点随角度横移；地面以半径 1.3 m 的虚线圆作标记。
- 背景有 12 棵树，均匀分布在半径 10 m 的圆上；相机环绕时它们从人物背后穿过。
- 复位：3.6–4.2 s 停留，最后 0.5 s 交叉淡化返回；右上角读数显示 −54° → +54°。
何时使用：用于立体展示人物或产品，或强调登场和关键时刻。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/030.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
