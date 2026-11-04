请使用“Light sweep”（ライトスイープ），它是“Motion graphics moves”中的一个名称。
Motion Prompt #022

定义：一条光带扫过表面。
示例展示：一条倾斜光带扫过标志徽章的表面。
规格：
- 每 2.35 s 扫光一次；光只画在徽章形状的裁剪范围内，徽章为 400 × 112、圆角半径 28、蓝色渐变。
- 光带是宽 116 px 的白色渐变，中间不透明度 0.72、两端为 0；另有相距 78 px、宽 12 px、不透明度 0.5 的细光带，两者倾斜 0.42 rad，约 24°。
- 0.45–1.5 s 内，光从徽章左侧外 130 px 移到右侧外 130 px，总距离 660 px，采用二次 ease-in-out。
- 闪光：1.38–1.98 s，右上角出现四角星；尺寸为 30 × sin(πq) × (1 + 0.2(1 − q))，旋转 0.9 rad。
- 徽章本身不移动。
何时使用：用于为标志、徽章或按钮增加精致质感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/022.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
