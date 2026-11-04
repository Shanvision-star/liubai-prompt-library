请使用“Toast notification”（トースト），它是“UI component names”中的一个名称。
Motion Prompt #056

定义：短消息出现在角落，并自行消失
示例展示：点击“保存”后，深色通知滑入右下角；剩余时间条耗尽时滑出。
规格：
- 卡片为542×191，循环4.5 s。光标1.0 s点击左下角110×36蓝色“保存”按钮，随后向左下离开。
- 通知颜色#26282c，大小214×52、圆角半径10，距右边18 px、距底边16 px；在1.05–1.4 s内按easeOutCubic从右侧相距240 px处滑入。
- 内部包含蓝色圆中的白色勾，以及白色15 px“已保存”文字。
- 底部高3 px的剩余时间线在1.4–3.2 s内线性从194 px缩至0。
- 退出：3.2–3.55 s内按easeInOutCubic向右滑出240 px。
何时使用：不中断用户操作地确认保存、发送等结果。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/056.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/ui.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
