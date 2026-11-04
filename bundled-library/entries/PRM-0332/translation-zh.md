请使用“Lazy loading”（遅延読み込み），它是“Landing page & web effects”中的一个名称。
Motion Prompt #090

定义：图片只有进入视野时才加载。
示例展示：灰色占位框滚入视野时，框内出现旋转加载标识，图片到达后淡入；第一排从一开始就已加载。
规格：
- 3 × 3网格的占位框各151 × 92，第一排初始可见。滚动量在0.35–1.1 s从0→110 px，1.7–2.5 s从110→225 px，3.5–4.5 s从225→0，使用cubic ease-in-out。
- 占位框顶边越过视口底部168 px后开始加载，每一列比左邻列延后0.12 s。
- 占位框中心的半径11加载圈旋转0.45 s，每0.8 s转一圈。
- 随后图像在0.35 s内以cubic ease-out从不透明度0→1；尚未加载的占位框显示图像图标。
- 离开视口底部的占位框在视野外重置。
何时使用：在图片较多的页面加快首屏加载。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/090.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
