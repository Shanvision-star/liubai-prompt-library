请使用“Preloader”（ローディング画面），它是“Landing page & web effects”中的一个名称。
Motion Prompt #089

定义：页面加载期间显示的屏幕。
示例展示：深蓝屏幕中，标志下方数字从0%计到100%；随后整屏向上揭开，下面的页面淡入。
规格：
- 深蓝屏幕铺满视口，包含标志、28 px数字和180 × 4进度条。
- 0.25–2.1 s从0→100%，使用cubic ease-out并四舍五入为整数；橙色进度条同步填充。
- 2.3–2.85 s整屏向上移动168 px并离场，使用cubic ease-in-out。
- 2.35–2.95 s页面标题与照片从不透明度0→1，同时从下方14 px处升起，使用cubic ease-out。
- 4.25–4.75 s屏幕从顶部落回，恢复0%，表示下一次加载。
何时使用：图像或视频较重的网站，将加载等待转化为品牌呈现。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/089.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
