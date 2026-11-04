请使用“Infinite scroll”（無限スクロール），它是“Landing page & web effects”中的一个名称。
Motion Prompt #091

定义：到达底部时自动加载更多项目。
示例展示：滚到列表尾部出现加载圈，随后新增三项，读者可继续阅读。
规格：
- 列表项331 × 44、圆角半径8、间隔52；最后一项下方有半径10的加载圈，每0.8 s转一圈。
- 滚动量在0.25–0.85 s从38→116 px，1.15–1.75 s从116→194 px，使用cubic ease-in-out，停下时列表末尾可见。
- 2.6 s添加三项；每项在0.35 s内从不透明度0→1，同时从下方10 px升起，使用cubic ease-out；加载圈移到新的末尾。
- 每个循环推进三项，即156 px；内容每三项重复，因此循环结尾与开头外观相同。
何时使用：供用户连续阅读、不必翻页的信息流或新闻列表。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/091.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
