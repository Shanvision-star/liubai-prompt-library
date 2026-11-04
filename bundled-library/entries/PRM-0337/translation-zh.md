请使用“Animated gradient”（グラデーションアニメーション），它是“Landing page & web effects”中的一个名称。
Motion Prompt #095

定义：背景颜色持续漂移、混合。
示例展示：标题背后，橙、浅橙、蓝、浅蓝的柔和色块沿环形轨迹漂移，不断形成不同混色。
规格：
- 底色#FFF1EB，上叠四个径向渐变，中心为颜色、边缘透明，每层不透明度0.85。
- 橙色半径230；浅橙#FFB08F半径210；蓝色半径240；浅蓝#9DB6FB半径200。
- 每个中心沿椭圆每4.8 s一圈；x半径分别70、60、80、50，y半径分别30、40、30、35，起始角分别0、2.1、4.2、1.0 rad。
- 34 px白色标题和按钮置于其上，仅渐变移动。
何时使用：不使用照片，也为首屏或标题背景增加运动与色彩。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/095.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
