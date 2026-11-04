请使用“Dolly in”（ドリーイン），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #027

定义：让相机朝主体移动。
示例展示：相机本体向主体靠近；近景物体迅速变大并掠过，远山几乎不变。
规格：
- 相机沿景深方向前移 0 m → 5.8 m；高度 1.5 m，方向和焦距固定，焦距为 330 px，读数显示 24mm。
- 时间为 0.5–3.4 s，历时 2.9 s；采用三次 ease-in-out，约为 cubic-bezier(0.65,0,0.35,1)。
- 人物静止在前方 8 m；相机与人物距离从 8 m 变为 2.2 m，所以人物约放大 3.6 倍。
- 视差：左侧 1.5 m、深度 3.6 m 的前景柱和右侧 1.6 m、深度 4.8 m 的石头掠出画面；120 m 以外的山体大小几乎不变。
- 复位：3.4–4.2 s 停留，最后 0.5 s 交叉淡化回起点；一遍为 4.7 s。
- 右上角焦距读数始终为 24mm，这是与包内 04 Zoom in（全库 #028）的区别。
何时使用：用于靠近人物或细节，同时保留空间纵深感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/027.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
