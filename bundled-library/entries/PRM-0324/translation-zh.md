请使用“Image zoom on hover”（ホバーで画像ズーム），它是“Landing page & web effects”中的一个名称。
Motion Prompt #082

定义：照片在固定外框内放大。
示例展示：光标下的照片缓慢放大，外框保持原尺寸；光标离开后照片缩回。
规格：
- 两个照片框均222 × 118，圆角半径8；光标先停左框、再停右框，每处约1.5 s。
- 悬停时内容以中心为原点，在0.5 s内从1放大至1.15，使用cubic ease-out；移开后也用0.5 s恢复。
- 超出框的内容被裁切，对应overflow:hidden；边框和说明文字不移动。
何时使用：照片网格、作品、产品或文章列表中，指出即将被选择的项目。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/082.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
