# Local Icon Library

This repository vendors a curated subset of official icon packs for scientific-figure work.

## Packs

- `lucide/`
  Source: `https://github.com/lucide-icons/lucide`
  License: ISC
- `heroicons/outline/`
  Source: `https://github.com/tailwindlabs/heroicons`
  License: MIT

## Usage

- Search the registry:
  `python3 scripts/icon_registry.py search "dialogue cognition resource pool"`
- Reference an icon in SVG:
  `<use data-icon="lucide/brain-circuit" x="40" y="60" width="24" height="24" fill="#2563EB"/>`
- Embed icon geometry into the final SVG:
  `python3 scripts/svg_finalize/embed_icons.py workspace/drafts/merged/draft_figure.svg`
