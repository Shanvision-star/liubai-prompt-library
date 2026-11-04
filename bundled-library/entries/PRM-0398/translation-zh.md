请使用“Text roll on hover”（テキストロール），它是“Landing page & web effects, part 2”中的一个名称。
Motion Prompt #156

定义：悬停时字母向上滚动并替换。
示例展示：光标停在菜单词上时，字母依次向上滚出，同一单词的橙色副本从下方滚入；离开后向下滚回。
规格：
- 视口511×168，三个菜单词WORKS、ABOUT、CONTACT，字号30 px、字重800、字距1 px。光标从左到右各停约0.85 s。单次4.7 s，在9.4 s包循环内播放两次。
- 每个单词的橙色副本位于原词下方40 px，两者共同裁切在39 px高的盒子内，类似overflow: hidden。
- 悬停时每字错开0.035 s，在0.36 s内以三次ease-in-out向上移动40 px并离场，同时其橙色副本升到原位。
- 离开时，各字使用相同错峰和时长向下滚回。
何时使用：用于页头菜单或按钮，让短文字链接产生可触感反馈。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/156.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
