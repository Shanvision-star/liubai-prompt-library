请使用“Cross dissolve”（クロスディゾルブ），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #044

定义：将一个镜头混合过渡到下一个。
示例展示：把下一幅画面叠在当前画面上，不透明度逐渐升高直至完全替换；中途两幅画面互相透出。
规格：
- 衔接为 1.5–3.0 s，持续 1.5 s；下一画面的不透明度从 0 到 100%。
- 采用二次 ease-in-out，约为 cubic-bezier(0.45,0,0.55,1)，在 2.25 s 达到 50%。
- 前一画面保持完全不透明地铺在下层，下一画面叠在上层；不是先把前一画面淡出。
- 两幅画面中相机均固定，A 高度 1.4 m，B 高度 1.6 m、pitch 为 +0.1 rad；主体也不移动。
- 0–1.5 s 只显示前一画面，3.0–4.7 s 只显示下一画面。
- 每 4.7 s 交替 A→B 与 B→A，完整往返为 9.4 s；右上角显示 A → B 或 B → A。
何时使用：用于柔和地表现时间经过、地点变化，或进入回忆。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/044.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
