请使用“Before/after slider”（ビフォーアフタースライダー），它是“Landing page & web effects”中的一个名称。
Motion Prompt #087

定义：拖动分界线，比较前后效果。
示例展示：左右拖动照片中央分界线，改变左侧灰色“之前”和右侧彩色“之后”的可见比例。
规格：
- 照片框359 × 140，圆角半径10。右侧为彩色处理后照片；左侧为同一照片的处理前版本，去饱和并叠加不透明度0.18的深蓝色。
- 处理前图像裁切在分界线左侧；线上有宽3的白线和半径17、带左右箭头的白圆。
- 0.7 s抓住白圆；分界从50%→20%（0.75–1.55 s）→82%（1.55–2.65 s）→50%（2.65–3.55 s），均为cubic ease-in-out。
- 3.62 s释放；左上标BEFORE，右上标AFTER。
何时使用：展示装修、美容或照片修饰等改变前后的页面。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/087.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
