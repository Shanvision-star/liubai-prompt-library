请使用“Marquee”（マーキー），它是“Landing page & web effects”中的一个名称。
Motion Prompt #094

定义：文字或标志在无尽横带中横向滚动。
示例展示：深蓝横带内，大号服务名称由橙点分隔，持续无缝地向左移动。
规格：
- 横带高58、深蓝色、铺满视口宽度；白色文字30 px、粗重字重、字距1 px。
- 每组四个词：WEB DESIGN / BRANDING / MOTION / UI/UX；词间相隔64 px，每个间隙有半径6的橙点。
- 每4.8 s循环以恒速向左移动一组的宽度，本例约881 px；测量整组宽度并据此取模偏移，避免可见接缝。
- 重复该组，直到覆盖整个视口宽度。
何时使用：有活力地展示服务名称、客户标志或宣传语。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/094.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
