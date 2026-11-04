请使用“Film grain”（フィルムグレイン），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #118

定义：覆盖图像的细腻胶片状颗粒。
示例展示：同一风景表面出现细颗粒，整体颜色略偏温暖奶油色。
规格：
- 场景3：左侧是半身像，头部中心(x=140,y=82)、半径28 px；右侧是山丘、房屋、树和太阳，太阳(x=432,y=54)、半径15 px。
- 颗粒为2,600个方块，固定随机种子，尺寸0.8–1.7 px；55%为深色#3A3530，45%为白色。
- 颗粒不透明度为16%–38%乘以效果量；颗粒不移动，不闪烁。
- 每种颜色向#F2DDBE移动16%。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：减轻过于干净的数字感，增加模拟胶片纹理。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/118.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
