请使用“Zoom through”（ズームスルー），它是“Motion graphics moves”中的一个名称。
Motion Prompt #020

定义：放大进入一个物体，并穿过它到达下一个场景。
示例展示：镜头冲入字母 O 的孔洞，并从孔洞穿到下一个场景。
规格：
- 场景 X 为黄色底的 ZOOM，场景 Y 为蓝色底的 GO!，按 X → Y → X 切换，每段 2.35 s。
- 围绕 O 孔洞的中心缩放当前场景，孔洞半径 24.5；最大缩放为孔洞刚好覆盖整个画面所需值的 1.08 倍，约 14 倍。
- 缩放 = maxScale^p，采用指数缩放，使它看起来具有恒定速度。
- p = 0.8 × 三次 ease-in（0.25–1.2 s）+ 0.2 × 三次 ease-out（1.2–1.65 s），表现为加速冲入、末尾减速。
- 孔洞内把下一场景缩小到 1/maxScale；缩放结束时，它恰好变为原始大小，随后切换到下一场景。
何时使用：用于钻入标志或字母内部，带着冲劲进入下一个场景。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/020.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
