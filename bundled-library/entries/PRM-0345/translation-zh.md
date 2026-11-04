请使用“Golden hour”（ゴールデンアワー），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #103

定义：日出后或日落前，低角度、温暖的光线。
示例展示：太阳降至地平线正上方，天空与地面变橙；人物左侧受光，路灯和树的影子向右拉长。
规格：
- 场景1：地平线位于y=150，前方为头肩人形；头部中心(x=270,y=78)、半径29 px，不画五官和头发。
- 太阳半径18 px，从(x=110,y=−30)移至(x=96,y=136)，被山丘遮住一半。
- 颜色：天空#FAF9F7→顶部#FFE8BC、地平线附近#FFCF80；地面#F1F0EE→#F6DDB0；人形亮部#FFB547，阴影#3E3650。
- 头部受左侧约66°光线照射，边界右侧为阴影；身体左亮右暗。
- 阴影从路灯和树根部向右延伸，长度0→150 px，颜色#DDAA6E；右上时间12:00→17:40。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：用于温暖、怀旧、柔和的画面。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/103.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
