<div align="center">

# svg2pptx-skill

[English](./README.md) · **简体中文**

### 一条命令，把扁平的 AI 草图变成**可逐个编辑的矢量 PowerPoint**。

*每一个形状、文字、箭头、渐变都成为真正的 PowerPoint 对象——可点选、可改色、可重打字——然后随手导出 PDF、Keynote 或 Google Slides。*

![前后对照：扁平 SVG 变为原生可编辑的 PowerPoint 形状](docs/before-after.png)

</div>

---

## 为什么需要它

AI 很擅长"画"图，却几乎给不了你能"改"的东西。你让 GPT 或 Claude 画一张机制图、架构图、流程图——拿到的是一张 **PNG 或 SVG**。把它丢进 PowerPoint，就是一块死掉的像素:挪不动一个框、改不了一个错字、换不了箭头颜色、套不上品牌配色。于是你只能手动重画一遍。

**svg2pptx-skill 补上了这关键的最后一步。** 它把你的 SVG 用 **原生 DrawingML**(PowerPoint 内部使用的同一套形状语言)重新搭建出来,于是打开的 deck 是一堆**可以单独编辑**的对象,而不是一张截图。

```
   GPT / Claude / 手绘                 本 skill                 你，在 PowerPoint 里
   ┌──────────────────────┐      ┌───────────────┐      ┌──────────────────────────┐
   │   草图  PNG  ·  SVG    │ ───▶ │  SVG → 原生   │ ───▶ │  逐个编辑每个形状与文字   │ ──▶ PDF · Keynote · Slides
   └──────────────────────┘      │     PPTX       │      └──────────────────────────┘
                                  └───────────────┘
```

> **它打通的工作流:** *向 AI 要图 → 在这里转换 → 在 PowerPoint 里精修 → 导出 PDF。* 第一稿享受 AI 的速度,收尾保留完全的人工掌控——而且你拿到的是一份真正属于自己、可持续编辑的源文件。

---

## "原生"意味着什么(以及为什么重要)

| | 图片塞进幻灯片(常见的 AI 导出) | **svg2pptx-skill** |
|---|---|---|
| 移动 / 缩放某个框 | ❌ 已经烤进图片里 | ✅ 是真正的形状 |
| 给箭头改色 | ❌ | ✅ |
| 改一个错字 | ❌ 只能整张重新生成 | ✅ 点一下就改 |
| 套用品牌色 / 字体 | ❌ | ✅ |
| 导出任意尺寸的清晰 PDF | 模糊(位图) | ✅ 矢量级锐利 |

形状 → `custGeom`/`prstGeom`,文字 → 可编辑文本框,渐变 → `gradFill`,箭头 → 原生箭头端,虚线 / 旋转 / 图案 → 各自对应的 DrawingML 表达。

---

## 快速开始

```bash
git clone https://github.com/JamieJustTang/svg2pptx-skill.git
cd svg2pptx-skill
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 一条命令——产物就在你文件旁边
python3 convert.py 路径/diagram.svg
```

```bash
python3 convert.py diagram.svg -o out.pptx     # 指定输出路径
python3 convert.py slides/ -o deck.pptx         # 一个装满 .svg 的文件夹 → 一份多页 deck
python3 convert.py diagram.svg --check-only      # 只跑兼容性质检
python3 convert.py diagram.svg --svg-snapshot    # 额外产出一份像素级还原的 *_svg.pptx
```

用自带示例试一下:

```bash
python3 convert.py examples/support_structure_demo.svg
python3 convert.py examples/filtration_demo.svg
```

[`examples/`](examples/) 里放了源 SVG 与转换后的 `.pptx` 成对对照。

---

## 作为 Claude Code 插件一键安装

本仓库同时也是一个 Claude Code **插件市场(plugin marketplace)**。在 Claude Code 里:

```text
/plugin marketplace add JamieJustTang/svg2pptx-skill
/plugin install svg2pptx@svg2pptx
```

skill 会立即可用。安装后在缓存的插件目录里跑一次依赖安装(`pip install -r requirements.txt`),Python 引擎即可运行。

---

## 作为 AI Agent 的 skill 使用

本仓库以 **skill** 形式组织:[`SKILL.md`](SKILL.md) 是 agent 入口。把任意 agent(Claude Code、Cursor、Codex…)指向这个目录,它就能驱动整条流程——写出兼容的 SVG、跑质检、按质检提示修复、再导出——你完全不用碰命令行。配套的契约文档 [`references/shared-standards.md`](references/shared-standards.md) 会告诉模型:哪些 SVG 特性能安全地转进 PowerPoint。

一个自然的 agent 循环:
> *"按 `references/shared-standards.md` 把某张图画成 SVG,然后运行 `convert.py`,根据质检报错反复修到干净导出为止。"*

---

## 工作原理

```
你的 SVG ─▶ svg_quality_checker ─▶ finalize_svg ─▶ svg_to_pptx ─▶ 原生 .pptx
            (兼容性质检门禁)        (嵌入图标、       (逐元素
             继续前必须 0 错误        裁剪/嵌入图片、    DrawingML 转换)
                                     拍平文本、圆角矩形)
```

- **质量门禁** —— 在导出*之前*抓出 PowerPoint 无法表达的 SVG 特性,给出精确报错,而不是导出一张悄悄坏掉的幻灯片。没有自动修复:报错就意味着要重写该元素,让替代方案保住你的设计意图。详见 [`references/shared-standards.md`](references/shared-standards.md)。
- **作图经验法则** —— 只用内联样式;符号用裸 Unicode;一条逻辑文本行 = 一个 `<text>`;箭头用 `marker-end`,裁图用 `<image>` 上的 `clip-path`,填充用渐变/图案。完整契约见参考文档。
- **附赠** —— [`scripts/svg_position_calculator.py`](scripts/svg_position_calculator.py) 可在数值需要映射到像素时,校准数据图表的几何(柱高、饼/环角度、散点位置)。

---

## 环境要求

- Python 3.10+
- `pip install -r requirements.txt`(`python-pptx`、`Pillow`、`lxml`、`svglib`、`reportlab`、`numpy`)
- *可选:* `cairosvg`(更优的旧版 Office PNG 兜底渲染;需系统 `cairo` 库——macOS 上 `brew install cairo`)。没有它时由 `svglib`+`reportlab` 兜底。
- 产物可在 PowerPoint 2016+ 打开(支持原生 SVG 的 Office 显示可编辑形状;更旧的 Office 自动回退到内嵌 PNG)。

---

## 致谢与许可

SVG → DrawingML 转换引擎提取并改编自
**[hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)**(MIT)—— 转换核心的全部功劳归原作者。本仓库把其中的 SVG→PPTX 路径重新打包成一个独立、对 agent 友好的 skill。

以 [MIT 许可证](LICENSE) 发布。内置图标集:
[Heroicons](https://github.com/tailwindlabs/heroicons)(MIT)与
[Lucide](https://github.com/lucide-icons/lucide)(ISC)。
