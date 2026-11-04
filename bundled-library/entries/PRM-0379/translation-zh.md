请使用“Push transition”（プッシュ），它是“Motion graphics moves, part 2”中的一个名称。
Motion Prompt #137

定义：下一场景把当前场景推出
示例展示：下一个场景从侧面滑入，同时将当前场景推出画面。
规格：
- 海景→山景→海景，每段2.35 s。每半段的0.45–1.6 s执行切换，时长1.15 s，使用三次ease-in-out。
- 两个场景始终相连，一起移动完整画面宽度539 px；不重叠、不淡化。
- 方向：海景→山景时向左移动，下个场景从右侧进入；山景→海景时向右移动。
- 两个场景之间的接缝由宽6的深蓝色线标记。
何时使用：用于依次浏览幻灯片、照片或步骤，使变化显得连续并向前推进。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/137.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
