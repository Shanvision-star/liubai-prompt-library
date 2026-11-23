# Glasswork 每日学习 06｜把跨端折射当作增强，不当作基础

2026-11-23（北京时间）。06 是留白的学习编号，不是作者文章编号。本篇是对枯白 Kubai（@Kubai087）公开仓库的原创学习笔记，不代表业务页面已改动或通过真机验证。

## 观察：同样的料感，背后是两条渲染路径

先用半透明底色、模糊和薄边缘高光做基础玻璃。Chromium 支持 SVG 背景滤镜时，可用 `lens.js` 让边缘产生位移；Glasswork 演示为 Safari／iOS／Firefox 另用 `refract.js` 画 WebGL2 层。这需要受控的背景图、视频或场景画布，并非任意 DOM 都能折射。WebGL2 不可用或背景无法读取时，保留基础磨砂。只复制 CSS 与 `lens.js` 不是复制了演示的兼容实现。

## 练习：只改一个搜索胶囊

用虚构数据和自己绘制的灰线背景做一张检索面板，结果、数字和证据保持不透明。A 只用磨砂，B 在可用时增加边缘折射。用 Edge 检查细线是否只在边缘产生偏移；在真实 iPhone Safari 上对照，并关闭增强再试一次。切换前后，搜索、筛选和证据入口必须同样可辨，键盘焦点与点击范围不变，降级时不得空白或牺牲文字对比。先验收可用性，不要求两端像素相同。

## 来源和许可

- [固定版浏览器分支](https://github.com/kubai087/glasswork/blob/4f0b6744b898b3a9b98fbd913ab24fdb83c53162/playground.js#L773-L841) · [基础玻璃样式](https://github.com/kubai087/glasswork/blob/4f0b6744b898b3a9b98fbd913ab24fdb83c53162/glass.css#L110-L128)
- [MIT 许可](https://github.com/kubai087/glasswork/blob/4f0b6744b898b3a9b98fbd913ab24fdb83c53162/LICENSE) · [素材例外](https://github.com/kubai087/glasswork/blob/4f0b6744b898b3a9b98fbd913ab24fdb83c53162/NOTICE)。复用源码时保留许可；不复制不在授权内的 Apple 壁纸。
