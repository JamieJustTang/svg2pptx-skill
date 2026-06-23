#!/usr/bin/env python3
"""
svg2pptx-skill — one-shot SVG → native editable PowerPoint converter.

The underlying engine works on a project directory containing a `svg_output/`
folder. This wrapper hides that: point it at a single .svg (or a folder of
.svg files for a multi-page deck) and it stages, quality-checks, finalizes and
exports for you, dropping the .pptx next to your input.

Examples
--------
    python3 convert.py diagram.svg                 # -> diagram.pptx
    python3 convert.py diagram.svg -o out.pptx      # custom output path
    python3 convert.py slides/ -o deck.pptx         # folder of svgs -> one deck
    python3 convert.py diagram.svg --check-only      # just run the quality gate
    python3 convert.py diagram.svg --force           # export even if the gate errors
    python3 convert.py diagram.svg --svg-snapshot    # also emit a pixel-faithful *_svg.pptx
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
SCRIPTS = REPO / "scripts"
PY = sys.executable


def run(cmd):
    """Run a subcommand, streaming output; return its exit code."""
    print(f"\n$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd).returncode


def collect_svgs(src: Path):
    if src.is_dir():
        files = sorted(p for p in src.glob("*.svg"))
        if not files:
            sys.exit(f"[error] no .svg files found in {src}")
        return files
    if src.suffix.lower() != ".svg":
        sys.exit(f"[error] input must be a .svg file or a folder of them: {src}")
    return [src]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert SVG → native editable PPTX.")
    ap.add_argument("input", type=Path, help="an .svg file, or a folder of .svg files (multi-page)")
    ap.add_argument("-o", "--output", type=Path, help="output .pptx path (default: alongside input)")
    ap.add_argument("--check-only", action="store_true", help="run the quality gate and stop")
    ap.add_argument("--force", action="store_true", help="export even if the quality gate reports errors")
    ap.add_argument("--svg-snapshot", action="store_true", help="also emit a pixel-faithful *_svg.pptx")
    ap.add_argument("--keep", action="store_true", help="keep the temporary working directory")
    args = ap.parse_args(argv)

    src = args.input
    if not src.exists():
        sys.exit(f"[error] not found: {src}")
    svgs = collect_svgs(src)

    work = Path(tempfile.mkdtemp(prefix="svg2pptx_"))
    svg_out = work / "svg_output"
    svg_out.mkdir(parents=True)
    for i, svg in enumerate(svgs, 1):
        shutil.copy(svg, svg_out / f"{i:02d}_{svg.stem}.svg")

    try:
        # 1) quality gate
        gate = run([PY, str(SCRIPTS / "svg_quality_checker.py"), str(work)])
        if gate != 0 and not args.force:
            print("\n[blocked] Quality gate found errors. Fix the SVG and retry, "
                  "or pass --force to export anyway (elements may be dropped).")
            return gate
        if args.check_only:
            return 0

        # 2) finalize  3) export
        if run([PY, str(SCRIPTS / "finalize_svg.py"), str(work)]) != 0:
            return 1
        export_cmd = [PY, str(SCRIPTS / "svg_to_pptx.py"), str(work), "--no-notes"]
        if args.svg_snapshot:
            export_cmd.append("--svg-snapshot")
        if run(export_cmd) != 0:
            return 1

        produced = sorted((work / "exports").glob("*.pptx"))
        native = [p for p in produced if not p.stem.endswith("_svg")]
        if not native:
            sys.exit("[error] export produced no .pptx")

        default_name = (src.stem if src.is_file() else src.name) + ".pptx"
        dest = args.output or (src.parent / default_name if src.is_file() else src.parent / default_name)
        dest = dest.resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(native[0], dest)
        print(f"\n[ok] saved: {dest}")
        if args.svg_snapshot:
            snap = [p for p in produced if p.stem.endswith("_svg")]
            if snap:
                snap_dest = dest.with_name(dest.stem + "_svg.pptx")
                shutil.copy(snap[0], snap_dest)
                print(f"[ok] saved: {snap_dest}  (pixel-faithful reference)")
        return 0
    finally:
        if args.keep:
            print(f"[kept] working dir: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
