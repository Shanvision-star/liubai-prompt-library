请使用“Low-key”（ローキー），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #114

定义：只有受光部分突出的暗调画面。
示例展示：大部分画面沉入暗处，太阳消失；半身像右侧被侧光照亮的边缘仍明亮，直方图峰移到左端。
规格：
- 场景3：左侧是半身像，头部中心(x=140,y=82)、半径28 px；右侧是山丘、房屋、树和太阳，太阳(x=432,y=54)、半径15 px。
- 颜色：天空#FAF9F7→#2B2D33，山丘变为#313339和#36383E，地面→#24252A，人形→#25272E；太阳及光环取天空色而消失。
- 半身像右侧受光边缘保留，颜色#FFC75A→#FFB547。
- 直方图峰中心0.56→0.14，宽度0.2→0.08。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：用于奢华、紧张或神秘的画面。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/114.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
