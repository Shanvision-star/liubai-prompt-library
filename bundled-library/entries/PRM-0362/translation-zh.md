请使用“Double exposure”（二重露光（多重露光）），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #120

定义：两张照片叠合在同一画框中。
示例展示：背景变白，山丘、房屋、树和太阳的风景缩小后，只出现在半身像轮廓内部。
规格：
- 场景3：左侧是半身像，头部中心(x=140,y=82)、半径28 px；右侧是山丘、房屋、树和太阳，太阳(x=432,y=54)、半径15 px。
- 半身像之外的背景为白色#FFFFFF。
- 半身像内部：同一风景缩放为0.7倍，定位使太阳落在头部右上方，山脊横过颈部。
- 内部颜色：天空#D3DBE6，山丘#9AA8BD和#76869F，地面#55647E，树#3F4C66。
- 过渡：按照效果量，将双重曝光图叠加在原图上。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：在海报与封面中，将人物与某个地方、记忆或内心世界联系起来。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/120.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
