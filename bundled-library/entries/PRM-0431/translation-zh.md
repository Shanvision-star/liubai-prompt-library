请使用“Cutaway”（カットアウェイ），它是“Camera moves & transitions, part 2”中的一个名称。
Motion Prompt #189

定义：切向其他对象，然后切回
示例展示：从演讲者切到聆听的观众再切回；中间插入的是另一主体。
规格：
- 剪接：两次硬切，转场为0帧；1.7 s切向另一主体，3.0 s切回原场景，离开主镜头1.3 s。
- 主镜头A：固定摄像机，高度1.4 m；人物在5.5 m远处讲话，双臂和双腿按0.45·sin(u×6) rad摆动，右侧0.9 m处有灰色讲台。
- 另一主体CUTAWAY：聆听的观众，五个人位于3.1–4.6 m处，身穿蓝色和浅蓝色，双臂举起，按|sin(t×9+i)|×5 cm上下弹动；没有背景，表示另一处空间。
- 底部条分为A（灰）、另一主体（蓝）、A（灰），并有播放头（原文“17 Insert shot”展示同一场景的细节）。
- 右上角读数为“SHOT A” → “CUTAWAY” → “SHOT A”；4.7 s时硬切回起点。
何时使用：表现反应，或掩盖跳时与删去口误的剪接。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/189.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
