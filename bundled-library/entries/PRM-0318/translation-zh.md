请使用“Pinning”（ピン留め），它是“Landing page & web effects”中的一个名称。
Motion Prompt #076

定义：分区保持固定，滚动推进其内部内容。
示例展示：深蓝分区铺满视口后停住，继续滚动将数字和照片依次切换为1→2→3，然后该分区继续滚走。
规格：
- 滚动量在0.3–3.0 s从0→500 px，3.5–4.5 s从500→0，使用cubic ease-in-out。
- 深蓝分区高168，在滚动110 px时到达顶部，并在接下来的300 px滚动距离内保持固定，相当于GSAP ScrollTrigger pin。
- 固定期间进度p = (scroll − 110) / 300；左侧长124的竖线按p填充为橙色。
- 在p = 1/3和2/3附近（±0.07，cubic ease-in-out）转至下一步：46 px数字向上滚52 px，226 × 124照片向上滑124 px。
- 300 px固定区间结束后解除固定，分区和下方白色分区一起向上滚动。
何时使用：在同一屏内依次讲解步骤、功能或前后对比。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/076.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
