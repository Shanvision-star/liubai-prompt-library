请使用“Kinetic typography”（キネティックタイポグラフィ），它是“Motion graphics moves”中的一个名称。
Motion Prompt #008

定义：词语随所说内容的节奏移动、缩放与旋转。
示例展示：词语按自身含义运动：一个拉伸、一个弹跳、一个旋转、一个猛然落下。
规格：
- 四个词各展示 1.175 s，采用 88 px 粗体；每个词在最后 0.2 s 一边渐隐一边向上移动 46 px，采用三次 ease-in。
- Stretch（蓝色）：水平缩放从 0.3 到 1，使用弹簧 1 − e^(−4.2t)·cos(12t)；竖直缩放为 1/√(水平缩放)。
- Bounce（黄色）：字符错开 0.1 s；弹跳高度为 78 px × |sin(πt/0.4)| × e^(−2.6t)；每次接触地面时竖直方向最多压扁 16%。
- Spin（薄荷绿）：字符错开 0.12 s；在 0.62 s 内以 backOut（s = 1.3）从 −360° 转至 0°；缩放在 0.25 s 内以三次 ease-out 从 0 变为 1。
- Slam（珊瑚色、100 px、倾斜）：0.02–0.2 s 以三次 ease-in 将缩放从 3.4 减至 1。
- 冲击后：横向震动为 10 px × e^(−9t) × sin(38t)，竖向压扁为 20% × e^(−11t)，并显示 8 条放射线 0.4 s。
何时使用：用于通过运动方式加强旁白或歌词中关键词的记忆点。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/008.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
