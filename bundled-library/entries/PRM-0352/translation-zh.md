请使用“Fisheye lens”（魚眼レンズ），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #110

定义：使中央鼓起、直线弯曲的超广角镜头。
示例展示：街景中央向外鼓起，建筑竖线和道路线向外弯曲，四角位置保持不变。
规格：
- 场景2：街角，建筑、树和路灯（x=114、292、494）位于y=132–162的道路后方；人物站在左前方，脚部(x=176,y=200)，身高124 px。
- 变形：距中心d的点，距离乘以g = (1 + k) / (1 + k·d²/R²)；R为中心到角的距离，即289 px。
- k从0→1.25；中心放大2.25倍，角点不移动。
- 每条轮廓在变形前每6 px细分一次，让直线可弯成曲线。
- 右上焦距24mm→8mm。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：用于大胆、活泼或猫眼式视角，如滑板和音乐视频。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/110.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
