#!/usr/bin/env python
"""Create descriptive recalibration and landmark-stratified performance tables."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


TARGET = "aki_progression_48h"
GROUP = "stay_id"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Make recalibration analysis outputs.")
    parser.add_argument("--mimic-iv-predictions", required=True)
    parser.add_argument("--mimic-iii-predictions", required=True)
    parser.add_argument("--sicdb-predictions", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def read_prediction(path: str, cohort: str, model_label: str = "xgboost_crossdb") -> pd.DataFrame:
    df = pd.read_csv(path)
    if "model" in df.columns:
        df = df[df["model"] == "xgboost"].copy()
    required = {GROUP, TARGET, "landmark_hour", "y_prob"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    out = df[[GROUP, TARGET, "landmark_hour", "y_prob"]].copy()
    out["cohort"] = cohort
    out["model"] = model_label
    out[TARGET] = out[TARGET].astype(int)
    out["y_prob"] = out["y_prob"].astype(float)
    return out


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1.0 - 1e-6)
    return np.log(p / (1.0 - p))


def inv_logit(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def calibration_model(y_true: np.ndarray, y_prob: np.ndarray) -> tuple[float, float]:
    x = logit(y_prob).reshape(-1, 1)
    model = LogisticRegression(C=np.inf, solver="lbfgs", max_iter=1000)
    try:
        model.fit(x, y_true)
    except Exception:
        return math.nan, math.nan
    return float(model.intercept_[0]), float(model.coef_[0][0])


def intercept_only_recalibration(y_true: np.ndarray, y_prob: np.ndarray) -> tuple[float, np.ndarray]:
    lp = logit(y_prob)
    lo, hi = -10.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        pred = inv_logit(lp + mid)
        if pred.mean() < y_true.mean():
            lo = mid
        else:
            hi = mid
    intercept = (lo + hi) / 2.0
    return float(intercept), inv_logit(lp + intercept)


def logistic_recalibration(y_true: np.ndarray, y_prob: np.ndarray) -> tuple[float, float, np.ndarray]:
    intercept, slope = calibration_model(y_true, y_prob)
    if math.isnan(intercept) or math.isnan(slope):
        return math.nan, math.nan, np.full_like(y_prob, np.nan, dtype=float)
    return intercept, slope, inv_logit(intercept + slope * logit(y_prob))


def metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    intercept, slope = calibration_model(y_true, y_prob)
    return {
        "auroc": roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) == 2 else math.nan,
        "auprc": average_precision_score(y_true, y_prob) if len(np.unique(y_true)) == 2 else math.nan,
        "brier": brier_score_loss(y_true, y_prob),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
        "mean_predicted_risk": float(np.mean(y_prob)),
        "observed_event_rate": float(np.mean(y_true)),
    }


def summarize_recalibration(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    pred_frames = []
    for cohort, part in df.groupby("cohort", sort=False):
        y = part[TARGET].to_numpy()
        p = part["y_prob"].to_numpy()

        variants: list[tuple[str, np.ndarray, dict[str, float]]] = []
        variants.append(("unrecalibrated", p, {"recalibration_intercept": 0.0, "recalibration_slope": 1.0}))

        intercept_shift, p_intercept = intercept_only_recalibration(y, p)
        variants.append(
            (
                "intercept_only",
                p_intercept,
                {"recalibration_intercept": intercept_shift, "recalibration_slope": 1.0},
            )
        )

        rec_intercept, rec_slope, p_logistic = logistic_recalibration(y, p)
        variants.append(
            (
                "intercept_plus_slope",
                p_logistic,
                {"recalibration_intercept": rec_intercept, "recalibration_slope": rec_slope},
            )
        )

        for variant, prob, params in variants:
            row = {
                "cohort": cohort,
                "variant": variant,
                "n_rows": int(len(part)),
                "n_stays": int(part[GROUP].nunique()),
                "events": int(part[TARGET].sum()),
            }
            row.update(params)
            row.update(metrics(y, prob))
            rows.append(row)

            pred = part[[GROUP, TARGET, "landmark_hour", "cohort", "model"]].copy()
            pred["variant"] = variant
            pred["y_prob"] = prob
            pred_frames.append(pred)

    return pd.DataFrame(rows), pd.concat(pred_frames, ignore_index=True)


def summarize_landmarks(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (cohort, landmark), part in df.groupby(["cohort", "landmark_hour"], sort=True):
        y = part[TARGET].to_numpy()
        p = part["y_prob"].to_numpy()
        row = {
            "cohort": cohort,
            "landmark_hour": int(landmark),
            "n_rows": int(len(part)),
            "n_stays": int(part[GROUP].nunique()),
            "events": int(part[TARGET].sum()),
        }
        row.update(metrics(y, p))
        rows.append(row)
    return pd.DataFrame(rows)


def calibration_bins(df: pd.DataFrame, n_bins: int = 10) -> pd.DataFrame:
    rows = []
    for (cohort, variant), part in df.groupby(["cohort", "variant"], sort=False):
        tmp = part.copy()
        tmp["bin"] = pd.qcut(tmp["y_prob"], q=n_bins, duplicates="drop")
        bins = (
            tmp.groupby("bin", observed=True)
            .agg(
                n=(TARGET, "size"),
                predicted_mean=("y_prob", "mean"),
                observed_rate=(TARGET, "mean"),
                predicted_min=("y_prob", "min"),
                predicted_max=("y_prob", "max"),
            )
            .reset_index(drop=True)
        )
        bins.insert(0, "bin_id", np.arange(1, len(bins) + 1))
        bins.insert(0, "variant", variant)
        bins.insert(0, "cohort", cohort)
        rows.append(bins)
    return pd.concat(rows, ignore_index=True)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    lines = [
        "| " + " | ".join(df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for row in df.to_numpy():
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def format_table(summary: pd.DataFrame) -> pd.DataFrame:
    out = summary.copy()
    for col in [
        "auroc",
        "auprc",
        "brier",
        "calibration_intercept",
        "calibration_slope",
        "mean_predicted_risk",
        "observed_event_rate",
        "recalibration_intercept",
        "recalibration_slope",
    ]:
        out[col] = out[col].map(lambda x: "NA" if pd.isna(x) else f"{x:.3f}")
    return out[
        [
            "cohort",
            "variant",
            "n_rows",
            "n_stays",
            "events",
            "observed_event_rate",
            "mean_predicted_risk",
            "auroc",
            "auprc",
            "brier",
            "calibration_intercept",
            "calibration_slope",
            "recalibration_intercept",
            "recalibration_slope",
        ]
    ]


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = [
        read_prediction(args.mimic_iv_predictions, "MIMIC-IV internal test"),
        read_prediction(args.mimic_iii_predictions, "MIMIC-III external with CRRT"),
        read_prediction(args.sicdb_predictions, "SICdb sensitivity external"),
    ]
    predictions = pd.concat(frames, ignore_index=True)

    recal, recal_predictions = summarize_recalibration(predictions)
    landmark = summarize_landmarks(predictions)
    bins = calibration_bins(recal_predictions)

    predictions.to_csv(out_dir / "input_predictions_combined.csv", index=False)
    recal.to_csv(out_dir / "recalibration_summary.csv", index=False)
    recal_predictions.to_csv(out_dir / "recalibrated_predictions.csv", index=False)
    landmark.to_csv(out_dir / "landmark_performance_summary.csv", index=False)
    bins.to_csv(out_dir / "recalibration_calibration_bins.csv", index=False)

    report = [
        "# Recalibration and Landmark Performance",
        "",
        "Note: intercept-only and intercept-plus-slope recalibration are descriptive apparent recalibration analyses estimated within each evaluation cohort. They should not replace the primary unrecalibrated external validation.",
        "",
        "## Recalibration Summary",
        "",
        dataframe_to_markdown(format_table(recal)),
        "",
        "## Landmark-Specific Unrecalibrated Performance",
        "",
        dataframe_to_markdown(format_table(landmark.assign(variant="unrecalibrated", recalibration_intercept=np.nan, recalibration_slope=np.nan))),
        "",
    ]
    (out_dir / "recalibration_report.md").write_text("\n".join(report), encoding="utf-8")
    (out_dir / "run_config.json").write_text(
        json.dumps(
            {
                "mimic_iv_predictions": args.mimic_iv_predictions,
                "mimic_iii_predictions": args.mimic_iii_predictions,
                "sicdb_predictions": args.sicdb_predictions,
                "note": "Descriptive apparent recalibration only.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(format_table(recal).to_string(index=False), flush=True)
    print(f"Saved recalibration outputs to: {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
