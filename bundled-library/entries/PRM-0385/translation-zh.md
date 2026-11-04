请使用“Exploded view”（分解図），它是“Motion graphics moves, part 2”中的一个名称。
Motion Prompt #143

定义：部件分离，展示内部结构
示例展示：手机分离成多个层，展示内部构造，然后重新组装。
规格：
- 等距视角手机由后盖、电池、电路板、屏幕四层组成。每层是扁平圆角板，沿缩放0.85并向两侧各倾斜30°的坐标轴绘制，侧面厚6 px。
- 拆开：从0.45 s起，每层持续0.75 s，后一层比下方一层晚0.08 s，使用backOut（s = 1.3）。第i层高度（从底部起i = 0–3）= 7i + 30i × 进度，因此后盖保持不动。
- 分开期间，每层每4.7 s上下浮动±3 px两次；角点由虚线引导线相连，右侧出现带引线的名称标签，演示中为日文。
- 组装：从3.25 s起，每层持续0.7 s，从顶层开始，彼此间隔0.07 s，三次ease-in-out。
何时使用：直观解释产品内部有什么、如何工作或由什么组成。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/143.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
