请使用“Panning shot”（流し撮り），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #108

定义：跟随移动主体，使只有背景形成拖影。
示例展示：相机跟随运动汽车：车保持在画面中央且清晰，身后建筑、树和路灯横向拖成条纹。
规格：
- 街角的建筑、树和灯位于y=132–162道路后方，没有大型前景人物。
- 没有效果时，汽车5 s内从x=−80驶至620；有效果时，汽车保持在x=270 ±10 px。
- 拖影：背景在横向46 px范围内重复绘制12次并求平均，展开范围从0→46 px。
- 轮辐线每5 s旋转12圈。
- 右上快门速度1/1000→1/15。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：在静态照片中表现汽车、自行车或跑者的速度。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/108.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
