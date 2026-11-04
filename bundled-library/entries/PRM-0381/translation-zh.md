请使用“Cube transition”（キューブ），它是“Motion graphics moves, part 2”中的一个名称。
Motion Prompt #139

定义：像立方体转动一样切换场景
示例展示：像立方体转动一样，正面转离视线，下一个面转到前方。
规格：
- A面是珊瑚底上的“A”，B面是薄荷底上的“B”，各250×146；每段2.35 s，依次A→B→A。
- 0.45–1.6 s内旋转0→90°，时长1.15 s，三次ease-in-out；绕穿过立方体中心的竖直轴旋转，深度等于面宽250。
- 透视相机距离820 px。每个面按2 px宽的竖直切片绘制，每片依据其透视系数调整尺寸和位置。
- 转走的面最多变暗55%，即0.55·sinφ；进入的面从55%暗度逐渐变亮，即0.55·cosφ。地面阴影跟随可见宽度变化。
何时使用：依次展示产品、套餐或屏幕，同时加入纵深感。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/139.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/motion2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
