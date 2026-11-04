请使用“Parallax scrolling”（パララックススクロール），它是“Landing page & web effects”中的一个名称。
Motion Prompt #073

定义：滚动时，背景图层的移动速度慢于内容。
示例展示：页面向下滚动时，标题按正常速度上移，天空和太阳、远山、近山则移动得更慢。
规格：
- 浏览器窗口的视口为511 × 168。滚动量在0.3–1.9 s从0→120 px，在2.9–4.3 s从120→0，均为cubic ease-in-out。
- 每层位移等于滚动量乘以系数：天空和太阳0.15，远山0.4，近山0.7。
- 28 px标题、按钮和下一节以1.0系数移动，即正常滚动速度。
- 白色的下一节从首屏底部（168 px）开始，并滑过较慢的背景层。
- 右侧滚动条滑块跟随滚动量移动。
何时使用：为首屏或分区照片营造纵深感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/073.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
