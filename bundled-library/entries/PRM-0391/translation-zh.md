请使用“Hide-on-scroll header”（隠れるヘッダー），它是“Landing page & web effects, part 2”中的一个名称。
Motion Prompt #149

定义：向下滚动时隐藏，向上滚动时返回。
示例展示：向下滚动时，页头向上移出视野以释放空间；即使只向上滚一点，页头也立即返回。
规格：
- 视口511×168，顶部固定34 px高页头。滚动0.3–1.1 s从0→170 px向下，1.5–1.9 s从170→100向上，2.4–2.9 s从100→230向下，3.3–4.3 s从230→0向上，均用三次ease-in-out。单次4.7 s，在9.4 s包循环内播放两次。
- 最近一次移动向下则隐藏页头，向上则显示；距页面顶部34 px以内始终显示。
- 隐藏和显示都在0.3 s内以二次ease-in-out切换向上36 px的位移状态，类似带transition的transform: translateY。
- 发生滚动时页头下方有12 px阴影，其不透明度在最初30 px滚动内从0→0.14；滚动条滑块跟随滚动。
何时使用：用于手机等屏幕空间紧张的页面，为内容腾出空间，同时让菜单只需轻微回滚就可到达。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/149.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
