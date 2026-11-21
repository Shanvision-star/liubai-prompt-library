# Glasswork｜液态玻璃材质：浅色、深色与边缘折射

分类：Skill  
标签：UI 设计、CSS、液态玻璃、Glasswork、浏览器降级  
来源：[枯白 Glasswork 演示](https://www.kubai.design/glasswork/) · [源码仓库](https://github.com/kubai087/glasswork) · [v1.1.0 折射模块](https://github.com/kubai087/glasswork/blob/v1.1.0/lens.js)。CSS 是用户从作者工具导出的参数快照；JS 的版本不代表这份 CSS 来自同一版本。

## 给 Codex 的调用词

> 请调用「Glasswork｜液态玻璃材质」。先检查目标组件和现有主题，只给指定浮层、小入口或工具条应用样式。保持布局、鼠标与键盘操作不变；不用于正文、公式或数据表。先完成 CSS 静态玻璃，再在明确要求时给目标组件增加可选的边缘折射；不要把原始脚本的全局选择器照搬进生产。交付同一背景下只改变折射开关的对照，并列出测试环境和未测项。

## 用法与验收

1. 单独引用下方 `glass.css`，在示例容器上用 `class="glass"`，深色加 `is-dark`，胶囊加 `is-pill`。生产用组件作用域避免同名冲突。
2. 不加载 JS 也保留底色、高光和可支持的背景模糊。只有需要折射时才加载下方 `glass-init.js`；示例来自作者导出。独立 `lens.js` 的 SVG 折射面向 Chromium，作者站在 Safari/iOS/Firefox 的 WebGL 路径并不包含在此卡。需要离线时先评估供应链，将审核过的固定版本随项目管理并保留许可。
3. 用同一条纹背景，只切折射，核对斜纹边缘偏移、文字和按钮清晰、键盘焦点可见；背景过杂或混合模式导致小字变淡时，加实底色或撤掉该组件的混合模式。不支持的环境只保留静态可读样式，必要时降级为实底；减弱动效时不要加材质动画。不视作已通过真机验收。

## glass.css · 作者导出原样

```css
/* Lumno's liquid glass, from Glasswork (https://www.kubai.design/glasswork/).
   Light glass with dark ink by default; .glass.is-dark for dark glass with light ink.
   If Safari leaves a surface with busy content undrawn, move background and
   backdrop-filter to a ::before under the content, as glass.css in the repo does. */

.glass {
  border-radius: 28px;
  corner-shape: superellipse(1.25);
}
/* Capsules keep round ends. */
.glass.is-pill { border-radius: 999px; corner-shape: round; }

.glass {
  background: rgb(255 255 255 / 0.078);
  -webkit-backdrop-filter: blur(2px) saturate(180%) brightness(1.025);
  backdrop-filter: blur(2px) saturate(180%) brightness(1.025) var(--glass-lens,);
  box-shadow:
    inset 1.5px 1.5px 1px -1px rgb(255 255 255 / 1),
    inset -1.5px -1.5px 1px -1px rgb(255 255 255 / 0.6),
    inset 0 0 0 0.5px rgb(255 255 255 / 0.3),
    0 0 0 0.5px rgb(0 0 0 / 0.12),
    0 4px 16px rgb(0 0 0 / 0.1),
    inset 0 6px 8px -6px rgb(255 255 255 / 0.205),
    inset 4px 0 8px -6px rgb(255 255 255 / 0.09),
    inset -4px 0 8px -6px rgb(255 255 255 / 0.049),
    inset 0 -6px 8px -6px rgb(0 0 0 / 0.025);
  color: rgb(0 0 0 / 0.86);
}
.glass > * { mix-blend-mode: multiply; }
.glass .secondary { color: rgb(60 60 67 / 0.7); }

.glass.is-dark {
  background: rgb(30 30 34 / 0.339);
  -webkit-backdrop-filter: blur(2px) saturate(160%) brightness(0.8);
  backdrop-filter: blur(2px) saturate(160%) brightness(0.8) var(--glass-lens,);
  box-shadow:
    inset 1px 1px 0.5px -0.5px rgb(255 255 255 / 0.46),
    inset -1px -1px 0.5px -0.5px rgb(255 255 255 / 0.18),
    inset 0 0 0 0.5px rgb(255 255 255 / 0.06),
    0 0 0 0.5px rgb(0 0 0 / 0.28),
    0 4px 14px rgb(0 0 0 / 0.22),
    inset 0 6px 8px -6px rgb(255 255 255 / 0.18),
    inset 4px 0 8px -6px rgb(255 255 255 / 0.07),
    inset -4px 0 8px -6px rgb(255 255 255 / 0.04),
    inset 0 -6px 8px -6px rgb(0 0 0 / 0.08);
  color: rgb(255 255 255 / 0.94);
}
.glass.is-dark > * { mix-blend-mode: plus-lighter; }
.glass.is-dark .secondary { color: rgb(235 235 245 / 0.64); }
```

## glass-init.js · 可选，作者导出的脚本内容

```js
import { liquidGlass } from 'https://cdn.jsdelivr.net/gh/kubai087/glasswork@v1.1.0/lens.js';
for (const el of document.querySelectorAll('.glass')) liquidGlass(el, { rim: 40, edge: 1.1, power: 2.6, dispersion: 0.15 });
```

原始 HTML 形态是用 `<script type="module">…</script>` 包裹以上 JS；作为独立文件时不保留标签，从页面用 `<script type="module" src="./glass-init.js"></script>` 加载。原导出在模块前另有注释：`<!-- The rim lens (Chromium); everywhere else the CSS glass stays as it is. -->`。

## 第三方许可 · Glasswork（MIT）

```text
MIT License

Copyright (c) 2026 Kubai087

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
