#!/usr/bin/env python
"""Summarize prediction-model performance with clustered bootstrap CIs."""

from __future__ import annotations

import argparse
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


TARGET = "aki_progression_48h"
GROUP = "stay_id"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create manuscript-ready performance summaries.")
    parser.add_argument("--output-dir", required=True, help="Directory for summary CSV/Markdown files.")
    parser.add_argument("--bootstrap", type=int, default=1000, help="Number of clustered bootstrap samples.")
    parser.add_argument("--seed", type=int, default=20260620, help="Random seed.")
    return parser.parse_args()


def read_prediction_file(path: str, cohort: str, model: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(path)
    if model is not None and "model" in df.columns:
        df = df[df["model"] == model].copy()
    if "model" not in df.columns:
        df["model"] = model or "xgboost"
    elif model is not None:
        df["model"] = model
    df["cohort"] = cohort
    required = {GROUP, TARGET, "landmark_hour", "y_prob", "model", "cohort"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    return df[list(required)].copy()


def calibration_intercept_slope(y_true: np.ndarray, y_prob: np.ndarray) -> tuple[float, float]:
    eps = 1e-6
    clipped = np.clip(y_prob, eps, 1.0 - eps)
    logits = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)
    model = LogisticRegression(C=np.inf, solver="lbfgs", max_iter=1000)
    try:
        model.fit(logits, y_true)
        return float(model.intercept_[0]), float(model.coef_[0][0])
    except Exception:
        return math.nan, math.nan


def compute_metric(df: pd.DataFrame, metric_name: str) -> float:
    y_true = df[TARGET].astype(int).to_numpy()
    y_prob = df["y_prob"].astype(float).to_numpy()
    if metric_name == "auroc":
        return roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) == 2 else math.nan
    if metric_name == "auprc":
        return average_precision_score(y_true, y_prob) if len(np.unique(y_true)) == 2 else math.nan
    if metric_name == "brier":
        return brier_score_loss(y_true, y_prob)
    raise ValueError(f"Unsupported bootstrap metric: {metric_name}")


def point_metrics(df: pd.DataFrame) -> dict[str, float]:
    y_true = df[TARGET].astype(int).to_numpy()
    y_prob = df["y_prob"].astype(float).to_numpy()
    intercept, slope = calibration_intercept_slope(y_true, y_prob)
    return {
        "auroc": roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) == 2 else math.nan,
        "auprc": average_precision_score(y_true, y_prob) if len(np.unique(y_true)) == 2 else math.nan,
        "brier": brier_score_loss(y_true, y_prob),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
        "event_rate": float(np.mean(y_true)),
    }


