请使用“Teal and orange”（ティール＆オレンジ），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #117

定义：将阴影推向青绿，将肤色与高光推向橙色。
示例展示：同一风景的天空、山丘、地面和阴影中的人形转为青绿色，人物受光边和太阳转为橙色，形成互补对比。
规格：
- 场景3：左侧是半身像，头部中心(x=140,y=82)、半径28 px；右侧是山丘、房屋、树和太阳，太阳(x=432,y=54)、半径15 px。
- 青绿色：天空#CFE6E3，山丘#8CC1BE和#62A2A1，地面#3F8083，树#2F6A6E，人形#1D4E53。
- 橙色：人物受光处#FF9248，太阳#FF8236，太阳光环#FFC48C。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：用于色彩对比强烈的大片或预告片观感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/117.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
