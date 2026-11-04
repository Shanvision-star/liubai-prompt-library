请使用“Backlighting”（逆光），它是“Photo looks, lighting & styles”中的一个名称。
Motion Prompt #097

定义：光源位于主体后方。
示例展示：太阳从画外移动到人物头部正后方；人形边缘出现细亮边，浅暖色薄雾覆盖画面，朝相机的一面变暗。
规格：
- 场景1：地平线位于y=150，前方为头肩人形；头部中心(x=270,y=78)、半径29 px，不画五官和头发。亮部为平涂琥珀色#FFC75A，阴影为平涂#33405A。
- 太阳半径20 px，从画外左上方(x=40,y=−40)移动至头部正后方(x=270,y=56)；外有半径2.6倍和1.7倍的平涂圆环，#FFE3A3分别为35%与60%不透明度。
- 轮廓：先用7 px线描边人形，再填充，留下外侧3.5 px亮边。
- 人形颜色#4D5A75→#33405A；天空#FAF9F7→#FFF4DC；整幅画面叠加22%不透明度的#FFE3A3。
- 时序：效果在0.4–1.4 s逐渐进入，保持至4.0 s，到4.8 s再次消失；一次播放5 s，使用cubic ease-in-out，约为cubic-bezier(0.65,0,0.35,1)。
何时使用：用于通透、发光感的人像，或需要沐浴在光线中感觉的画面。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/097.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/photo.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
