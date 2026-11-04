请使用“Horizontal scroll”（横スクロール），它是“Landing page & web effects”中的一个名称。
Motion Prompt #077

定义：向下滚动使内容横向移动。
示例展示：页面向下滚动时，分区保持原位，四张编号作品卡向左移动。
规格：
- 滚动量在0.3–3.0 s从0→420 px，3.5–4.5 s从420→0，使用cubic ease-in-out。
- 标题“WORKS”滚走；分区在滚动40 px时抵达顶部并固定。
- 四张卡片各200 × 112，间距20，两侧内边距34。横向行程=34·2 + 200·4 + 20·3 − 511 = 417 px。
- 卡片x = 起始x − p × 417，p = (scroll − 40) / 380；位移与滚动量线性对应，不添加缓动。
- 卡片横移时，滚动条滑块仍然向下移动。
何时使用：在纵向长页面里横向展示作品、案例或产品。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/077.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
