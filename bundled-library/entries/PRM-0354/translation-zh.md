请使用“Vignette”（周辺減光（ビネット）），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #112

定义：四角变暗，引导视线看向中心。
示例展示：画框从四角平滑变暗，中央人物和道路保持明亮。
规格：
- 场景2：街角，建筑、树和路灯（x=114、292、494）位于y=132–162的道路后方；人物站在左前方，脚部(x=176,y=200)，身高124 px。
- 形状：以画面中心为中心的椭圆，竖直半径=水平半径 × 208/539 × 1.35。
- 水平半径334 px的45%以内保持透明，之后rgb(32,35,43)朝边缘从0%增加到70%不透明度。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：将注意力聚焦主体，或暗示老镜头质感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/112.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
