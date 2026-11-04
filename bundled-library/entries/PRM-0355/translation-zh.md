请使用“High-key”（ハイキー），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #113

定义：明亮、白色调、阴影很浅的画面。
示例展示：风景和人物转为接近白色的浅色，阴影很淡，右下直方图的峰移到右端。
规格：
- 场景3：左侧是半身像，头部中心(x=140,y=82)、半径28 px；右侧是山丘、房屋、树和太阳，太阳(x=432,y=54)、半径15 px。
- 颜色：天空#FAF9F7→#FFFFFF，山丘#EAEDF1→#F5F6F8，人形#4D5A75→#B9C0CE，阴影#33405A→#A6AEBF，太阳#F5A524→#FFD889。
- 直方图96×46 px，共20根条：峰中心0.56→0.85，宽度0.2→0.09。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：干净、明亮、柔和的产品图与人像。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/113.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
