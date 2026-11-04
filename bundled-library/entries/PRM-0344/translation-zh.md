请使用“Butterfly lighting”（バタフライライティング），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #102

定义：正面高处来光，在鼻子下方投出蝴蝶形阴影。
示例展示：正前方高处的灯亮起，面部两侧均匀受光，只在下巴下面留下小而对称的阴影。
规格：
- 场景1：地平线位于y=150，前方为头肩人形；头部中心(x=270,y=78)、半径29 px，不画五官和头发。背景转暗，天空为#E7E5E1。
- 头部全部使用亮色#FFC75A，没有阴影侧。
- 下巴阴影是椭圆，中心y = 78+1.06R，宽0.72R、高0.38R；R=29，约21×11 px，颜色#33405A。
- 身体中心±0.8×56 px范围受光，外侧细条保留基底色；平面图灯在相机侧0°，右上读数“0° · ↑45°”。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：用于修饰面部的美容与时尚人像。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/102.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
