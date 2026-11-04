请使用“Long take”（長回し），它是“Camera moves & transitions, part 2”中的一个名称。
Motion Prompt #172

定义：一个没有剪切的连续镜头
示例展示：一个连续镜头不切换地跟随行走人物；底部条始终是一条不间断的带状线。
规格：
- 剪接：无；连续4.2 s用同一个镜头跟随人物（#041 Jump cut则将其分成五段）。
- 主体：人物以恒速从左前方（x = -3.4 m，深度5.2 m）走向右后方（x = 2.8 m，深度9.6 m）；双腿和双臂按sin(t×7)×0.42 rad摆动。
- 摄像机：跟随人物向右横移0 m → 1.4 m，同时转向，yaw = atan2(person x - camera x, depth)×0.8；高度1.4 m。
- 底部条：一条带播放头的蓝色横条，标注“1ショット・カットなし”（一个镜头、无剪切），表示没有断点。
- 返回：4.2 s停止，最后0.5 s交叉淡化回起点；单次过程为4.7 s。
- 右上角读数显示已播放时间（NO CUT 0.0s → 4.2s）。
何时使用：维持连续的紧张感与现场感，或把一连串动作呈现为一个完整流动过程。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/172.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
