请使用“Locked-off shot”（ロックオフ），它是“Camera moves & transitions, part 2”中的一个名称。
Motion Prompt #175

定义：摄像机固定，只有主体移动
示例展示：人物在三脚架固定的摄像机前横穿，后方汽车驶过；摄像机没有任何像素位移。
规格：
- 摄像机：完全固定，高度1.4 m、朝正前方、焦距330 px；只有主体运动。
- 主体：人物在前方6.5 m处以恒速从左向右横穿，4.7 s内x = -6.2 m → +6.2 m；双腿和双臂按sin(u×7)×0.42 rad摆动。
- 灰色汽车在15 m远处从右向左驶过，4.7 s内x = +16 m → -16 m。
- 两者均在画面外开始、在画面外结束，因此每4.7 s无缝循环。
- 左下有灰色三脚架图标，右上读数显示“LOCKED”（#040 Freeze frame停止的是影像时间；本例时间继续，只有摄像机静止）。
何时使用：通过动静对比突出主体，进行定点观察，或作为延时摄影与合成的基础。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/175.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
