请使用“Steadicam”（ステディカム），它是“Camera moves & transitions, part 2”中的一个名称。
Motion Prompt #173

定义：平滑、漂浮般且没有抖动的运动
示例展示：摄像机向前平滑跟随行走人物，只有缓慢轻柔的摇摆，没有手持式抖动。
规格：
- 摄像机：以恒定1.7 m/s向前移动，每4.7 s移动8 m；高度1.45 m，俯仰角-0.02 rad，不使用缓动。
- 摇摆：高度±3.5 cm（每4.7 s内2个周期）、横向±5 cm（1周期）、yaw±0.012 rad、roll±0.006 rad，均为整数周期的正弦波，缓慢且宽舒（#034 Handheld则快速、不规则）。
- 主体：人物在摄像机前方5 m处以同速行走；双腿和双臂每4.7 s完成5次步伐。
- 树木：x = -5 m一侧高3.6 m，x = +5 m一侧高3.2 m，每8 m一棵，两排错开4 m；山和太阳随摄像机移动。
- 8 m同时是网格间距2 m和树间距8 m的倍数，因此每4.7 s无缝循环；右上角读数显示“STEADICAM”。
何时使用：让步行中的镜头呈现平稳、电影化的移动感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/173.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
