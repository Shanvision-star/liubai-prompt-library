请使用“Floating animation”（ふわふわアニメーション），它是“Landing page & web effects”中的一个名称。
Motion Prompt #096

定义：元素轻柔地上下浮动。
示例展示：标题旁，手机、爱心徽章和评分小标签以不同节奏轻柔上下漂浮，手机下方阴影随之伸缩。
规格：
- 手机92 × 132：y = −8·sin(2πt/2.4)，每2.4 s浮动一次；正弦曲线在两端减速。
- 爱心徽章半径20：y = −6·sin(2πt/1.6 + 1.2)。评分标签76 × 30：y = −6·sin(2πt/2.4 + 2.4)。
- 手机下方54 × 6椭圆阴影的尺寸和不透明度乘以(1 + y/40)，手机升高时阴影变小、变淡。
- 2.4 s与1.6 s两个周期都整除4.8 s，因此循环没有接缝。
何时使用：为产品图、应用模型或装饰图标加入安静的动感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/096.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
