请使用“Exit-intent popup”（離脱防止ポップアップ），它是“Landing page & web effects”中的一个名称。
Motion Prompt #088

定义：访客即将离开时出现的弹窗。
示例展示：光标从页面顶部朝标签和关闭按钮方向移出时，页面变暗并出现“等等！”弹窗；点击×关闭。
规格：
- 光标在0.7–1.25 s从页面向浏览器地址栏上升，使用cubic ease-in-out。
- 光标越过视口顶部y=0时触发，约在1.07 s，等同于document的mouseleave且clientY ≤ 0的判断。
- 触发后0.05–0.45 s展开，使用cubic ease-out：深蓝背景遮罩不透明度0→0.5；260 × 132、圆角半径12的弹窗不透明度0→1，缩放0.9→1。
- 内部包含标题、橙色折扣行、优惠券按钮及右上角×。
- 2.9 s点击×，此后0.03–0.25 s线性消失。
何时使用：给即将离开、尚未转化的访客最后一次优惠提议。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/088.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
