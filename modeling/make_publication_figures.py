#!/usr/bin/env python
"""Generate publication-oriented SVG result figures without plotting dependencies."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

import pandas as pd


BLACK = "#111827"
GRAY = "#6b7280"
LIGHT = "#e5e7eb"
M4 = "#2f6f9f"
M3 = "#b64b4b"
SIC = "#6f7f3f"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create publication SVG figures.")
    parser.add_argument("--performance-summary", required=True)
    parser.add_argument("--mimic-iv-calibration", required=True)
    parser.add_argument("--mimic-iii-calibration", required=True)
    parser.add_argument("--sicdb-calibration", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def svg_text(
    x: float,
    y: float,
    text: str,
    size: int = 12,
    weight: str = "400",
    anchor: str = "start",
    color: str = BLACK,
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">'
        f"{html.escape(str(text))}</text>"
    )


def rotated_svg_text(
    x: float,
    y: float,
    text: str,
    size: int = 12,
    weight: str = "400",
    color: str = BLACK,
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="middle" fill="{color}" '
        f'transform="rotate(-90 {x:.1f} {y:.1f})">{html.escape(str(text))}</text>'
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


def x_scale(value: float, x0: float, width: float, low: float, high: float) -> float:
    return x0 + (value - low) / (high - low) * width


def make_forest_svg(perf_path: Path, output_dir: Path) -> None:
    perf = pd.read_csv(perf_path)
    keep = perf[
        (perf["landmark"] == "overall")
        & (
            ((perf["cohort"] == "MIMIC-IV internal test") & (perf["model"] == "xgboost_crossdb"))
            | ((perf["cohort"] == "MIMIC-III external with CRRT") & (perf["model"] == "xgboost_crossdb"))
            | ((perf["cohort"] == "SICdb sensitivity external") & (perf["model"] == "xgboost_crossdb"))
        )
    ].copy()
    order = ["MIMIC-IV internal test", "MIMIC-III external with CRRT", "SICdb sensitivity external"]
    labels = {
        "MIMIC-IV internal test": "MIMIC-IV internal",
        "MIMIC-III external with CRRT": "MIMIC-III external",
        "SICdb sensitivity external": "SICdb sensitivity",
    }
    colors = {
        "MIMIC-IV internal test": M4,
        "MIMIC-III external with CRRT": M3,
        "SICdb sensitivity external": SIC,
    }
    keep["cohort_order"] = keep["cohort"].map({c: i for i, c in enumerate(order)})
    keep = keep.sort_values("cohort_order")

    width, height = 980, 420
    x0, chart_w = 300, 470
    low, high = 0.45, 0.85
    row_y = [115, 195, 275]
    body = [svg_text(30, 38, "A  Discrimination of the primary model across cohorts", 17, "700")]
    body.append(svg_text(x0, 70, "AUROC (95% CI)", 12, "700"))
    body.append(f'<line x1="{x0}" y1="310" x2="{x0 + chart_w}" y2="310" stroke="{BLACK}" stroke-width="1"/>')
    for tick in [0.5, 0.6, 0.7, 0.8]:
        x = x_scale(tick, x0, chart_w, low, high)
        body.append(f'<line x1="{x:.1f}" y1="84" x2="{x:.1f}" y2="310" stroke="{LIGHT}" stroke-width="1"/>')
        body.append(f'<line x1="{x:.1f}" y1="310" x2="{x:.1f}" y2="317" stroke="{BLACK}" stroke-width="1"/>')
        body.append(svg_text(x, 335, f"{tick:.1f}", 11, "400", "middle"))
    body.append(svg_text(x0 + chart_w / 2, 365, "AUROC", 12, "400", "middle"))

    for y, row in zip(row_y, keep.itertuples(index=False)):
        color = colors[row.cohort]
        body.append(svg_text(45, y + 4, labels[row.cohort], 13, "700"))
        body.append(svg_text(45, y + 24, f"{int(row.n_rows):,} rows; {int(row.n_stays):,} stays", 11, "400", color=GRAY))
        body.append(svg_text(45, y + 42, f"Event rate {row.event_rate * 100:.1f}%", 11, "400", color=GRAY))
        lo = x_scale(float(row.auroc_ci_low), x0, chart_w, low, high)
        mid = x_scale(float(row.auroc), x0, chart_w, low, high)
        hi = x_scale(float(row.auroc_ci_high), x0, chart_w, low, high)
        body.append(f'<line x1="{lo:.1f}" y1="{y:.1f}" x2="{hi:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="3"/>')
        body.append(f'<circle cx="{mid:.1f}" cy="{y:.1f}" r="7" fill="{color}"/>')
        body.append(svg_text(800, y + 4, f"{row.auroc:.3f} ({row.auroc_ci_low:.3f}-{row.auroc_ci_high:.3f})", 12, "400"))
        body.append(svg_text(800, y + 24, f"AUPRC {row.auprc:.3f}; Brier {row.brier:.3f}", 11, "400", color=GRAY))
    save_svg(output_dir / "fig_performance_forest.svg", width, height, body)


def read_calibration(path: Path, label: str, color: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["label"] = label
    df["color"] = color
    return df


def make_calibration_svg(paths: dict[str, Path], output_dir: Path) -> None:
    cal = pd.concat(
        [
            read_calibration(paths["m4"], "MIMIC-IV internal", M4),
            read_calibration(paths["m3"], "MIMIC-III external", M3),
            read_calibration(paths["sic"], "SICdb sensitivity", SIC),
        ],
        ignore_index=True,
    )
    width, height = 820, 640
    x0, y0, size = 125, 72, 430
    body = [svg_text(30, 38, "B  Calibration by predicted-risk decile", 17, "700")]
    body.append(f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" fill="white" stroke="{BLACK}" stroke-width="1"/>')
    for tick in [0.0, 0.25, 0.5, 0.75, 1.0]:
        x = x0 + tick * size
        y = y0 + size - tick * size
        body.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y0 + size}" stroke="{LIGHT}" stroke-width="1"/>')
        body.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + size}" y2="{y:.1f}" stroke="{LIGHT}" stroke-width="1"/>')
        body.append(svg_text(x, y0 + size + 22, f"{tick:.2f}".rstrip("0").rstrip("."), 10, "400", "middle"))
        body.append(svg_text(x0 - 12, y + 4, f"{tick:.2f}".rstrip("0").rstrip("."), 10, "400", "end"))
    body.append(f'<line x1="{x0}" y1="{y0 + size}" x2="{x0 + size}" y2="{y0}" stroke="{GRAY}" stroke-width="1.4" stroke-dasharray="5,5"/>')

    for label, part in cal.groupby("label", sort=False):
        color = part["color"].iloc[0]
        points = []
        for row in part.itertuples(index=False):
            x = x0 + float(row.predicted_mean) * size
            y = y0 + size - float(row.observed_rate) * size
            points.append((x, y))
        body.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}" fill="none" stroke="{color}" stroke-width="2.4"/>')
        for x, y in points:
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="{color}"/>')

    body.append(svg_text(x0 + size / 2, y0 + size + 54, "Predicted risk", 12, "400", "middle"))
    body.append(rotated_svg_text(45, y0 + size / 2, "Observed event rate", 12))
    legend_x, legend_y = 600, 130
    for i, (label, color) in enumerate([("MIMIC-IV internal", M4), ("MIMIC-III external", M3), ("SICdb sensitivity", SIC)]):
        y = legend_y + i * 30
        body.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 26}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        body.append(f'<circle cx="{legend_x + 13}" cy="{y}" r="4.2" fill="{color}"/>')
        body.append(svg_text(legend_x + 36, y + 4, label, 12))
    body.append(svg_text(600, 260, "Dashed line: perfect calibration", 11, "400", color=GRAY))
    body.append(svg_text(600, 282, "SICdb shows systematic", 11, "400", color=GRAY))
    body.append(svg_text(600, 300, "overprediction before", 11, "400", color=GRAY))
    body.append(svg_text(600, 318, "local recalibration.", 11, "400", color=GRAY))
    save_svg(output_dir / "fig_multicohort_calibration.svg", width, height, body)


def main() -> int:
    args = parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    make_forest_svg(Path(args.performance_summary), out)
    make_calibration_svg(
        {
            "m4": Path(args.mimic_iv_calibration),
            "m3": Path(args.mimic_iii_calibration),
            "sic": Path(args.sicdb_calibration),
        },
        out,
    )
    print(f"Saved publication figures to: {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
