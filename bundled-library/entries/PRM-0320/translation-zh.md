请使用“Scroll snap”（スクロールスナップ），它是“Landing page & web effects”中的一个名称。
Motion Prompt #078

定义：滚动最终精确停在下一分区。
示例展示：用户小幅滚动后，页面自行完成剩余移动，使下一分区顶部与视口顶部对齐。
规格：
- 每节与视口等高，均为168 px；第一节浅蓝，第二节深蓝。
- 每2.4 s吸附一次；0.45–0.85 s用户只滚动34 px，使用cubic ease-out。
- 0.9–1.5 s页面自行移动余下134 px，使下一节顶部对齐，使用cubic ease-out。
- 第二个2.4 s以同样方式向上返回第一节，表现scroll-snap-type: y mandatory的行为。
何时使用：用于希望像幻灯片一样逐个整屏阅读的页面。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/078.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
