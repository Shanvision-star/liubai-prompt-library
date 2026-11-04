请使用“Page transition”（ページ遷移アニメーション），它是“Landing page & web effects”中的一个名称。
Motion Prompt #092

定义：衔接两个页面的动画。
示例展示：点击作品列表卡片后，橙色面板从左扫入；URL改变，面板向右退出，露出详情页。“返回列表”以相同方式返回。
规格：
- 0.8 s点击卡片；0.9–1.3 s橙色、铺满视口、中央有标志的面板从左进入并遮住全部内容，使用cubic ease-in-out。
- 1.3 s在全遮挡期间，页面与地址栏URL从/works切换为/works/02。
- 1.4–1.85 s面板向右退出，使用cubic ease-in-out。
- 3.0 s点击“← Back to list”；面板3.1–3.5 s进入，3.5 s切换页面，3.6–4.05 s退出。
- 面板覆盖整个视口，包括页头。
何时使用：品牌站或作品集串联相邻页面。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/092.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
