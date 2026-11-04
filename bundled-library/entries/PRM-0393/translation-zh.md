请使用“Back-to-top button”（トップへ戻るボタン），它是“Landing page & web effects, part 2”中的一个名称。
Motion Prompt #151

定义：向下浏览后出现，可返回顶部。
示例展示：向下滚动后，右下角出现圆形箭头按钮；点击即可把页面带回顶部。
规格：
- 视口511×168。滚动在0.2–1.7 s内从0→300 px到页面底部，使用三次ease-in-out。单次4.7 s，在9.4 s包循环内播放两次。
- 按钮为右下角橙色圆，圆心x = 472、y = 138，半径19，白色向上箭头，阴影模糊10 px；滚动80–140 px期间，以三次ease-out淡入并向上移动10 px。
- 2.6 s点击按钮；光标悬停时，在0.2 s内从#FF5A2C变暗至#D9431C。
- 点击后滚动量在2.66–3.26 s从300→0，持续0.6 s，三次ease-in-out；滚动低于80 px时按钮按同一公式淡出。
何时使用：用于博客、长落地页或商品列表等长页面，让读者返回顶部菜单。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/151.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
