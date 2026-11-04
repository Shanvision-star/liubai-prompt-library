请使用“Dutch angle”（ダッチアングル），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #036

定义：让画面沿对角方向倾斜。
示例展示：水平相机绕镜头轴滚转，停在地平线倾斜的构图上。
规格：
- 相机位置固定，高度 1.5 m；只改变滚转角，从 0 到 0.36 rad，约 21°，整幅图像绕画面中心转动。
- 0.6–2.2 s 变化，历时 1.6 s；采用三次 ease-in-out，约为 cubic-bezier(0.65,0,0.35,1)。
- 人物静止在前方 7 m；地平线、建筑和人物都倾斜相同角度。
- 2.2–4.2 s 保持倾斜，让观众有时间读取倾斜构图本身。
- 最后 0.5 s 交叉淡化回水平起始状态，一遍为 4.7 s。
- 右上角读数为 ∠ 0° → ∠ 21°。
何时使用：用于表达不安、紧张或某处不对劲的感觉。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/036.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
