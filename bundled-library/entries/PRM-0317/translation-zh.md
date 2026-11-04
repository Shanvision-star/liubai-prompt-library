请使用“Sticky header”（追従ヘッダー），它是“Landing page & web effects”中的一个名称。
Motion Prompt #075

定义：页面滚动时，页头保持在顶部。
示例展示：公告条滚走后，下方页头停在顶部边缘，内容从其下面继续滚动。
规格：
- 滚动量在0.4–1.3 s从0→110 px，1.9–2.8 s从110→250 px，3.4–4.4 s从250→0，使用cubic ease-in-out。
- 页面最上方是22 px高的深蓝公告条，其下是34 px高的页头，内含标志、三个菜单项和按钮。
- 页头位置=max(22 − scroll, 0)：公告条离开后，页头停在顶部，对应position: sticky; top: 0。
- 随后24 px滚动区间内，页头下方12 px阴影的不透明度从0渐增到0.16。
- 照片、标题和三张卡片按正常速度从页头下方滚动。
何时使用：在长页面中始终保留可访问的菜单和行动按钮。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/075.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
