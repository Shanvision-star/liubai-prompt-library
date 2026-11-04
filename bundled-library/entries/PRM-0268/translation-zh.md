请使用“Tilt”（ティルト），它是“Camera moves & transitions”中的一个名称。
Motion Prompt #026

定义：让相机向上或向下转动。
示例展示：相机留在原地向上仰转，从地面的一个人转向塔顶。
规格：
- 相机位置固定，高度 1.4 m；只改变俯仰角，从 −0.06 rad 到 +0.36 rad，即 −3° 到 +21°，总计约 24°。
- 时间为 0.5–3.4 s，历时 2.9 s；采用三次 ease-in-out，约为 cubic-bezier(0.65,0,0.35,1)。
- 主体人物静止在前方 7 m；后方距相机 26 m 有一座高 9.5 m 的塔，天线顶端高 11.8 m。
- 画面中的一切向下滑动：人物从底部离开，塔顶及天线进入画面。
- 复位：3.4–4.2 s 停留，最后 0.5 s 交叉淡化回起点；一遍为 4.7 s。
- 右上角读数以整数角度显示 −3° → +21°。
何时使用：用于展示建筑或人物的高度和尺度。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/026.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
