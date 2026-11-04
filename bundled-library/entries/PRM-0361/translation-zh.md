请使用“Light leak”（ライトリーク），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #119

定义：红橙色辉光，仿佛光漏到了胶片上。
示例展示：同一风景右缘出现漏光带，内侧浅黄、边缘红色，并缓慢摇摆。
规格：
- 场景3：左侧是半身像，头部中心(x=140,y=82)、半径28 px；右侧是山丘、房屋、树和太阳，太阳(x=432,y=54)、半径15 px。
- 形状为四个高椭圆，中心在右边缘外30 px，循环中左右摇摆±6 px；竖直半径为画面高度的1.1倍。
- 水平半径与颜色依次为250 px、#FFD089、35%；170 px、#FF9A3D、40%；95 px、#FF5A3A、45%；45 px、#FF3B30、50%。每个半径从0增至该值。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：营造怀旧、夏日、偶然拍下的记忆感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/119.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
