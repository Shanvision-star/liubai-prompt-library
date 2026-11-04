请使用“Toggle switch”（トグルスイッチ），它是“UI component names”中的一个名称。
Motion Prompt #059

定义：将某项设置打开或关闭
示例展示：三行设置中，前两行开关依次打开，随后再依次关闭。
规格：
- 卡片为542×191，循环4.5 s。三行设置间隔60 px，带分隔线。x=450处为64×34轨道，圆角半径17；白色旋钮半径13，带阴影。
- 点击时刻：1.0 s打开第1行，1.8 s打开第2行，3.0 s关闭第1行，3.6 s关闭第2行；第3行始终关闭。
- 每次切换持续0.2 s，使用easeOutCubic；旋钮滑动30 px（17→47）。
- 轨道颜色随开关进度从灰色#d9d7d5混合到蓝色#1f5ae8。
何时使用：用于立即生效且只有开/关两种状态的设置。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/059.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/ui.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
