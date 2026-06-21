#!/usr/bin/env python
"""Create manuscript-ready descriptive tables for S-AKI prediction study."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate manuscript descriptive tables.")
    parser.add_argument("--mimic-iv", required=True, help="MIMIC-IV modeling dataset CSV.")
    parser.add_argument("--mimic-iii", required=True, help="MIMIC-III with-CRRT modeling dataset CSV.")
    parser.add_argument("--sicdb", default=None, help="Optional SICdb sensitivity validation dataset CSV.")
    parser.add_argument("--performance-summary", required=True, help="Performance summary CSV.")
    parser.add_argument("--clinical-utility", default=None, help="Optional Table 4 clinical utility CSV.")
    parser.add_argument("--recalibration-summary", default=None, help="Optional recalibration summary CSV.")
    parser.add_argument("--landmark-performance", default=None, help="Optional landmark performance summary CSV.")
    parser.add_argument("--predictor-definitions", default=None, help="Optional supplementary predictor-definition CSV.")
    parser.add_argument("--candidate-model-comparison", default=None, help="Optional candidate model comparison CSV.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    return parser.parse_args()


def read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def first_landmark(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(["stay_id", "landmark_hour"]).drop_duplicates("stay_id", keep="first")


def median_iqr(series: pd.Series, digits: int = 1) -> str:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return "NA"
    q1, med, q3 = s.quantile([0.25, 0.5, 0.75])
    return f"{med:.{digits}f} ({q1:.{digits}f}-{q3:.{digits}f})"


def n_pct(mask: pd.Series, denom: int) -> str:
    n = int(mask.fillna(False).sum())
    pct = 100 * n / denom if denom else np.nan
    return f"{n} ({pct:.1f}%)"


def binary_rate(df: pd.DataFrame, col: str, value=1) -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    return df[col] == value


def male_mask(df: pd.DataFrame) -> pd.Series:
    g = df["gender"].astype(str).str.upper()
    return g.isin(["M", "MALE"])


def standardized_mean_diff(x: pd.Series, y: pd.Series) -> float:
    x = pd.to_numeric(x, errors="coerce").dropna()
    y = pd.to_numeric(y, errors="coerce").dropna()
    if len(x) == 0 or len(y) == 0:
        return np.nan
    pooled = np.sqrt((x.var(ddof=1) + y.var(ddof=1)) / 2)
    if not pooled or np.isnan(pooled):
        return np.nan
    return float((x.mean() - y.mean()) / pooled)


def standardized_binary_diff(x_mask: pd.Series, y_mask: pd.Series) -> float:
    px = float(x_mask.mean())
    py = float(y_mask.mean())
    pooled = np.sqrt((px * (1 - px) + py * (1 - py)) / 2)
    if not pooled or np.isnan(pooled):
        return np.nan
    return float((px - py) / pooled)


def make_baseline_table(m4: pd.DataFrame, m3: pd.DataFrame, sicdb: pd.DataFrame | None = None) -> pd.DataFrame:
    m4b = first_landmark(m4)
    m3b = first_landmark(m3)
    sb = first_landmark(sicdb) if sicdb is not None else None
    rows = []

    def add(
        variable: str,
        m4_value: str,
        m3_value: str,
        smd_m3: float | None,
        sicdb_value: str | None = None,
        smd_sicdb: float | None = None,
    ) -> None:
        row = {
            "Variable": variable,
            "MIMIC-IV": m4_value,
            "MIMIC-III": m3_value,
            "SMD: MIMIC-III vs MIMIC-IV": "" if smd_m3 is None or np.isnan(smd_m3) else f"{smd_m3:.3f}",
        }
        if sb is not None:
            row["SICdb"] = sicdb_value or "NA"
            row["SMD: SICdb vs MIMIC-IV"] = "" if smd_sicdb is None or np.isnan(smd_sicdb) else f"{smd_sicdb:.3f}"
        rows.append(row)

    def smd_num(col: str) -> float | None:
        return standardized_mean_diff(m4b[col], sb[col]) if sb is not None and col in sb else None

    def smd_bin(col: str, value=1) -> float | None:
        return (
            standardized_binary_diff(binary_rate(m4b, col, value), binary_rate(sb, col, value))
            if sb is not None and col in sb
            else None
        )

    def sic_median(col: str, digits: int = 1) -> str | None:
        return median_iqr(sb[col], digits) if sb is not None and col in sb else None

    def sic_binary(col: str, value=1) -> str | None:
        return n_pct(binary_rate(sb, col, value), len(sb)) if sb is not None and col in sb else None

    add("Number of ICU stays", f"{m4b['stay_id'].nunique():,}", f"{m3b['stay_id'].nunique():,}", None, f"{sb['stay_id'].nunique():,}" if sb is not None else None, None)
    add("Landmark rows", f"{len(m4):,}", f"{len(m3):,}", None, f"{len(sicdb):,}" if sicdb is not None else None, None)
    add("Age, median (IQR), years", median_iqr(m4b["age"]), median_iqr(m3b["age"]), standardized_mean_diff(m4b["age"], m3b["age"]), sic_median("age"), smd_num("age"))
    add("Male sex, n (%)", n_pct(male_mask(m4b), len(m4b)), n_pct(male_mask(m3b), len(m3b)), standardized_binary_diff(male_mask(m4b), male_mask(m3b)), n_pct(male_mask(sb), len(sb)) if sb is not None else None, standardized_binary_diff(male_mask(m4b), male_mask(sb)) if sb is not None else None)
    add("Initial KDIGO stage 1, n (%)", n_pct(binary_rate(m4b, "current_kdigo", 1), len(m4b)), n_pct(binary_rate(m3b, "current_kdigo", 1), len(m3b)), standardized_binary_diff(binary_rate(m4b, "current_kdigo", 1), binary_rate(m3b, "current_kdigo", 1)), sic_binary("current_kdigo", 1), smd_bin("current_kdigo", 1))
    add("Initial KDIGO stage 2, n (%)", n_pct(binary_rate(m4b, "current_kdigo", 2), len(m4b)), n_pct(binary_rate(m3b, "current_kdigo", 2), len(m3b)), standardized_binary_diff(binary_rate(m4b, "current_kdigo", 2), binary_rate(m3b, "current_kdigo", 2)), sic_binary("current_kdigo", 2), smd_bin("current_kdigo", 2))
    add("SOFA score, median (IQR)", median_iqr(m4b["sofa_max"]), median_iqr(m3b["sofa_max"]), standardized_mean_diff(m4b["sofa_max"], m3b["sofa_max"]), sic_median("sofa_max"), smd_num("sofa_max"))
    add("OASIS score, median (IQR)", median_iqr(m4b["oasis"]), median_iqr(m3b["oasis"]), standardized_mean_diff(m4b["oasis"], m3b["oasis"]), sic_median("oasis"), smd_num("oasis"))
    add("SAPS II score, median (IQR)", median_iqr(m4b["sapsii"]), median_iqr(m3b["sapsii"]), standardized_mean_diff(m4b["sapsii"], m3b["sapsii"]), sic_median("sapsii"), smd_num("sapsii"))
    add("Creatinine, median (IQR), mg/dL", median_iqr(m4b["creatinine_recent"]), median_iqr(m3b["creatinine_recent"]), standardized_mean_diff(m4b["creatinine_recent"], m3b["creatinine_recent"]), sic_median("creatinine_recent"), smd_num("creatinine_recent"))
    add("BUN, median (IQR), mg/dL", median_iqr(m4b["bun_recent"]), median_iqr(m3b["bun_recent"]), standardized_mean_diff(m4b["bun_recent"], m3b["bun_recent"]), sic_median("bun_recent"), smd_num("bun_recent"))
    add("Lactate, median (IQR), mmol/L", median_iqr(m4b["lactate_max"]), median_iqr(m3b["lactate_max"]), standardized_mean_diff(m4b["lactate_max"], m3b["lactate_max"]), sic_median("lactate_max"), smd_num("lactate_max"))
    add("Platelet count, median (IQR)", median_iqr(m4b["platelet_min"]), median_iqr(m3b["platelet_min"]), standardized_mean_diff(m4b["platelet_min"], m3b["platelet_min"]), sic_median("platelet_min"), smd_num("platelet_min"))
    add("MAP, median (IQR), mmHg", median_iqr(m4b["map_mean"]), median_iqr(m3b["map_mean"]), standardized_mean_diff(m4b["map_mean"], m3b["map_mean"]), sic_median("map_mean"), smd_num("map_mean"))
    add("Urine output, median (IQR), mL", median_iqr(m4b["urine_output_total"], 0), median_iqr(m3b["urine_output_total"], 0), standardized_mean_diff(m4b["urine_output_total"], m3b["urine_output_total"]), sic_median("urine_output_total", 0), smd_num("urine_output_total"))
    add("Vasopressor use, n (%)", n_pct(binary_rate(m4b, "vasopressor", 1), len(m4b)), n_pct(binary_rate(m3b, "vasopressor", 1), len(m3b)), standardized_binary_diff(binary_rate(m4b, "vasopressor", 1), binary_rate(m3b, "vasopressor", 1)), sic_binary("vasopressor", 1), smd_bin("vasopressor", 1))
    add("Mechanical ventilation, n (%)", n_pct(binary_rate(m4b, "mechanical_ventilation", 1), len(m4b)), n_pct(binary_rate(m3b, "mechanical_ventilation", 1), len(m3b)), standardized_binary_diff(binary_rate(m4b, "mechanical_ventilation", 1), binary_rate(m3b, "mechanical_ventilation", 1)), sic_binary("mechanical_ventilation", 1), smd_bin("mechanical_ventilation", 1))
    add("Hospital mortality, n (%)", n_pct(binary_rate(m4b, "hospital_expire_flag", 1), len(m4b)), n_pct(binary_rate(m3b, "hospital_expire_flag", 1), len(m3b)), standardized_binary_diff(binary_rate(m4b, "hospital_expire_flag", 1), binary_rate(m3b, "hospital_expire_flag", 1)), sic_binary("hospital_expire_flag", 1), smd_bin("hospital_expire_flag", 1))
    return pd.DataFrame(rows)


def make_landmark_table(m4: pd.DataFrame, m3: pd.DataFrame, sicdb: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    cohorts = [("MIMIC-IV", m4), ("MIMIC-III with CRRT", m3)]
    if sicdb is not None:
        cohorts.append(("SICdb sensitivity", sicdb))
    for cohort, df in cohorts:
        for landmark, part in df.groupby("landmark_hour", sort=True):
            events = int(part["aki_progression_48h"].sum())
            rows.append(
                {
                    "Cohort": cohort,
                    "Landmark": f"{int(landmark)} h",
                    "Rows": int(len(part)),
                    "Unique ICU stays": int(part["stay_id"].nunique()),
                    "AKI progression events": events,
                    "Event rate": f"{part['aki_progression_48h'].mean() * 100:.1f}%",
                    "Future CRRT/RRT rate": f"{part['future_rrt'].mean() * 100:.1f}%" if "future_rrt" in part.columns else "Included in outcome",
                }
            )
    return pd.DataFrame(rows)


def make_missingness_table(m4: pd.DataFrame, m3: pd.DataFrame, sicdb: pd.DataFrame | None = None) -> pd.DataFrame:
    features = [
        ("Creatinine recent", "creatinine_recent"),
        ("BUN recent", "bun_recent"),
        ("Lactate maximum", "lactate_max"),
        ("Platelet minimum", "platelet_min"),
        ("MAP mean", "map_mean"),
        ("Urine output total", "urine_output_total"),
        ("SOFA score", "sofa_max"),
        ("Systolic BP mean", "sbp_mean"),
        ("SpO2 minimum", "spo2_min"),
        ("pH minimum", "ph_min"),
    ]
    rows = []
    for label, col in features:
        row = {
            "Feature": label,
            "MIMIC-IV missing %": f"{m4[col].isna().mean() * 100:.1f}%" if col in m4 else "NA",
            "MIMIC-III missing %": f"{m3[col].isna().mean() * 100:.1f}%" if col in m3 else "NA",
        }
        if sicdb is not None:
            row["SICdb missing %"] = f"{sicdb[col].isna().mean() * 100:.1f}%" if col in sicdb else "NA"
        rows.append(row)
    return pd.DataFrame(rows)


def make_performance_table(perf: pd.DataFrame) -> pd.DataFrame:
    overall = perf[perf["landmark"] == "overall"].copy()
    rows = []
    for row in overall.itertuples(index=False):
        rows.append(
            {
                "Cohort": row.cohort,
                "Model": row.model,
                "N rows": int(row.n_rows),
                "N stays": int(row.n_stays),
                "Event rate": f"{row.event_rate * 100:.1f}%",
                "AUROC (95% CI)": f"{row.auroc:.3f} ({row.auroc_ci_low:.3f}-{row.auroc_ci_high:.3f})",
                "AUPRC (95% CI)": f"{row.auprc:.3f} ({row.auprc_ci_low:.3f}-{row.auprc_ci_high:.3f})",
                "Brier (95% CI)": f"{row.brier:.3f} ({row.brier_ci_low:.3f}-{row.brier_ci_high:.3f})",
                "Calibration intercept": f"{row.calibration_intercept:.3f}",
                "Calibration slope": f"{row.calibration_slope:.3f}",
            }
        )
    return pd.DataFrame(rows)


def make_recalibration_table(recal: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in recal.itertuples(index=False):
        rows.append(
            {
                "Cohort": row.cohort,
                "Recalibration variant": row.variant,
                "N rows": int(row.n_rows),
                "Observed event rate": f"{row.observed_event_rate * 100:.1f}%",
                "Mean predicted risk": f"{row.mean_predicted_risk * 100:.1f}%",
                "AUROC": f"{row.auroc:.3f}",
                "AUPRC": f"{row.auprc:.3f}",
                "Brier score": f"{row.brier:.3f}",
                "Calibration intercept": f"{row.calibration_intercept:.3f}",
                "Calibration slope": f"{row.calibration_slope:.3f}",
                "Applied intercept": f"{row.recalibration_intercept:.3f}",
                "Applied slope": f"{row.recalibration_slope:.3f}",
            }
        )
    return pd.DataFrame(rows)


def make_landmark_performance_table(landmark: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in landmark.itertuples(index=False):
        rows.append(
            {
                "Cohort": row.cohort,
                "Landmark": f"{int(row.landmark_hour)} h",
                "N rows": int(row.n_rows),
                "Events": int(row.events),
                "Event rate": f"{row.observed_event_rate * 100:.1f}%",
                "Mean predicted risk": f"{row.mean_predicted_risk * 100:.1f}%",
                "AUROC": f"{row.auroc:.3f}",
                "AUPRC": f"{row.auprc:.3f}",
                "Brier score": f"{row.brier:.3f}",
                "Calibration intercept": f"{row.calibration_intercept:.3f}",
                "Calibration slope": f"{row.calibration_slope:.3f}",
            }
        )
    return pd.DataFrame(rows)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    headers = [str(c) for c in df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in df.to_numpy():
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def clean_table_strings(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace({np.nan: "", "nan": "", "NaN": ""})


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    m4 = read_csv(args.mimic_iv)
    m3 = read_csv(args.mimic_iii)
    sicdb = read_csv(args.sicdb) if args.sicdb else None
    perf = read_csv(args.performance_summary)

    tables = {
        "table1_baseline_characteristics": make_baseline_table(m4, m3, sicdb),
        "table2_landmarks_event_rates": make_landmark_table(m4, m3, sicdb),
        "table3_model_performance": make_performance_table(perf),
        "table_s1_predictor_missingness": make_missingness_table(m4, m3, sicdb),
    }
    if args.clinical_utility:
        tables["table4_calibration_clinical_utility"] = read_csv(args.clinical_utility)
    if args.recalibration_summary:
        tables["table_s2_recalibration"] = make_recalibration_table(read_csv(args.recalibration_summary))
    if args.landmark_performance:
        tables["table_s3_landmark_performance"] = make_landmark_performance_table(read_csv(args.landmark_performance))
    if args.predictor_definitions:
        tables["table_s4_predictor_definitions"] = read_csv(args.predictor_definitions)
    if args.candidate_model_comparison:
        tables["table_s5_candidate_model_comparison"] = read_csv(args.candidate_model_comparison)

    md_parts = ["# Manuscript Tables\n"]
    titles = {
        "table1_baseline_characteristics": "Table 1. Baseline Characteristics by Cohort",
        "table2_landmarks_event_rates": "Table 2. Landmark Rows and Outcome Event Rates",
        "table3_model_performance": "Table 3. Model Performance",
        "table_s1_predictor_missingness": "Table S1. Predictor Missingness",
        "table_s2_recalibration": "Table S2. Descriptive Recalibration Analysis",
        "table_s3_landmark_performance": "Table S3. Landmark-Specific Unrecalibrated Performance",
        "table_s4_predictor_definitions": "Table S4. Locked Primary-Model Predictor Definitions",
        "table_s5_candidate_model_comparison": "Table S5. Candidate Model Comparison",
        "table4_calibration_clinical_utility": "Table 4. Calibration and Clinical Utility",
    }
    for name, table in tables.items():
        table = clean_table_strings(table)
        table.to_csv(output_dir / f"{name}.csv", index=False)
        md_parts.append(f"## {titles[name]}\n")
        md_parts.append(dataframe_to_markdown(table))
        md_parts.append("")

    (output_dir / "manuscript_tables.md").write_text("\n".join(md_parts), encoding="utf-8")
    print(f"Saved manuscript tables to: {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