def clustered_bootstrap_ci(
    df: pd.DataFrame,
    metric_name: str,
    n_boot: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    groups = df[GROUP].drop_duplicates().to_numpy()
    if len(groups) < 2:
        return math.nan, math.nan

    values: list[float] = []
    group_to_rows = {group: rows for group, rows in df.groupby(GROUP).indices.items()}
    for _ in range(n_boot):
        sampled_groups = rng.choice(groups, size=len(groups), replace=True)
        sampled_indices = np.concatenate([group_to_rows[g] for g in sampled_groups])
        sample = df.iloc[sampled_indices]
        if sample[TARGET].nunique() < 2:
            continue
        try:
            value = compute_metric(sample, metric_name)
        except Exception:
            continue
        if not math.isnan(value):
            values.append(float(value))

    if len(values) < 50:
        return math.nan, math.nan
    lo, hi = np.percentile(values, [2.5, 97.5])
    return float(lo), float(hi)


def summarize_one(
    df: pd.DataFrame,
    cohort: str,
    model: str,
    landmark: str,
    n_boot: int,
    rng: np.random.Generator,
) -> dict[str, object]:
    metrics = point_metrics(df)
    row: dict[str, object] = {
        "cohort": cohort,
        "model": model,
        "landmark": landmark,
        "n_rows": int(len(df)),
        "n_stays": int(df[GROUP].nunique()),
        "events": int(df[TARGET].sum()),
    }
    row.update(metrics)
    if n_boot > 0:
        for metric in ["auroc", "auprc", "brier"]:
            lo, hi = clustered_bootstrap_ci(df, metric, n_boot, rng)
            row[f"{metric}_ci_low"] = lo
            row[f"{metric}_ci_high"] = hi
    for metric in ["auroc", "auprc", "brier", "calibration_slope"]:
        row.setdefault(f"{metric}_ci_low", math.nan)
        row.setdefault(f"{metric}_ci_high", math.nan)
    return row


def format_ci(value: float, lo: float, hi: float) -> str:
    if math.isnan(value):
        return "NA"
    if math.isnan(lo) or math.isnan(hi):
        return f"{value:.3f}"
    return f"{value:.3f} ({lo:.3f}-{hi:.3f})"


def dataframe_to_markdown(table: pd.DataFrame) -> str:
    headers = [str(c) for c in table.columns]
    rows = [[str(value) for value in row] for row in table.to_numpy()]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    warnings.filterwarnings("ignore", category=FutureWarning)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    root = Path(__file__).resolve().parents[1]
    specs = [
        {
            "cohort": "MIMIC-IV internal test",
            "model": "xgboost_full",
            "path": root / "results" / "mimic_iv_first_run_with_boosting" / "predictions.csv",
            "filter_model": "xgboost",
        },
        {
            "cohort": "MIMIC-IV internal test",
            "model": "xgboost_crossdb",
            "path": root / "results" / "mimic_iv_crossdb_features" / "predictions.csv",
            "filter_model": "xgboost",
        },
        {
            "cohort": "MIMIC-III external KDIGO-only",
            "model": "xgboost_full",
            "path": root / "results" / "mimiciii_external_validation_xgboost" / "predictions_mimiciii.csv",
            "filter_model": "xgboost",
        },
        {
            "cohort": "MIMIC-III external with CRRT",
            "model": "xgboost_full",
            "path": root / "results" / "mimiciii_external_validation_xgboost_with_crrt" / "predictions_mimiciii_with_crrt.csv",
            "filter_model": "xgboost",
        },
        {
            "cohort": "MIMIC-III external with CRRT",
            "model": "xgboost_crossdb",
            "path": root / "results" / "mimiciii_external_validation_xgboost_crossdb_with_crrt" / "predictions_mimiciii_crossdb_with_crrt.csv",
            "filter_model": "xgboost",
        },
        {
            "cohort": "SICdb sensitivity external",
            "model": "xgboost_crossdb",
            "path": root / "results" / "sicdb_external_validation_xgboost_crossdb" / "predictions_sicdb.csv",
            "filter_model": "xgboost",
        },
    ]

    frames = []
    for spec in specs:
        frames.append(
            read_prediction_file(
                str(spec["path"]),
                cohort=str(spec["cohort"]),
                model=str(spec["filter_model"]),
            ).assign(model_label=str(spec["model"]))
        )
    all_predictions = pd.concat(frames, ignore_index=True)

    rows: list[dict[str, object]] = []
    for (cohort, model_label), part in all_predictions.groupby(["cohort", "model_label"], sort=False):
        rows.append(summarize_one(part, cohort, model_label, "overall", args.bootstrap, rng))
        for landmark_hour, landmark_part in part.groupby("landmark_hour", sort=True):
            rows.append(
                summarize_one(
                    landmark_part,
                    cohort,
                    model_label,
                    f"{int(landmark_hour)}h",
                    0,
                    rng,
                )
            )

    summary = pd.DataFrame(rows)
    summary.to_csv(out_dir / "performance_summary_with_ci.csv", index=False)

    overall = summary[summary["landmark"] == "overall"].copy()
    table = pd.DataFrame(
        {
            "Cohort": overall["cohort"],
            "Model": overall["model"],
            "N rows": overall["n_rows"],
            "N stays": overall["n_stays"],
            "Event rate": overall["event_rate"].map(lambda x: f"{x:.1%}"),
            "AUROC (95% CI)": [
                format_ci(r.auroc, r.auroc_ci_low, r.auroc_ci_high) for r in overall.itertuples()
            ],
            "AUPRC (95% CI)": [
                format_ci(r.auprc, r.auprc_ci_low, r.auprc_ci_high) for r in overall.itertuples()
            ],
            "Brier (95% CI)": [
                format_ci(r.brier, r.brier_ci_low, r.brier_ci_high) for r in overall.itertuples()
            ],
            "Calibration slope (95% CI)": [
                format_ci(r.calibration_slope, r.calibration_slope_ci_low, r.calibration_slope_ci_high)
                for r in overall.itertuples()
            ],
        }
    )
    markdown = "# Performance Summary\n\n" + dataframe_to_markdown(table) + "\n"
    (out_dir / "performance_summary_with_ci.md").write_text(markdown, encoding="utf-8")

    print(table.to_string(index=False), flush=True)
    print(f"Saved summaries to: {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
