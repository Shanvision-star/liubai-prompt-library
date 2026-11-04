请使用“Chromatic aberration”（色収差），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #111

定义：高反差边缘上的红色与蓝紫色色边。
示例展示：街景分解为红、绿、蓝三份，以略微不同尺寸叠回，在人物、建筑和路灯边缘形成红青色边，越靠外侧越明显。
规格：
- 场景2：街角，建筑、树和路灯（x=114、292、494）位于y=132–162的道路后方；人物站在左前方，脚部(x=176,y=200)，身高124 px。
- 分离：图像分别乘以红#FF0000、绿#00FF00和蓝#0000FF得到三个副本，再在黑底上加法合成。
- 以画面中心缩放：红1 + 2s，绿1 + s，蓝1；s从0→0.02。
- 左右边缘红蓝最终相距约11 px，中心偏移为0。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：增添不完美的旧镜头、VHS或故障感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/111.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
