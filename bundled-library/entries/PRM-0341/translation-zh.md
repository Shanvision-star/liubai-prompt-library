请使用“Silhouette”（シルエット），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #099

定义：主体在明亮天空前呈现为黑色形状。
示例展示：以明亮傍晚天空为曝光基准时，人物、建筑、路灯和树变成无细节的黑色平面形状，只有天空保持明亮。
规格：
- 场景1：地平线位于y=150，前方为头肩人形；头部中心(x=270,y=78)、半径29 px，不画五官和头发。
- 天空从#FAF9F7变为顶部#FFEDC4，地平线附近y=92–150出现#FFCF73色带。
- 除天空外的所有物体变为#2A2D36，远山为#4A4546，人形为#22252D。
- 太阳半径20 px、x=404，从y=60沉至y=128，并被山丘遮住一半。
- 右上读数从±0.0 EV变为−2.0 EV。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：在日落或明亮窗户前，让形状和姿态成为画面主要表达。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/099.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
