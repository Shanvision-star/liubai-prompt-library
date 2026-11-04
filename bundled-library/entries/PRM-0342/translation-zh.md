请使用“Split lighting”（スプリットライティング），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #100

定义：侧面来光将脸分为受光与阴影两半。
示例展示：光源从接近正面20°转到正侧面90°；头部阴影由月牙扩大到恰好一半，沿面部中线分开明暗。
规格：
- 场景1：地平线位于y=150，前方为头肩人形；头部中心(x=270,y=78)、半径29 px，不画五官和头发。背景转暗，天空为#E7E5E1。
- 光从画面左侧照来，角度20°→90°；右下有平面图，右上读数为“90° · ↑0°”。
- 头部：x = 270 + cos(angle)·√(29² − dy²)右侧为阴影#33405A，左侧为亮部#FFC75A；到90°时边界成为笔直的中心线。
- 身体半宽56 px；x = 270 + cos(angle)·56右侧为阴影，左边缘的一条带状区域受光。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：用于戏剧性、紧张或情绪浓郁的人像。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/100.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
