#!/usr/bin/env python
"""Externally validate a saved S-AKI dynamic prediction model."""

from __future__ import annotations

import argparse
import json
import math
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="External validation for S-AKI prediction models.")
    parser.add_argument("--input", required=True, help="External validation dataset (.csv or .parquet).")
    parser.add_argument("--model", required=True, help="Saved model pickle from train_dynamic_model.py.")
    parser.add_argument("--predictors", required=True, help="predictor_columns.json from training run.")
    parser.add_argument("--output-dir", required=True, help="Directory for validation outputs.")
    parser.add_argument("--cohort-name", default="external", help="Name of external validation cohort.")
    parser.add_argument("--target", default="aki_progression_48h", help="Binary target column.")
    parser.add_argument("--group-col", default="stay_id", help="Group identifier column.")
    return parser.parse_args()


def read_dataset(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported input file type: {path.suffix}")


def calibration_summary(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    data = pd.DataFrame({"y_true": y_true, "y_prob": y_prob})
    data["bin"] = pd.qcut(data["y_prob"], q=n_bins, duplicates="drop")
    out = (
        data.groupby("bin", observed=True)
        .agg(
            n=("y_true", "size"),
            predicted_mean=("y_prob", "mean"),
            observed_rate=("y_true", "mean"),
            predicted_min=("y_prob", "min"),
            predicted_max=("y_prob", "max"),
        )
        .reset_index(drop=True)
    )
    out.insert(0, "bin_id", np.arange(1, len(out) + 1))
    return out


def decision_curve_summary(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    thresholds: np.ndarray | None = None,
) -> pd.DataFrame:
    if thresholds is None:
        thresholds = np.arange(0.01, 0.80, 0.01)
    prevalence = float(np.mean(y_true))
    rows = []
    n = len(y_true)
    for pt in thresholds:
        predicted_positive = y_prob >= pt
        tp = int(np.sum((predicted_positive == 1) & (y_true == 1)))
        fp = int(np.sum((predicted_positive == 1) & (y_true == 0)))
        net_benefit_model = (tp / n) - (fp / n) * (pt / (1.0 - pt))
        net_benefit_all = prevalence - (1.0 - prevalence) * (pt / (1.0 - pt))
        rows.append(
            {
                "threshold": float(pt),
                "net_benefit_model": float(net_benefit_model),
                "net_benefit_all": float(net_benefit_all),
                "net_benefit_none": 0.0,
            }
        )
    return pd.DataFrame(rows)


def calibration_intercept_slope(y_true: np.ndarray, y_prob: np.ndarray) -> tuple[float, float]:
    eps = 1e-6
    clipped = np.clip(y_prob, eps, 1.0 - eps)
    logits = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)
    model = LogisticRegression(penalty=None, solver="lbfgs", max_iter=1000)
    try:
        model.fit(logits, y_true)
        return float(model.intercept_[0]), float(model.coef_[0][0])
    except Exception:
        return math.nan, math.nan


def evaluate(cohort_name: str, y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, Any]:
    metrics: dict[str, Any] = {"cohort": cohort_name}
    if len(np.unique(y_true)) == 2:
        metrics["auroc"] = roc_auc_score(y_true, y_prob)
        metrics["auprc"] = average_precision_score(y_true, y_prob)
    else:
        metrics["auroc"] = math.nan
        metrics["auprc"] = math.nan
    metrics["brier"] = brier_score_loss(y_true, y_prob)
    intercept, slope = calibration_intercept_slope(y_true, y_prob)
    metrics["calibration_intercept"] = intercept
    metrics["calibration_slope"] = slope
    metrics["n"] = int(len(y_true))
    metrics["n_groups"] = None
    metrics["event_rate"] = float(np.mean(y_true))
    return metrics


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = read_dataset(Path(args.input))
    predictors = json.loads(Path(args.predictors).read_text(encoding="utf-8"))

    if args.target not in df.columns:
        raise ValueError(f"Target column not found: {args.target}")

    missing_predictors = [c for c in predictors if c not in df.columns]
    if missing_predictors:
        raise ValueError(
            "External dataset is missing predictors used in training: "
            + ", ".join(missing_predictors[:30])
            + ("..." if len(missing_predictors) > 30 else "")
        )

    eval_df = df[df[args.target].notna()].copy()
    y_true = eval_df[args.target].astype(int).to_numpy()
    x = eval_df[predictors]

    with Path(args.model).open("rb") as f:
        model = pickle.load(f)

    y_prob = model.predict_proba(x)[:, 1]

    metrics = evaluate(args.cohort_name, y_true, y_prob)
    if args.group_col in eval_df.columns:
        metrics["n_groups"] = int(eval_df[args.group_col].nunique())
    pd.DataFrame([metrics]).to_csv(output_dir / f"metrics_{args.cohort_name}.csv", index=False)

    pred_cols = [c for c in [args.group_col, args.target, "landmark_hour"] if c in eval_df.columns]
    predictions = eval_df[pred_cols].copy()
    predictions["cohort"] = args.cohort_name
    predictions["y_prob"] = y_prob
    predictions.to_csv(output_dir / f"predictions_{args.cohort_name}.csv", index=False)

    cal = calibration_summary(y_true, y_prob)
    cal.insert(0, "cohort", args.cohort_name)
    cal.to_csv(output_dir / f"calibration_bins_{args.cohort_name}.csv", index=False)

    dca = decision_curve_summary(y_true, y_prob)
    dca.insert(0, "cohort", args.cohort_name)
    dca.to_csv(output_dir / f"decision_curve_{args.cohort_name}.csv", index=False)

    missingness = (
        eval_df[predictors]
        .isna()
        .mean()
        .reset_index()
        .rename(columns={"index": "feature", 0: "missing_rate"})
        .sort_values("missing_rate", ascending=False)
    )
    missingness.to_csv(output_dir / f"missingness_{args.cohort_name}.csv", index=False)

    config = {
        "input": args.input,
        "model": args.model,
        "predictors": args.predictors,
        "target": args.target,
        "cohort_name": args.cohort_name,
        "n_rows": int(len(eval_df)),
        "n_predictors": len(predictors),
    }
    (output_dir / f"run_config_{args.cohort_name}.json").write_text(
        json.dumps(config, indent=2),
        encoding="utf-8",
    )

    print(pd.DataFrame([metrics]).to_string(index=False), flush=True)
    print(f"Saved outputs to: {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
