请使用“View transition (shared element)”（ビュートランジション），它是“Landing page & web effects, part 2”中的一个名称。
Motion Prompt #161

定义：列表照片扩展为详情页图像。
示例展示：点击列表照片后，同一张照片连续放大为详情页顶部图像，其余内容切换为详情页；返回时照片缩回原位置。
规格：
- 视口511×168，列表中三张照片各143×80、圆角半径6。0.75 s点击中间照片，3.05 s点击详情页“← 一覧へ”（返回列表）。单次4.7 s，在9.4 s包循环内播放两次。
- 前进：0.85–1.45 s内，0.6 s三次ease-in-out，使被点击的照片从列表槽位连续移动并变形为详情页顶部479×94图像，圆角半径8；全程保持为同一张照片。
- 其他照片和标题在运动前62%内淡出，详情标题、正文和返回按钮在最后40%内淡入；进度50%时URL从/works变为/works/02。
- 返回：3.15–3.75 s，0.6 s内反向运行相同运动，照片回到列表槽位。
- 这是列表照片与详情照片共享相同view-transition-name时，View Transitions API呈现的视觉效果。
何时使用：用于列表与详情来回切换的画廊或商品页面，让用户始终认得自己打开的是哪一项。

参考实现（Canvas 2D，画面仅由时间决定的函数）：https://showheyohtaki.github.io/motion-prompt/api/v1/en/e/161.txt
共享辅助代码：https://showheyohtaki.github.io/motion-prompt/api/v1/kit/lp2.js
请保持参考实现的形状、时间安排和缓动数值不变，只调整文字、颜色和素材，以适配我正在制作的项目。
