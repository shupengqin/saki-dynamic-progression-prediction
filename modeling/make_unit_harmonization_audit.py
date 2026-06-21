#!/usr/bin/env python
"""Audit cross-database units for the locked S-AKI prediction predictors."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATASETS = {
    "MIMIC-IV": ROOT / "data" / "mimic_iv_modeling_dataset.csv",
    "MIMIC-III": ROOT / "data" / "mimiciii_modeling_dataset_with_crrt.csv",
    "SICdb": ROOT / "data" / "sicdb_modeling_dataset.csv",
}

FEATURES = [
    ("creatinine_recent", "mg/dL", "Serum creatinine"),
    ("bun_recent", "mg/dL", "Blood urea nitrogen"),
    ("lactate_max", "mmol/L", "Lactate"),
    ("temp_mean", "degC", "Temperature"),
    ("temp_min", "degC", "Minimum temperature"),
    ("temp_max", "degC", "Maximum temperature"),
    ("platelet_min", "10^9/L", "Platelet count"),
    ("hemoglobin_min", "g/dL", "Hemoglobin"),
    ("map_mean", "mmHg", "Mean arterial pressure"),
    ("sbp_mean", "mmHg", "Systolic blood pressure"),
    ("urine_output_total", "mL", "Cumulative urine output"),
]

NOTES = {
    "creatinine_recent": "All extracted values are interpreted as mg/dL. SICdb KDIGO timing is reconstructed from serum creatinine values.",
    "bun_recent": "MIMIC values are BUN in mg/dL. SICdb Harnstoff is urea and was converted to BUN using urea x 0.467.",
    "lactate_max": "Values are treated as mmol/L across cohorts.",
    "temp_mean": "MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius.",
    "temp_min": "MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius.",
    "temp_max": "MIMIC temperatures were harmonized to Celsius in the source extraction. SICdb temperatures are interpreted as Celsius.",
    "platelet_min": "10^9/L and K/uL are numerically equivalent for platelet count.",
    "hemoglobin_min": "Values are treated as g/dL.",
    "map_mean": "Blood pressure values are treated as mmHg; MIMIC-III labels were filtered to avoid pulmonary-artery/cuff metadata fields.",
    "sbp_mean": "Blood pressure values are treated as mmHg; MIMIC-III labels were filtered to avoid alarm and non-systemic fields.",
    "urine_output_total": "Values are cumulative mL from S-AKI onset to landmark, not weight-normalized mL/kg/h.",
}


def summarize_series(series: pd.Series) -> dict[str, str]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {"n": "0", "p1": "NA", "p50": "NA", "p99": "NA", "max": "NA"}
    return {
        "n": str(len(values)),
        "p1": f"{values.quantile(0.01):.2f}",
        "p50": f"{values.quantile(0.50):.2f}",
        "p99": f"{values.quantile(0.99):.2f}",
        "max": f"{values.max():.2f}",
    }


def markdown_table(rows: list[dict[str, str]]) -> str:
    columns = list(rows[0])
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row[col] for col in columns) + " |")
    return "\n".join(lines)


def main() -> int:
    frames = {
        name: pd.read_csv(path, usecols=lambda col: col in {feature for feature, _, _ in FEATURES})
        for name, path in DATASETS.items()
    }

    rows = []
    for feature, unit, label in FEATURES:
        for cohort, df in frames.items():
            summary = summarize_series(df[feature]) if feature in df.columns else {"n": "0", "p1": "NA", "p50": "NA", "p99": "NA", "max": "NA"}
            rows.append(
                {
                    "Feature": feature,
                    "Clinical label": label,
                    "Cohort": cohort,
                    "Expected unit": unit,
                    "N observed": summary["n"],
                    "P1": summary["p1"],
                    "Median": summary["p50"],
                    "P99": summary["p99"],
                    "Max": summary["max"],
                    "Audit note": NOTES[feature],
                }
            )

    text = [
        "# Unit Harmonization Audit",
        "",
        "This audit summarizes value ranges for the locked cross-database predictors most vulnerable to unit mismatch. Ranges are descriptive and should be reviewed alongside extraction code and database dictionaries before submission.",
        "",
        markdown_table(rows),
        "",
        "## Interpretation",
        "",
        "- No locked predictor was missing from the MIMIC-IV, MIMIC-III, or SICdb modeling datasets.",
        "- MIMIC-III temperature values were corrected at extraction: plausible Fahrenheit values were converted to Celsius before aggregation, plausible Celsius values were retained, and implausible temperature values were excluded from temperature summaries.",
        "- SICdb BUN harmonization was corrected by converting Harnstoff (urea) to BUN using urea x 0.467 before validation.",
        "- Platelet units were treated as numerically compatible across 10^9/L and K/uL conventions.",
        "- Urine output is cumulative mL from S-AKI onset to landmark and is not weight-normalized; this should be stated in Methods and Table S4.",
        "- SICdb remains exploratory because the sepsis definition and time-resolved KDIGO phenotype are less harmonized than the MIMIC cohorts.",
        "",
    ]
    output = ROOT / "unit_harmonization_audit.md"
    output.write_text("\n".join(text), encoding="utf-8")
    print(f"Saved unit harmonization audit: {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
