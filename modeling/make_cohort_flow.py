#!/usr/bin/env python
"""Create cohort-flow source tables and an SVG diagram."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "cohort_flow"


BLACK = "#111827"
GRAY = "#6b7280"
LIGHT = "#e5e7eb"
BLUE = "#2f6f9f"
RED = "#b64b4b"
SIC = "#6f7f3f"


def fmt(n: int | str) -> str:
    if isinstance(n, str):
        return n
    return f"{n:,}"


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    lines = [
        "| " + " | ".join(df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for row in df.to_numpy():
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def make_source_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    m4 = pd.read_csv(ROOT / "data" / "mimic_iv_modeling_dataset.csv")
    m3 = pd.read_csv(ROOT / "data" / "mimiciii_modeling_dataset_with_crrt.csv")
    sic = pd.read_csv(ROOT / "data" / "sicdb_modeling_dataset.csv")

    rows = [
        {
            "cohort": "MIMIC-IV",
            "role": "Development/internal validation",
            "step_order": 1,
            "step": "Adult first ICU stays",
            "rows": 67423,
            "icu_stays": 67423,
            "source": "mimic_iv_first_run_summary.md",
        },
        {
            "cohort": "MIMIC-IV",
            "role": "Development/internal validation",
            "step_order": 2,
            "step": "Sepsis-3 ICU stays",
            "rows": 33573,
            "icu_stays": 33573,
            "source": "mimic_iv_first_run_summary.md",
        },
        {
            "cohort": "MIMIC-IV",
            "role": "Development/internal validation",
            "step_order": 3,
            "step": "S-AKI onset cohort",
            "rows": 27241,
            "icu_stays": 27241,
            "source": "mimic_iv_first_run_summary.md",
        },
        {
            "cohort": "MIMIC-IV",
            "role": "Development/internal validation",
            "step_order": 4,
            "step": "Raw landmark rows",
            "rows": 81723,
            "icu_stays": 27241,
            "source": "mimic_iv_first_run_summary.md",
        },
        {
            "cohort": "MIMIC-IV",
            "role": "Development/internal validation",
            "step_order": 5,
            "step": "Eligible/final landmark rows",
            "rows": len(m4),
            "icu_stays": m4["stay_id"].nunique(),
            "source": "data/mimic_iv_modeling_dataset.csv",
        },
        {
            "cohort": "MIMIC-IV",
            "role": "Development/internal validation",
            "step_order": 6,
            "step": "Internal test set",
            "rows": 1393,
            "icu_stays": 1026,
            "source": "results/mimic_iv_crossdb_features/run_config.json",
        },
        {
            "cohort": "MIMIC-III",
            "role": "Primary temporal/external validation",
            "step_order": 1,
            "step": "Adult first ICU stays",
            "rows": 41759,
            "icu_stays": 41759,
            "source": "mimiciii_first_run_summary.md",
        },
        {
            "cohort": "MIMIC-III",
            "role": "Primary temporal/external validation",
            "step_order": 2,
            "step": "Sepsis-approximation ICU stays",
            "rows": 14754,
            "icu_stays": 14754,
            "source": "mimiciii_first_run_summary.md",
        },
        {
            "cohort": "MIMIC-III",
            "role": "Primary temporal/external validation",
            "step_order": 3,
            "step": "S-AKI onset cohort",
            "rows": 10981,
            "icu_stays": 10981,
            "source": "mimiciii_first_run_summary.md",
        },
        {
            "cohort": "MIMIC-III",
            "role": "Primary temporal/external validation",
            "step_order": 4,
            "step": "Raw landmark rows",
            "rows": 32943,
            "icu_stays": 10981,
            "source": "mimiciii_first_run_summary.md",
        },
        {
            "cohort": "MIMIC-III",
            "role": "Primary temporal/external validation",
            "step_order": 5,
            "step": "Eligible landmark rows after prior-CRRT exclusion",
            "rows": len(m3),
            "icu_stays": m3["stay_id"].nunique(),
            "source": "data/mimiciii_modeling_dataset_with_crrt.csv",
        },
        {
            "cohort": "SICdb",
            "role": "Exploratory sensitivity external validation",
            "step_order": 1,
            "step": "Adult admission-sepsis ICU cases",
            "rows": 793,
            "icu_stays": 793,
            "source": "results/sicdb_extraction_summary.json",
        },
        {
            "cohort": "SICdb",
            "role": "Exploratory sensitivity external validation",
            "step_order": 2,
            "step": "Initial creatinine-reconstructed landmark rows",
            "rows": 820,
            "icu_stays": 410,
            "source": "extract_sicdb_dataset.py run log",
        },
        {
            "cohort": "SICdb",
            "role": "Exploratory sensitivity external validation",
            "step_order": 3,
            "step": "Final landmark rows after prior-CRRT exclusion",
            "rows": len(sic),
            "icu_stays": sic["stay_id"].nunique(),
            "source": "data/sicdb_modeling_dataset.csv",
        },
    ]

    flow = pd.DataFrame(rows)
    landmark_rows = []
    for cohort, df in [("MIMIC-IV", m4), ("MIMIC-III", m3), ("SICdb", sic)]:
        for landmark, part in df.groupby("landmark_hour", sort=True):
            landmark_rows.append(
                {
                    "cohort": cohort,
                    "landmark_hour": int(landmark),
                    "rows": int(len(part)),
                    "icu_stays": int(part["stay_id"].nunique()),
                    "events": int(part["aki_progression_48h"].sum()),
                    "event_rate": f"{part['aki_progression_48h'].mean() * 100:.1f}%",
                }
            )
    return flow, pd.DataFrame(landmark_rows)


def text(x: float, y: float, value: str, size: int = 12, weight: str = "400", anchor: str = "middle", color: str = BLACK) -> str:
    import html

    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">'
        f"{html.escape(value)}</text>"
    )


def wrapped_text(
    x: float,
    y: float,
    lines: list[str],
    size: int = 12,
    weight: str = "400",
    anchor: str = "middle",
    color: str = BLACK,
    line_height: int = 16,
) -> list[str]:
    return [text(x, y + i * line_height, line, size, weight, anchor, color) for i, line in enumerate(lines)]


def box(x: float, y: float, w: float, h: float, title: str, rows: list[str], color: str) -> list[str]:
    title_lines = [title]
    title_size = 13
    if title == "Eligible landmark rows after prior-CRRT exclusion":
        title_lines = ["Eligible landmark rows", "after prior-CRRT exclusion"]
        title_size = 12
    elif title == "Initial creatinine-reconstructed landmark rows":
        title_lines = ["Initial creatinine-reconstructed", "landmark rows"]
        title_size = 12
    elif title == "Final landmark rows after prior-CRRT exclusion":
        title_lines = ["Final landmark rows", "after prior-CRRT exclusion"]
        title_size = 12

    body = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" fill="white" stroke="{color}" stroke-width="2"/>',
        *wrapped_text(x + w / 2, y + 24, title_lines, title_size, "700", line_height=15),
    ]
    row_start = y + 49 + (len(title_lines) - 1) * 10
    for i, row in enumerate(rows):
        body.append(text(x + w / 2, row_start + i * 18, row, 11, "400", color=GRAY))
    return body


def arrow(x1: float, y1: float, x2: float, y2: float, color: str) -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="1.8" marker-end="url(#arrow)"/>'
    )


def make_svg(flow: pd.DataFrame, landmark: pd.DataFrame) -> str:
    width, height = 1320, 840
    body: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L8,4 L0,8 Z" fill="#6b7280"/></marker></defs>',
        '<rect width="100%" height="100%" fill="white"/>',
        text(40, 38, "Cohort construction and analysis sets", 18, "700", "start"),
    ]
    specs = [
        ("MIMIC-IV", BLUE, 65),
        ("MIMIC-III", RED, 485),
        ("SICdb", SIC, 905),
    ]
    box_w = 330
    y_positions = [80, 175, 270, 365, 460, 555]
    for cohort, color, x in specs:
        part = flow[flow["cohort"] == cohort].sort_values("step_order")
        body.append(text(x + 145, 64, cohort, 15, "700"))
        for i, row in enumerate(part.itertuples(index=False)):
            y = y_positions[i]
            title = row.step
            rows = [f"Rows: {fmt(int(row.rows))}", f"ICU stays: {fmt(int(row.icu_stays))}"]
            if cohort == "MIMIC-IV" and row.step == "Internal test set":
                rows.append("Primary internal test")
            if cohort == "SICdb" and i == len(part) - 1:
                rows.append("Exploratory only")
            body.extend(box(x, y, box_w, 76, title, rows, color))
            if i < len(part) - 1:
                body.append(arrow(x + box_w / 2, y + 76, x + box_w / 2, y_positions[i + 1], GRAY))

        lpart = landmark[landmark["cohort"] == cohort]
        y = 675
        landmark_lines = [
            f"{int(r.landmark_hour)}h: {int(r.rows):,} rows; events {int(r.events):,} ({r.event_rate})"
            for r in lpart.itertuples(index=False)
        ]
        body.extend(box(x, y, box_w, 112, "Final landmark rows by time", [
            *landmark_lines,
            f"Total events: {int(lpart['events'].sum()):,}",
        ], color))

    body.append(text(70, 820, "SICdb and eICU are exploratory sensitivity/transportability analyses and are not co-primary external validations.", 11, "400", "start", GRAY))
    body.append("</svg>")
    return "\n".join(body)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    flow, landmark = make_source_tables()
    flow.to_csv(OUT_DIR / "cohort_flow_source_table.csv", index=False)
    landmark.to_csv(OUT_DIR / "cohort_landmark_event_table.csv", index=False)
    md = [
        "# Cohort Flow Source Tables",
        "",
        "## Cohort Attrition",
        "",
        dataframe_to_markdown(flow),
        "",
        "## Landmark Event Counts",
        "",
        dataframe_to_markdown(landmark),
        "",
        "Note: SICdb early-stage counts are limited to counts reconstructable from the current extractor and run logs. eICU is not included in the primary flow diagram because it is retained only as an exploratory transportability stress test.",
    ]
    (OUT_DIR / "cohort_flow_source_tables.md").write_text("\n".join(md), encoding="utf-8")
    (OUT_DIR / "fig_cohort_flow.svg").write_text(make_svg(flow, landmark), encoding="utf-8")
    print(f"Saved cohort flow outputs to: {OUT_DIR}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
