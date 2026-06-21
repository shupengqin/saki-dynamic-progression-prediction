#!/usr/bin/env python
"""Export manuscript SVG figures to PNG and PDF using a local Chromium browser."""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path


FIGURES = [
    ("fig_cohort_flow", Path("results/cohort_flow/fig_cohort_flow.svg")),
    ("fig_performance_forest", Path("results/figures_svg/fig_performance_forest.svg")),
    ("fig_multicohort_calibration", Path("results/figures_svg/fig_multicohort_calibration.svg")),
    ("fig_decision_curve", Path("results/clinical_utility/fig_decision_curve.svg")),
    ("fig_xgboost_global_importance", Path("results/figures_svg/fig_xgboost_global_importance.svg")),
    ("fig_xgboost_binned_dependence", Path("results/figures_svg/fig_xgboost_binned_dependence.svg")),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", required=True, help="Path to msedge.exe or chrome.exe.")
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--output-dir", default="results/figures_exported", help="Output directory.")
    parser.add_argument("--scale", type=int, default=3, help="PNG scale factor.")
    parser.add_argument("--padding", type=int, default=40, help="White padding around each SVG, in CSS pixels.")
    return parser.parse_args()


def svg_size(svg_text: str) -> tuple[int, int]:
    match = re.search(r"<svg[^>]*\bwidth=\"([0-9.]+)\"[^>]*\bheight=\"([0-9.]+)\"", svg_text)
    if not match:
        viewbox = re.search(r"<svg[^>]*\bviewBox=\"[^\"]*?([0-9.]+)\s+([0-9.]+)\"", svg_text)
        if viewbox:
            return int(float(viewbox.group(1))), int(float(viewbox.group(2)))
        return 1200, 800
    return int(float(match.group(1))), int(float(match.group(2)))


def make_html(svg_path: Path, html_path: Path, width: int, height: int, padding: int) -> tuple[int, int]:
    svg_uri = svg_path.resolve().as_uri()
    page_width = width + padding * 2
    page_height = height + padding * 2
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: {page_width}px;
      height: {page_height}px;
      background: white;
      overflow: hidden;
    }}
    body {{
      box-sizing: border-box;
      padding: {padding}px;
    }}
    img {{
      display: block;
      width: {width}px;
      height: {height}px;
    }}
  </style>
</head>
<body>
  <img src="{svg_uri}" alt="">
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    return page_width, page_height


def run_browser(browser: Path, html_path: Path, png_path: Path, pdf_path: Path, width: int, height: int, scale: int) -> None:
    url = html_path.resolve().as_uri()
    user_data_dir = Path(tempfile.mkdtemp(prefix="saki_browser_export_"))
    common = [
        str(browser),
        "--headless",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        "--no-sandbox",
        "--no-first-run",
        f"--user-data-dir={user_data_dir}",
        f"--window-size={width},{height}",
        f"--force-device-scale-factor={scale}",
    ]
    subprocess.run(common + [f"--screenshot={png_path}", url], check=True)
    subprocess.run(common + [f"--print-to-pdf={pdf_path}", "--print-to-pdf-no-header", url], check=True)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    browser = Path(args.browser)
    out_dir = (root / args.output_dir).resolve()
    html_dir = out_dir / "_html"
    out_dir.mkdir(parents=True, exist_ok=True)
    html_dir.mkdir(parents=True, exist_ok=True)

    rows = ["# Exported Figure Files", ""]
    for name, rel_svg in FIGURES:
        svg_path = root / rel_svg
        if not svg_path.exists():
            rows.append(f"- MISSING: `{rel_svg}`")
            continue
        svg_text = svg_path.read_text(encoding="utf-8")
        width, height = svg_size(svg_text)
        html_path = html_dir / f"{name}.html"
        png_path = out_dir / f"{name}.png"
        pdf_path = out_dir / f"{name}.pdf"
        page_width, page_height = make_html(svg_path, html_path, width, height, args.padding)
        run_browser(browser, html_path, png_path, pdf_path, page_width, page_height, args.scale)
        rows.append(f"- `{name}`: PNG `{png_path.name}`, PDF `{pdf_path.name}`; source `{rel_svg}`; source size {width}x{height}px; exported page {page_width}x{page_height}px")

    manifest = out_dir / "export_manifest.md"
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Saved exported figures to {out_dir}", flush=True)
    print(f"Saved manifest to {manifest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
