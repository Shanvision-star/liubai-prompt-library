请使用“Rack focus”（ラックフォーカス），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #033

定义：在近处与远处之间转移焦点。
示例展示：相机不移动，焦点从前景花朵转移到后方人物，两者的清晰与模糊关系互换。
规格：
- 相机位置、方向和焦距均固定，高度 1.1 m；只改变模糊量。
- 模糊：前景花朵位于左侧 0.75 m、前方 2 m，模糊由 0 px 变为 7 px；人物和背景由 6 px 变为 0 px，人物位于右侧 0.9 m、前方 9 m；地面网格使用背景模糊量的 0.6 倍。
- 1.0–2.6 s 变化，历时 1.6 s；采用三次 ease-in-out，约为 cubic-bezier(0.65,0,0.35,1)。
- 焦点标记：蓝色角括号沿直线从花朵移到人物，半宽从 46 px 缩至 30 px。
- 花朵与人物都不移动。
- 复位：2.6–4.2 s 停留，最后 0.5 s 交叉淡化返回；右上角对焦距离读数为 ◎ 2m → ◎ 9m。
何时使用：用于不切镜头就把注意力从前景移向背景，或反向转移。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/033.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
