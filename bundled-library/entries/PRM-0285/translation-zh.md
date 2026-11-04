请使用“Whip pan”（ホイップパン），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #043

定义：用快速摇镜的模糊衔接下一个镜头。
示例展示：相机非常快速地横甩，在条纹状模糊最强时换入下一个场景。
规格：
- 衔接持续 0.8 s，即 1.7–2.5 s；前 0.4 s 前一镜头甩出，后 0.4 s 后一镜头甩入并稳定。
- 前半段，前一镜头 yaw 从 0 到 +0.45 rad，约 26°，采用二次 ease-in-out；后半段，后一镜头 yaw 从 −0.45 rad 到 0，采用相同缓动。
- 在 50% 进度处直接替换场景，最强模糊将这个硬切隐藏。
- 模糊通过平均 9 次渲染实现，采样分布在 ±1.6 帧范围内，帧率为 30 fps。
- 相机高度 1.4 m，甩动之外均固定；主体不动，A 中为人物，B 中为汽车与城市。
- 每 4.7 s 交替 A→B 和 B→A，完整往返为 9.4 s；右上角显示 A → B 或 B → A。
何时使用：用于在保持高能量的同时更换地点或话题。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/043.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
