# PNG → spec-compliant SVG — ready-to-use prompt

This skill converts **SVG**, not raster pixels. To start from a **PNG/JPG** (e.g. a screenshot or
an AI-generated draft), first have a strong vision model **redraw** it as a clean, editable SVG that
already obeys this skill's [`shared-standards.md`](shared-standards.md) — then run `convert.py`.

**Recommended models** (vision-capable, strong at SVG): **GPT-5.5 Pro**, **Claude Opus 4.6 or
newer** (4.8 latest), or any current SOTA model. Smaller/older models produce sloppier geometry and
more gate errors.

## How to use

1. Open a chat with a recommended model and **attach your PNG/JPG**.
2. Paste the prompt below as your message.
3. Save the returned code as `figure.svg`.
4. `python3 convert.py figure.svg` → editable `.pptx`.
5. If the quality gate reports an error, paste it back to the model: *"Fix this and re-output the full
   SVG"* — repeat until it passes.

---

## The prompt (copy everything in the block)

```
You are an expert technical illustrator and SVG engineer. I am attaching a raster image (PNG/JPG)
of a diagram — a scientific figure, mechanism, architecture, flowchart, or chart. Redraw it as ONE
clean, fully EDITABLE SVG that faithfully reproduces the original AND converts losslessly into native
PowerPoint shapes (DrawingML).

## Fidelity — match the original
- Reproduce the layout, relative positions, sizes, and colors (sample the exact HEX values).
- Reproduce EVERY text label verbatim, in its original language — do not translate, summarize, or
  invent text. Keep all text as real <text> elements (editable), never as outlines or images.
- Redraw every visual as a vector primitive (rect, circle, ellipse, line, path, polygon) — do NOT
  embed the bitmap.
- Preserve arrow directions and relationship semantics (activation / flow vs. inhibition).

## Canvas
- Set <svg> width, height, and viewBox to the image's pixel dimensions; width and height MUST equal
  the viewBox (e.g. width="1280" height="720" viewBox="0 0 1280 720").
- Add a background <rect> for the page color. Work in pixels only (never pt).

## Hard rules — PowerPoint/DrawingML compatibility (do NOT violate any)
- Inline attributes ONLY. No <style>, no class, no CSS, no @font-face.
- BANNED elements/attrs: mask, <foreignObject>, <symbol>+<use>, textPath, <animate>/<set>, <script>,
  <iframe>, group opacity (<g opacity>), image opacity, and rgba()/hsla() colors.
- Colors: HEX only. Transparency via fill-opacity / stroke-opacity.
- Characters: write typography & symbols as RAW Unicode (— – → ± × ÷ ≤ ≥ ≈ ° α β γ · …). Escape ONLY
  the XML reserved characters as entities: & < > " '  →  &amp; &lt; &gt; &quot; &apos;. NEVER use HTML
  named entities (&nbsp; &mdash; &rarr; &alpha; …) — they abort the conversion.
- Text: one logical line = ONE <text> element; use inline <tspan> only for color/weight/size runs on
  that same line. Inline <tspan> must NOT carry x, y, or dy (those start a new line and split the
  frame) — use dx only for kerning. For separate lines or columns, use separate <text> elements (or
  an outer line-break <tspan x=".." dy="..">).
- Fonts: every font-family stack must END with a pre-installed family (Arial, Helvetica, Calibri,
  Times New Roman, Microsoft YaHei, SimSun, or Consolas).
- Arrows: use marker-start / marker-end ONLY with a <marker> defined in <defs>, with orient="auto",
  a triangle / diamond / circle (closed) shape, and the marker's fill EQUAL to the line's stroke
  color. Never reference a marker id you did not define. For inhibition (⊥ / T-bar), draw an explicit
  short perpendicular <line>, not a marker.
- clip-path is allowed ONLY on <image> (with a single shape child in its <clipPath>). For non-image
  shapes, draw the target geometry directly — do not clip.
- Group related elements in <g id="..."> with descriptive ids (each becomes a PowerPoint group).
- Effects that are fine: linearGradient/radialGradient in <defs> (fill="url(#id)"),
  stroke-dasharray, transform="rotate(angle, cx, cy)". For donut/pie sectors, compute arc endpoints
  with trigonometry (x=cx+r·cosθ, y=cy+r·sinθ; start at -90°; large-arc flag = 1 when the sector > 180°).

## Self-check before you answer
Confirm: width/height == viewBox; NO banned features; NO HTML named entities; NO x/y/dy on inline
<tspan>; every referenced marker is defined with a matching color; all text is present and verbatim.

## Output
Output ONLY the SVG code, starting with <svg ...> and ending with </svg>. No prose, no markdown fences.
```

---

> **Fidelity vs. cleanup:** the model recreates the figure semantically, so you get editable text and
> clean shapes — far better than auto-tracing a bitmap (which turns text into uneditable outlines).
> For complex figures, expect one or two fix rounds against the quality-gate output.
