#!/usr/bin/env python
"""Summarize calibration and decision-curve clinical utility."""

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
    parser = argparse.ArgumentParser(description="Create clinical utility tables and SVG drafts.")
    parser.add_argument("--mimic-iv-results", required=True, help="MIMIC-IV cross-db model results directory.")
    parser.add_argument("--mimic-iii-results", required=True, help="MIMIC-III cross-db external validation directory.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    return parser.parse_args()


def read_single(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def useful_range(dca: pd.DataFrame, low: float = 0.10, high: float = 0.75) -> str:
    part = dca[(dca["threshold"] >= low) & (dca["threshold"] <= high)].copy()
    mask = (part["net_benefit_model"] > part["net_benefit_all"]) & (
        part["net_benefit_model"] > part["net_benefit_none"]
    )
    useful = part[mask]
    if useful.empty:
        return "None within 0.10-0.75"
    return f"{useful['threshold'].min():.2f}-{useful['threshold'].max():.2f}"


def make_table(m4_dir: Path, m3_dir: Path) -> pd.DataFrame:
    m4_metrics = read_single(m4_dir / "metrics.csv")
    m4 = m4_metrics[m4_metrics["model"] == "xgboost"].iloc[0]
    m4_dca = read_single(m4_dir / "decision_curve_xgboost.csv")

    m3_metrics = read_single(m3_dir / "metrics_mimiciii_crossdb_with_crrt.csv").iloc[0]
    m3_dca = read_single(m3_dir / "decision_curve_mimiciii_crossdb_with_crrt.csv")

    return pd.DataFrame(
        [
            {
                "Model": "XGBoost cross-database",
                "Cohort": "MIMIC-IV internal test",
                "Calibration intercept": f"{m4['calibration_intercept']:.3f}",
                "Calibration slope": f"{m4['calibration_slope']:.3f}",
                "Brier score": f"{m4['brier']:.3f}",
                "DCA useful threshold range": useful_range(m4_dca),
            },
            {
                "Model": "XGBoost cross-database",
                "Cohort": "MIMIC-III temporal/external validation",
                "Calibration intercept": f"{m3_metrics['calibration_intercept']:.3f}",
                "Calibration slope": f"{m3_metrics['calibration_slope']:.3f}",
                "Brier score": f"{m3_metrics['brier']:.3f}",
                "DCA useful threshold range": useful_range(m3_dca),
            },
        ]
    )


def svg_text(x: float, y: float, text: str, size: int = 12, weight: str = "400", anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{BLACK}">'
        f"{html.escape(str(text))}</text>"
    )


def rotated_svg_text(x: float, y: float, text: str, size: int = 12, weight: str = "400") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="middle" fill="{BLACK}" '
        f'transform="rotate(-90 {x:.1f} {y:.1f})">{html.escape(str(text))}</text>'
    )


def transform(x: float, y: float, x0: float, y0: float, w: float, h: float, y_min: float, y_max: float) -> tuple[float, float]:
    px = x0 + (x - 0.0) / 0.80 * w
    y = min(max(y, y_min), y_max)
    py = y0 + h - (y - y_min) / (y_max - y_min) * h
    return px, py


def polyline(df: pd.DataFrame, y_col: str, x0: float, y0: float, w: float, h: float, y_min: float, y_max: float, color: str, dash: str = "") -> str:
    points = []
    for row in df.itertuples():
        x, y = transform(float(row.threshold), float(getattr(row, y_col)), x0, y0, w, h, y_min, y_max)
        points.append(f"{x:.1f},{y:.1f}")
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2"{dash_attr}/>'


def make_dca_svg(m4_dir: Path, m3_dir: Path, output_dir: Path) -> None:
    m4 = read_single(m4_dir / "decision_curve_xgboost.csv")
    m4["cohort_label"] = "MIMIC-IV"
    m3 = read_single(m3_dir / "decision_curve_mimiciii_crossdb_with_crrt.csv")
    m3["cohort_label"] = "MIMIC-III"
    both = pd.concat([m4, m3], ignore_index=True)
    both = both[both["threshold"] <= 0.80].copy()
    y_min = -0.05
    y_max = 0.45

    width, height = 820, 560
    x0, y0, w, h = 105, 70, 590, 380
    body = [svg_text(30, 32, "Decision curve analysis for the primary model", 16, "700")]
    body.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="white" stroke="{BLACK}" stroke-width="1"/>')
    for frac in [0.2, 0.4, 0.6, 0.8]:
        x = x0 + frac / 0.8 * w
        body.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y0 + h}" stroke="{LIGHT}" stroke-width="1"/>')
        body.append(svg_text(x, y0 + h + 22, f"{frac:.1f}", 10, "400", "middle"))
    for y in [-0.05, 0.0, 0.1, 0.2, 0.3, 0.4]:
        if y_min <= y <= y_max:
            _, py = transform(0, y, x0, y0, w, h, y_min, y_max)
            body.append(f'<line x1="{x0}" y1="{py:.1f}" x2="{x0 + w}" y2="{py:.1f}" stroke="{LIGHT}" stroke-width="1"/>')
            body.append(svg_text(x0 - 10, py + 4, f"{y:.1f}", 10, "400", "end"))

    body.append(polyline(m4[m4["threshold"] <= 0.80], "net_benefit_model", x0, y0, w, h, y_min, y_max, BLUE))
    body.append(polyline(m3[m3["threshold"] <= 0.80], "net_benefit_model", x0, y0, w, h, y_min, y_max, RED))
    body.append(polyline(m3[m3["threshold"] <= 0.80], "net_benefit_all", x0, y0, w, h, y_min, y_max, GRAY, "5,5"))
    body.append(polyline(m3[m3["threshold"] <= 0.80], "net_benefit_none", x0, y0, w, h, y_min, y_max, BLACK, "2,4"))
    body.append(svg_text(x0 + w / 2, y0 + h + 50, "Risk threshold", 12, "400", "middle"))
    body.append(rotated_svg_text(35, y0 + h / 2, "Net benefit", 12))
    legend_x, legend_y = x0 + 420, y0 + 30
    body.append(f'<rect x="{legend_x}" y="{legend_y}" width="180" height="105" fill="white" opacity="0.88" stroke="{LIGHT}" stroke-width="1"/>')
    body.append(f'<rect x="{legend_x + 14}" y="{legend_y + 18}" width="12" height="12" fill="{BLUE}"/>')
    body.append(svg_text(legend_x + 34, legend_y + 29, "MIMIC-IV model", 11))
    body.append(f'<rect x="{legend_x + 14}" y="{legend_y + 42}" width="12" height="12" fill="{RED}"/>')
    body.append(svg_text(legend_x + 34, legend_y + 53, "MIMIC-III external", 11))
    body.append(f'<line x1="{legend_x + 14}" y1="{legend_y + 72}" x2="{legend_x + 28}" y2="{legend_y + 72}" stroke="{GRAY}" stroke-width="2" stroke-dasharray="5,5"/>')
    body.append(svg_text(legend_x + 34, legend_y + 76, "Treat all", 11))
    body.append(f'<line x1="{legend_x + 14}" y1="{legend_y + 94}" x2="{legend_x + 28}" y2="{legend_y + 94}" stroke="{BLACK}" stroke-width="2" stroke-dasharray="2,4"/>')
    body.append(svg_text(legend_x + 34, legend_y + 98, "Treat none", 11))
    (output_dir / "fig_decision_curve.svg").write_text(
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


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    lines = [
        "| " + " | ".join(df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for row in df.to_numpy():
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    m4_dir = Path(args.mimic_iv_results)
    m3_dir = Path(args.mimic_iii_results)

    table = make_table(m4_dir, m3_dir)
    table.to_csv(output_dir / "table4_calibration_clinical_utility.csv", index=False)
    (output_dir / "table4_calibration_clinical_utility.md").write_text(
        "# Table 4. Calibration and clinical utility\n\n" + dataframe_to_markdown(table) + "\n",
        encoding="utf-8",
    )
    make_dca_svg(m4_dir, m3_dir, output_dir)
    print(f"Saved clinical utility outputs to: {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
