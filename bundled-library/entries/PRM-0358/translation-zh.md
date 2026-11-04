请使用“Duotone”（デュオトーン），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #116

定义：以两种颜色呈现图像，一种对应暗部，另一种对应亮部。
示例展示：同一风景的颜色被替换成两种颜色之间的范围：暗部靛蓝，亮部粉红。
规格：
- 场景3：左侧是半身像，头部中心(x=140,y=82)、半径28 px；右侧是山丘、房屋、树和太阳，太阳(x=432,y=54)、半径15 px。
- 两端颜色：暗端#1F2A5C，亮端#FF9FB2。
- 转换：根据每种颜色的亮度L，t = ((L − 70) / 180)^2.4，再按t混合两色；这样会拉开亮调之间的差异。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：用品牌色统一海报、音乐封面或社交图片。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/116.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
