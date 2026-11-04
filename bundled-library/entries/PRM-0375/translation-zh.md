请使用“Text mask”（テキストマスク），它是“Motion graphics moves, part 2”中的一个名称。
Motion Prompt #133

定义：将字母镂空，在内部显示图像
示例展示：粗重字母被做成镂空遮罩，运动的海景只显露在字内；周期接近结束时整幅海景显现。
规格：
- “OCEAN”字重900，system-ui字体，字距2 px。字号从172 px开始，每次减少2 px，直到单词宽度不超过500 px。
- 字内场景持续运动：珊瑚色天空、上下摆动±6 px的黄色太阳、y = 116以下的蓝色海面；四条白色波浪线每4.7 s分别沿交替方向漂移240 px；帆船每4.7 s横穿一次，云漂移60 px。
- 方法：先在离屏Canvas绘制文字，再用source-in把场景合成进去，使场景只保留在字母内；字母外围有4 px白色描边。
- 字母外的场景以12%不透明度显示；3.45–3.85 s升至100%，4.25–4.65 s回到12%，均用smoothstep。
何时使用：将照片或视频放进标题、品牌名内部，把文字与画面结合。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/133.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
