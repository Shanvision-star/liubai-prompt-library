请使用“Morph cut”（モーフカット），它是“Camera moves & transitions, part 2”中的一个名称。
Motion Prompt #186

定义：融合两次拍摄，使衔接消失
示例展示：同一人物的两次拍摄通过平滑插值位置和姿势连接，不像跳切那样突然位移。
规格：
- Take 1为0–2.0 s：固定摄像机，高度1.45 m；人物位于左侧0.4 m、距离3.3 m处，双臂和双腿角度-0.45 rad。Take 2从2.45 s开始：人物位于右侧0.35 m、肢体角度+0.55 rad。两段均叠加0.12·sin(t×3) rad的轻微摆动。
- 变形段为2.0–2.45 s，共0.45 s：位置以二次缓入缓出插值，约为cubic-bezier(0.45,0,0.55,1)；两种姿势在同一个插值位置绘制并交叉淡化。
- 只在变形期间，对整幅画面施加sin(q×π)×2.2 px的模糊以柔化衔接（#041 Jump cut允许位置直接跳变）。
- 底部条分为take 1（灰）、morph（蓝色窄段）、take 2（灰），并有播放头。
- 返回：最后0.5 s交叉淡化回take 1起点；右上角读数为“TAKE 1” → “MORPH” → “TAKE 2”。
何时使用：压紧采访或解说节奏，或不引人注意地删除口误。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/186.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
