请使用“Dolly zoom (Vertigo)”（ドリーズーム），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #032

定义：主体保持原样，背景发生形变。
示例展示：相机后退，同时按相同比例拉长焦距；人物大小不变，只有背景向人物逼近。
规格：
- 人物位于前方 8 m，相机与其距离 d 从 3.2 m 增至 8 m，相当于后移 4.8 m；相机高度 1.3 m。
- 焦距 f = 330 × d/8 px，即 132 px → 330 px，显示为 10mm → 24mm；使距离 ÷ 焦距保持恒定。
- 0.5–3.4 s 运动，历时 2.9 s，采用三次 ease-in-out，约为 cubic-bezier(0.65,0,0.35,1)。
- 人物不动，在画面中的高度保持一致；头部高度 1.8 m 与脚部处各有宽 160 px 的蓝色虚线，显示大小不变。
- 背景：48 m 外建筑约放大 2.2 倍，远山约放大 2.4 倍，像从人物背后逼近；人物前方地面则缩小。
- 复位：3.4–4.2 s 停留，最后 0.5 s 交叉淡化回起点；一遍为 4.7 s。
何时使用：用于顿悟时刻，或以视觉方式表现不安和震惊。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/032.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
