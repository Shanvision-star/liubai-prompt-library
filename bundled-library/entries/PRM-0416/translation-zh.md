请使用“Follow shot”（フォローショット），它是“Camera moves & transitions, part 2”中的一个名称。
Motion Prompt #174

定义：在移动主体身后跟随
示例展示：摄像机沿着蜿蜒行人的同一路径，在其身后数米处跟随；人物背面保持在画面中央附近。
规格：
- 路径：人物沿x = 1.8·sin(2.2s)、深度z = 4 + 9s的曲线行走，其中参数s从0到1，深度从4 m到13 m。
- 摄像机：沿同一曲线在s-0.4处跟随，约落后3.6–3.9 m，始终朝向人物；yaw = atan2(person x - camera x, person z - camera z)，高度1.5 m。
- 时间：0.3 s至4.2 s（3.9 s），使用三次缓入缓出，约为cubic-bezier(0.65,0,0.35,1)；双腿和双臂按sin(s×30)×0.42 rad摆动。
- 人物背面位于画面中央附近；路旁立柱和岩石在前景掠过（#029 Tracking shot是在人物旁侧同行）。
- 返回：最后0.5 s交叉淡化回起点，单次过程为4.7 s；右上角读数显示到人物的距离（FOLLOW 3.6–3.9m）。
何时使用：让观众与角色一起进入场所，或形成第三人称游戏式视角。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/174.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
