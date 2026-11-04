请使用“Pixelate”（ピクセレート），它是“Motion graphics moves, part 2”中的一个名称。
Motion Prompt #141

定义：变成粗像素块，然后切换
示例展示：画面逐渐变成更粗的像素块，在最粗时切换场景，再恢复清晰。
规格：
- 田野→城市→田野，每段2.35 s。在0.2–1.9 s的1.7 s内，块尺寸依次增大再减小，经过1、2、3、4、6、8、11、15、20、27、36 px；中点1.05 s最粗。
- 前半显示旧场景，后半显示新场景，在最粗的档位切换。
- 方法：先开启平滑，将帧缩小至原宽度 ÷ 块尺寸，再关闭平滑放大回原尺寸。
何时使用：用于游戏、复古或数字风格的场景转换，也可在切换时模糊内容。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/141.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
