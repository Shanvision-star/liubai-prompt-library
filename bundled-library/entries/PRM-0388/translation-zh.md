请使用“Scroll text reveal”（スクロールテキストリビール），它是“Landing page & web effects, part 2”中的一个名称。
Motion Prompt #146

定义：文字随滚动逐字变深。
示例展示：浅灰标题随页面滚动从左上角起逐字变深；向上滚动时则从末尾逐字变淡。
规格：
- 视口511×168。滚动进度p在0.3–2.6 s内0→1，3.2–4.4 s内1→0，均用三次ease-in-out；页面向上移动p × 40 px。单次4.7 s，在9.4 s包循环内播放两次。
- 三行标题共24个字符，字号27 px、字重800、行高38 px，开始均为浅灰#D6DBE4。
- 第n个字符从0计数，深色程度为clamp(p × 26 − n)；每个字符使用1/26的进度范围变成文字色#1C2333，并与滚动同步。
- 向上滚动时按同一公式从最后一个字符开始淡化；正文条和滚动条滑块随页面移动。
何时使用：用于理念或创始人寄语等需要慢慢阅读的短陈述。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/146.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
