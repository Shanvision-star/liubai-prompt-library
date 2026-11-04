请使用“Black and white”（モノクロ），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #115

定义：去除色彩，只显示明暗。
示例展示：同一风景的色彩褪去，太阳和人物受光处都变成灰色，仅凭亮度读出形状。
规格：
- 场景3：左侧是半身像，头部中心(x=140,y=82)、半径28 px；右侧是山丘、房屋、树和太阳，太阳(x=432,y=54)、半径15 px。
- 转换：每种颜色变为其亮度对应的灰色，亮度公式0.2126R + 0.7152G + 0.0722B；围绕140将对比度乘以1.25。
- 例如人形#4D5A75→约#4D4D4D，太阳#F5A524→约#B5B5B5。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：营造不过时的感觉，或让形状、光线、表情比颜色更重要。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/115.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
