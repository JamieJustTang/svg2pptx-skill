# SVG → DrawingML Compatibility Contract

The rules an SVG must follow to convert into **native, editable PowerPoint shapes**. PowerPoint's
DrawingML is a strict subset of what SVG can express; anything outside these rules is dropped,
rasterized, or aborts the export. `scripts/svg_quality_checker.py` enforces this as a hard gate.

---

## 1. Banned features

### 1.0 Text must be well-formed XML

| Category | Required | Forbidden |
|---|---|---|
| Typography & symbols (— – © ® → · ± × ÷ ≤ ≥ ≈ α β … emoji) | **raw Unicode** (`—` `→` `±` `α`) | HTML named entities (`&mdash;` `&rarr;` `&alpha;` `&nbsp;` …) |
| XML reserved (`&` `<` `>` `"` `'`) | **XML entities** (`&amp;` `&lt;` `&gt;` `&quot;` `&apos;`) | bare `&` `<` `>` (e.g. `R&D`, `a < b`) |

One offending character invalidates the file and aborts export.

### Structural blacklist

| Banned | Why |
|---|---|
| `mask` | no per-pixel alpha in DrawingML |
| `<style>` / `class` / external CSS | no stylesheet model — use inline attributes (`id` in `<defs>` for references is fine) |
| `<foreignObject>` | embedded HTML/foreign content |
| `<symbol>` + `<use>` | symbol reuse (the only exception: `<use data-icon="lib/name">` icon placeholders, auto-embedded in finalize) |
| `textPath`, `@font-face`, `<animate*>`/`<set>`, `<script>`/event attrs, `<iframe>` | no DrawingML equivalent |

**Conditionally allowed — and worth using** (they become native objects):
- `marker-start` / `marker-end` → `<a:headEnd>` / `<a:tailEnd>` arrowheads (§1.1)
- `clip-path` on `<image>` → cropped native picture geometry (§1.2)
- `<pattern>` fills → `<a:pattFill prst="...">`, preset enum only (§6)

### 1.1 Line-end markers (arrows)

`marker-start`/`marker-end` on `<line>`/`<path>` convert when the `<marker>`:
- is defined in `<defs>` with an `id`; uses `orient="auto"`;
- is a triangle (closed 3-vertex path/polygon), diamond (4-vertex), or `<circle>`/`<ellipse>` (oval);
- has a `fill` matching the line's `stroke`; `markerWidth/Height` ≈ 3–15 (→ sm/med/lg).

> Never reference a marker that isn't defined (`marker-end="url(#x)"` with no `<marker id="x">`) — the
> arrow renders headless and the gate errors.

```xml
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L10,5 L0,10 Z" fill="#1976D2"/>
  </marker>
</defs>
<line x1="100" y1="200" x2="400" y2="200" stroke="#1976D2" stroke-width="3" marker-end="url(#arrow)"/>
```

For chunky/diagonal arrows drawn as polygons, compute rotated vertices from the line direction (§6).

### 1.2 Image clipping

`clip-path` on `<image>` only (not on shapes/text/`<g>`). The `<clipPath>` holds a single child:
`<circle>`/`<ellipse>` → ellipse, `<rect rx>` → roundRect, `<path>`/`<polygon>` → custom geometry.

```xml
<defs><clipPath id="c"><circle cx="200" cy="200" r="100"/></clipPath></defs>
<image href="photo.jpg" x="100" y="100" width="200" height="200" clip-path="url(#c)" preserveAspectRatio="xMidYMid slice"/>
```

---

## 2. PPT-compatibility substitutions

| Banned | Use instead |
|---|---|
| `fill="rgba(255,255,255,0.1)"` | `fill="#FFFFFF" fill-opacity="0.1"` |
| `<g opacity="0.2">…</g>` | `fill-opacity`/`stroke-opacity` on each child |
| `<image opacity="0.3"/>` | overlay `<rect fill="#…" fill-opacity="0.7"/>` after the image |

PPT does not recognize `rgba()`, group opacity, or image opacity.

