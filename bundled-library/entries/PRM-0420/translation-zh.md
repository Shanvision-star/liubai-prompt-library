请使用“High angle”（ハイアングル），它是“Camera moves & transitions, part 2”中的一个名称。
Motion Prompt #178

定义：从上方向下拍摄
示例展示：摄像机升高并向下看；人物显得较小，地面占据画面大部分。
规格：
- 摄像机：从1.5 m升至4.5 m，同时俯仰角从0 → -0.5 rad（向下约29°）；不前后移动。
- 时间：0.6 s至2.2 s（1.6 s），使用三次缓入缓出，约为cubic-bezier(0.65,0,0.35,1)。
- 主体：人物静止站在前方5 m处；随着摄像机俯看，人物缩小并在画面中下移，地面网格占据画面大部分，地平线从顶部离开。
- 保持：2.2–4.2 s维持高角度（#031 Crane up继续升至9 m；原文“13 Bird's-eye view”则以90°垂直向下看）。
- 返回：最后0.5 s交叉淡化回到平视，单次过程为4.7 s；右上角读数显示角度和高度（↘ 0° · 1.5m → ↘ 29° · 4.5m）。
何时使用：让人物显得脆弱、渺小，或从上方解释场景状况。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/178.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
