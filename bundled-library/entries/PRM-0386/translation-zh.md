请使用“Split screen”（スプリットスクリーン），它是“Motion graphics moves, part 2”中的一个名称。
Motion Prompt #144

定义：划分画面，并排显示场景
示例展示：一个全屏场景先拆成两栏，再拆成三栏，各栏内的场景独立持续运动。
规格：
- 全屏海景在0.45–0.95 s分为两栏，分隔线位置539→269.5；1.4–1.9 s再分成三栏，分隔线位于1/3和2/3；3.75–4.4 s合回一栏，全部采用三次ease-in-out。
- 海景、城市、田野三个场景分别在自己的栏内居中并裁切，内部持续运动：海浪与帆船、城市窗户每4.7 s切换8次、风车每4.7 s转两圈。
- 栏间有6 px宽白色分隔线。
何时使用：用于对比、展示同时发生的事，或并列呈现人物、地点、前后状态和多个选项。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/144.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
