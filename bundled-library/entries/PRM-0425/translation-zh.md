请使用“Establishing shot”（エスタブリッシングショット），它是“Camera moves & transitions, part 2”中的一个名称。
Motion Prompt #183

定义：展示地点的宽景别开场镜头
示例展示：高处广角展示整座城镇；摄像机缓慢推进，左下角出现地点字幕。
规格：
- 摄像机：广角镜头，焦距220 px、显示为16mm，高度4.5 m，pitch为-0.06 rad；从-5 m缓慢推进至-2.5 m。
- 时间：0.3 s至4.2 s（3.9 s），使用三次缓入缓出，约为cubic-bezier(0.65,0,0.35,1)。
- 场景：八栋城市建筑在30 m远处，一座塔位于右侧16 m、距离36 m处，另有三片云与山体；左侧1 m、距离12 m的小人物提供尺度参照。
- 地点字幕：0.9–1.3 s，一张写有“EXT. CITY – DAY”的白卡在左下角淡入并上移8 px，卡片158×30 px、左侧蓝色竖条，之后保持显示。
- 返回：最后0.5 s交叉淡化回起点，单次过程为4.7 s；右上角读数显示“16mm WIDE”。
何时使用：用于场景开头交代所在地点，或在地点、时间变化时建立新环境。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/183.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
