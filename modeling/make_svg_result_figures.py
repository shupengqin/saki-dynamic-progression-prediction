#!/usr/bin/env python
"""Create dependency-free SVG drafts for result figures."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

import pandas as pd


BLUE = "#2f6f9f"
RED = "#b64b4b"
GRAY = "#6b7280"
LIGHT = "#e5e7eb"
BLACK = "#111827"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Make lightweight SVG figure drafts.")
    parser.add_argument("--explanation-dir", required=True)
    parser.add_argument("--validation-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--top-n", type=int, default=12)
    return parser.parse_args()


def svg_text(x: float, y: float, text: str, size: int = 12, weight: str = "400", anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{BLACK}">'
        f"{html.escape(str(text))}</text>"
    )


def save_svg(path: Path, width: int, height: int, body: list[str]) -> None:
    path.write_text(
        "\n".join(
            [
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                '<rect width="100%" height="100%" fill="white"/>',
                *body,
                "</svg>",
            ]
        ),
        encoding="utf-8",
    )


def make_importance_svg(explanation_dir: Path, output_dir: Path, top_n: int) -> None:
    df = pd.read_csv(explanation_dir / "xgboost_contribution_importance.csv").head(top_n).copy()
    df = df.iloc[::-1].reset_index(drop=True)
    width, height = 920, 500
    left, right, top, row_h = 230, 60, 55, 31
    max_val = df["mean_abs_contribution"].max()
    chart_w = width - left - right
    body = [svg_text(30, 30, "A  Global XGBoost contribution importance", 16, "700")]
    body.append(svg_text(left, 52, "Mean absolute contribution to log-odds", 11, "400"))
    for i, row in df.iterrows():
        y = top + i * row_h
        label = str(row["clean_feature"])
        value = float(row["mean_abs_contribution"])
        bar_w = chart_w * value / max_val if max_val else 0
        body.append(svg_text(left - 12, y + 16, label, 11, "400", "end"))
        body.append(f'<rect x="{left}" y="{y}" width="{bar_w:.1f}" height="20" fill="{BLUE}" rx="2"/>')
        body.append(svg_text(left + bar_w + 6, y + 15, f"{value:.3f}", 10, "400"))
    save_svg(output_dir / "fig_xgboost_global_importance.svg", width, height, body)


def make_dependence_svg(explanation_dir: Path, output_dir: Path) -> None:
    dep = pd.read_csv(explanation_dir / "xgboost_binned_dependence.csv")
    features = ["creatinine_recent", "urine_output_total", "sbp_mean", "lactate_max"]
    width, height = 980, 620
    panel_w, panel_h = 410, 220
    origins = [(80, 70), (560, 70), (80, 370), (560, 370)]
    body = [svg_text(30, 30, "B  Binned feature-contribution relationships", 16, "700")]
    for feature, (x0, y0) in zip(features, origins):
        part = dep[dep["feature"] == feature].copy()
        if part.empty:
            continue
        x_min, x_max = part["raw_median"].min(), part["raw_median"].max()
        y_min, y_max = part["mean_contribution"].min(), part["mean_contribution"].max()
        pad = 0.08 * (y_max - y_min or 1)
        y_min, y_max = y_min - pad, y_max + pad
        body.append(svg_text(x0, y0 - 18, feature, 12, "700"))
        body.append(f'<line x1="{x0}" y1="{y0 + panel_h}" x2="{x0 + panel_w}" y2="{y0 + panel_h}" stroke="{BLACK}" stroke-width="1"/>')
        body.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + panel_h}" stroke="{BLACK}" stroke-width="1"/>')
        zero_y = y0 + panel_h - (0 - y_min) / (y_max - y_min) * panel_h if y_min <= 0 <= y_max else None
        if zero_y is not None:
            body.append(f'<line x1="{x0}" y1="{zero_y:.1f}" x2="{x0 + panel_w}" y2="{zero_y:.1f}" stroke="{LIGHT}" stroke-width="1"/>')
        points = []
        for row in part.itertuples():
            x = x0 + (row.raw_median - x_min) / (x_max - x_min or 1) * panel_w
            y = y0 + panel_h - (row.mean_contribution - y_min) / (y_max - y_min or 1) * panel_h
            points.append((x, y))
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        body.append(f'<polyline points="{poly}" fill="none" stroke="{BLUE}" stroke-width="2"/>')
        for x, y in points:
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{BLUE}"/>')
        body.append(svg_text(x0, y0 + panel_h + 34, "Feature value, decile median", 10, "400"))
        body.append(svg_text(x0 - 12, y0 + 4, f"{y_max:.2f}", 9, "400", "end"))
        body.append(svg_text(x0 - 12, y0 + panel_h, f"{y_min:.2f}", 9, "400", "end"))
    save_svg(output_dir / "fig_xgboost_binned_dependence.svg", width, height, body)


def make_calibration_svg(validation_dir: Path, output_dir: Path) -> None:
    cal_files = list(validation_dir.glob("calibration_bins_*.csv"))
    if not cal_files:
        return
    df = pd.read_csv(cal_files[0])
    width, height = 560, 520
    x0, y0, size = 90, 65, 380
    body = [svg_text(30, 30, "C  External validation calibration", 16, "700")]
    body.append(f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" fill="white" stroke="{BLACK}" stroke-width="1"/>')
    for frac in [0.25, 0.5, 0.75]:
        pos = x0 + frac * size
        body.append(f'<line x1="{pos:.1f}" y1="{y0}" x2="{pos:.1f}" y2="{y0 + size}" stroke="{LIGHT}" stroke-width="1"/>')
        pos_y = y0 + size - frac * size
        body.append(f'<line x1="{x0}" y1="{pos_y:.1f}" x2="{x0 + size}" y2="{pos_y:.1f}" stroke="{LIGHT}" stroke-width="1"/>')
    body.append(f'<line x1="{x0}" y1="{y0 + size}" x2="{x0 + size}" y2="{y0}" stroke="{GRAY}" stroke-width="1.2" stroke-dasharray="5,5"/>')
    points = []
    for row in df.itertuples():
        x = x0 + float(row.predicted_mean) * size
        y = y0 + size - float(row.observed_rate) * size
        points.append((x, y))
    body.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}" fill="none" stroke="{RED}" stroke-width="2"/>')
    for x, y in points:
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{RED}"/>')
    body.append(svg_text(x0 + size / 2, y0 + size + 42, "Predicted risk", 12, "400", "middle"))
    body.append(svg_text(18, y0 + size / 2, "Observed rate", 12, "400"))
    body.append(svg_text(x0, y0 + size + 20, "0", 10))
    body.append(svg_text(x0 + size, y0 + size + 20, "1", 10, "400", "middle"))
    body.append(svg_text(x0 - 18, y0 + size, "0", 10, "400", "end"))
    body.append(svg_text(x0 - 18, y0 + 4, "1", 10, "400", "end"))
    save_svg(output_dir / "fig_external_calibration.svg", width, height, body)


def main() -> int:
    args = parse_args()
    explanation_dir = Path(args.explanation_dir)
    validation_dir = Path(args.validation_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    make_importance_svg(explanation_dir, output_dir, args.top_n)
    make_dependence_svg(explanation_dir, output_dir)
    make_calibration_svg(validation_dir, output_dir)
    print(f"Saved SVG figure drafts to: {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
