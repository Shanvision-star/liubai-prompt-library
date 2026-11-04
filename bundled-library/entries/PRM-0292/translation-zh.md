请使用“Drawer (Off-canvas)”（ドロワー），它是“UI component names”中的一个名称。
Motion Prompt #050

定义：菜单面板从屏幕侧边滑入
示例展示：点击“菜单”后，高面板从左侧滑入；点击外部后滑回。
规格：
- 卡片为542×191，循环4.5 s。光标在1.0 s点击左上角110×34的“菜单”按钮。
- 展开量a在1.0–1.38 s内按easeOutCubic从0→1。整卡rgba(18,20,28)遮罩的不透明度为0.36·a。
- 白色面板宽210、高度等于卡片高度；x = −210 + 210·a，因此从左边缘滑入。阴影模糊22，alpha为0.25。
- 顶部为半径14的头像和姓名，下面四行菜单间隔32 px；第一行以浅蓝色横条表示选中。
- 关闭：光标在3.3 s点击面板外(420,120)，a乘以(1 − 在3.3–3.65 s运行的easeInOutCubic)，面板滑回。
何时使用：将导航或筛选器隐藏在屏幕外，按需展开，尤其适合移动端。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/050.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/ui.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