---

## 3. Canvas / viewBox

- `<svg>` `width`/`height` must equal the `viewBox` pixel size (e.g. `0 0 1280 720`). Slide size is
  read from the viewBox; arbitrary canvas sizes are fine (the export maps px → EMU).
- Work in **pixels**, never `pt`. Define the page background with a `<rect>`.

---

## 4. Text, fonts, grouping

- **Fonts**: every `font-family` stack should end with a pre-installed family (Arial / Helvetica /
  Times New Roman / Calibri / Microsoft YaHei / Consolas …). `@font-face` is forbidden.
- **Colors**: HEX only; transparency via `fill-opacity` / `stroke-opacity`. Inline styles only.
- **One logical line = one `<text>`** with inline `<tspan>` children for color/weight/size runs —
  each `<tspan>` becomes a run in the same editable text frame:
  ```xml
  <text x="100" y="200" font-size="20" fill="#333">Up <tspan fill="#1A73E8" font-weight="bold">62%</tspan> vs. baseline</text>
  ```
  Inline tspans must **not** carry `x`/`y`/`dy` (those start a new line and split the frame); `dx`
  (kerning) is safe. For columns/new lines, use separate `<text>` or an outer line-break tspan.
- **Grouping**: wrap related elements in `<g id="...">` (becomes a PowerPoint group). Avoid one giant
  `<g>` around everything and avoid hundreds of ungrouped atoms. Only `<g opacity>` is banned; plain
  grouping `<g>` is encouraged.
- **Icons** (optional): `<use data-icon="<lib>/<name>" x="" y="" width="48" height="48" fill="#HEX"/>`
  — embedded by `finalize_svg.py` from `templates/icons/` (bundled: `heroicons`, `lucide`).

---

## 5. Pipeline

**One-shot** (recommended): `python3 convert.py input.svg` — stages, gates, finalizes, exports.

**Manual** (full control), one command at a time, in order:
```bash
mkdir -p proj/svg_output && cp in.svg proj/svg_output/01.svg
python3 scripts/svg_quality_checker.py proj   # gate (0 errors required)
python3 scripts/finalize_svg.py        proj   # icon embed, image crop/embed, text flatten, roundRect→path
python3 scripts/svg_to_pptx.py         proj   # export -> proj/exports/<name>_<ts>.pptx
```
Add `--svg-snapshot` to `svg_to_pptx.py` for an extra pixel-faithful `*_svg.pptx`. Never substitute
`cp` for `finalize_svg.py`. Any change to the SVG after finalize requires re-running gate → finalize → export.

---

## 6. Effects that convert to native DrawingML

- **stroke-dasharray** → `<a:prstDash>` (`4,4` dash, `2,2` dot, `8,4` long dash).
- **stroke-linejoin** → round / bevel / miter.
- **text-decoration** → underline / strikethrough.
- **linearGradient / radialGradient** (`fill="url(#id)"`) → `<a:gradFill>`.
- **`<pattern data-pptx-pattern="<preset>">`** → `<a:pattFill prst>` — preset enum only
  (`lgGrid`, `pct20`, `diagCross`, …); an out-of-enum value makes PowerPoint show a repair dialog.
  For exact spacing (e.g. a 40px grid), draw lines as one multi-subpath `<path>` instead.
- **transform: rotate(angle[, cx, cy])** → `<a:xfrm rot>` (works on text too).
- **Arc paths (donut/pie)**: compute endpoints with trig (`x=cx+r·cosθ`, `y=cy+r·sinθ`), start at
  −90°, large-arc flag = 1 when sector > 180°. Concentric stroke "ring" arcs are auto-detected.
- **Polygon arrows on diagonals**: rotate the triangle to the line direction —
  `ux=dx/len, uy=dy/len; px=−uy, py=ux; back=(tip−u·12±p·5)`.
- **Filter shadow/glow**: `feGaussianBlur`+`feOffset` → `<a:outerShdw>`; blur w/o offset → `<a:glow>`.
  Use sparingly — flat fills export cleanest.
