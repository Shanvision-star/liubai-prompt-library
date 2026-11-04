请使用“Tilt-shift”（ティルトシフト），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #106

定义：模糊上、下部分，使真实场景看起来像微缩模型。
示例展示：街景上、下方带状区域模糊，中间道路、汽车和小人物所在区域保持清晰，使街道像模型。
规格：
- 街角中，建筑、树和灯在y=132–162道路后方，不放大型前景人物；四个23–26 px高的小人在路面上，脚部y=172；汽车每5 s从x=−60驶至600。
- 清晰焦带为y=66–176。
- 模糊：y=0–42与y=190–208从0→7 px；y=42–66与y=176–190从0→3 px。
- 焦带边缘有虚线：线段6 px、间隔5 px，#8E8E93，不透明度75%。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：使城市或活动场景呈现玩具模型世界的观感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/106.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
