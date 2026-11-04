请使用“Page curl”（ページめくり），它是“Motion graphics moves, part 2”中的一个名称。
Motion Prompt #140

定义：像纸张一样掀开，显露下一页
示例展示：纸页从角部掀起并翻折，显露底下的下一页。
规格：
- 白色第1页→奶油色第2页→第1页，每段2.35 s。卷页从右下角开始，0.35–1.75 s完成，时长1.4 s，二次ease-in-out。
- 折线从角部沿归一化的(−1, −0.42)方向移动0→600 px。
- 折线外的部分关于折线镜像，形成翻起的纸背，颜色为浅灰或米色；带模糊14、偏移(4,4)的投影，以及2 px白色边缘。
- 纸张掀起区域露出下一页，折线沿线带有50 px宽的渐变阴影。
何时使用：用于书籍、目录、相册或章节切换，使纸张质感与阅读推进契合内容。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/140.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
