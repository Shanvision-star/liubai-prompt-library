请使用“Fade to black”（フェードアウト），它是“Camera moves & transitions, part 2”中的一个名称。
Motion Prompt #187

定义：画面逐渐暗至黑色
示例展示：整幅画面逐渐沉入黑色，下一场景再从黑色中变亮出现。
规格：
- 淡出：1.4–2.6 s，共1.2 s，在出场画面上覆盖黑色rgb(20,20,24)，不透明度0 → 100%，使用二次缓入缓出，约为cubic-bezier(0.45,0,0.55,1)。
- 黑场：2.6–3.1 s完全被黑色覆盖；2.9 s在不可见状态下以硬切换入下一画面。
- 淡入：3.1–4.3 s，共1.2 s，黑色不透明度按相同缓动从100% → 0。
- 摄像机：两幅画面都固定；A高度1.4 m，B高度1.6 m、pitch为+0.1 rad；主体也不动。
- 每4.7 s在A→B与B→A之间交替，完整往返9.4 s；右上角显示“FADE OUT” / “FADE IN”；取景框标记保持在黑色之上。
何时使用：用于章节分隔、较长时间流逝，或故事结束。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/187.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/camera2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
