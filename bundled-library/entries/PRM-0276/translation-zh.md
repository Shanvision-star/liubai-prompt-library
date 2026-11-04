请使用“Handheld”（手持ち），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #034

定义：轻微晃动，如同相机由人手持。
示例展示：给整幅画面加入小幅、不规则震动，仿佛相机由人手持而非架在三脚架上。
规格：
- 相机位置几乎固定；偏航、俯仰、滚转和高度各自叠加不同周期的正弦波，T = 2π×u/4.7。
- 偏航角（rad）= 0.016·sin(3T) + 0.008·sin(7T+1) + 0.004·sin(13T+2)，最多约 ±1.6°。
- 俯仰角（rad）= 0.012·sin(4T+2) + 0.006·sin(9T+0.5) + 0.003·sin(17T+1.2)，最多约 ±1.2°。
- 滚转角（rad）= 0.02·sin(5T+1) + 0.008·sin(11T+3)，最多约 ±1.6°；高度 = 1.5 + 0.03·sin(6T) m。
- 人物静止在前方 6.5 m；震动连续运行，没有缓动或停留段。
- 各频率倍数均为整数，因此每 4.7 s 可无缝循环；右上角显示 HANDHELD。
何时使用：用于营造纪录片感或身临现场的感觉。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/034.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
