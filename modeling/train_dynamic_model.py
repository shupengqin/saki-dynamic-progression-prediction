#!/usr/bin/env python
"""Train first-pass dynamic prediction models for S-AKI AKI progression.

This script is intentionally conservative:
- split by patient/ICU stay group, not by row;
- use only columns already present in the modeling table;
- keep gradient boosting dependencies optional;
- export plain CSV outputs for manuscript tables and debugging.
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ID_LIKE_COLUMNS = {
    "subject_id",
    "hadm_id",
    "stay_id",
    "admittime",
    "dischtime",
    "icu_intime",
    "icu_outtime",
    "sepsis_onset_offset",
    "saki_onset_offset",
    "landmark_offset",
    "unitdischargeoffset",
    "hospitaldischargeoffset",
    "saki_onset_time",
    "landmark_time",
    "hospital_expire_flag",
    "unitdischargestatus",
    "hospitaldischargestatus",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train S-AKI dynamic prediction models.")
    parser.add_argument("--input", required=True, help="Input modeling dataset (.csv or .parquet).")
    parser.add_argument("--output-dir", required=True, help="Directory for result outputs.")
    parser.add_argument("--target", default="aki_progression_48h", help="Binary target column.")
    parser.add_argument("--group-col", default="stay_id", help="Column used for grouped train/test split.")
    parser.add_argument("--test-size", type=float, default=0.20, help="Patient/group-level test fraction.")
    parser.add_argument("--random-state", type=int, default=20260620, help="Random seed.")
    parser.add_argument(
        "--include-columns",
        nargs="*",
        default=None,
        help="Optional explicit predictor columns. Defaults to all eligible non-ID columns.",
    )
    parser.add_argument(
        "--exclude-columns",
        nargs="*",
        default=[],
        help="Additional columns to exclude from predictors.",
    )
    return parser.parse_args()


def read_dataset(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported input file type: {path.suffix}")


def infer_predictor_columns(
    df: pd.DataFrame,
    target: str,
    group_col: str,
    include_columns: list[str] | None,
    exclude_columns: list[str],
) -> list[str]:
    if include_columns:
        missing = [c for c in include_columns if c not in df.columns]
        if missing:
            raise ValueError(f"Requested include columns not found: {missing}")
        return include_columns

    excluded = set(ID_LIKE_COLUMNS)
    excluded.add(target)
    excluded.add(group_col)
    excluded.update(exclude_columns)

    predictors = []
    for col in df.columns:
        if col in excluded:
            continue
        if col.endswith("_time") or col.endswith("time"):
            continue
        if col.endswith("_offset") or col.endswith("offset"):
            continue
        predictors.append(col)

    if not predictors:
        raise ValueError("No predictor columns were selected.")
    return predictors


def split_train_test(
    df: pd.DataFrame,
    group_col: str,
    test_size: float,
    random_state: int,
) -> tuple[np.ndarray, np.ndarray]:
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(splitter.split(df, groups=df[group_col]))
    return train_idx, test_idx


def make_preprocessor(x: pd.DataFrame) -> ColumnTransformer:
    numeric_cols = [c for c in x.columns if is_numeric_dtype(x[c]) and not is_bool_dtype(x[c])]
    categorical_cols = [c for c in x.columns if c not in numeric_cols]

    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipe, numeric_cols),
            ("categorical", categorical_pipe, categorical_cols),
        ],
        remainder="drop",
    )


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


def evaluate_model(name: str, y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, Any]:
    metrics: dict[str, Any] = {"model": name}
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
    metrics["event_rate"] = float(np.mean(y_true))
    return metrics


def get_optional_models(random_state: int) -> dict[str, Any]:
    models: dict[str, Any] = {}

    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(
            n_estimators=300,
            max_depth=3,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=random_state,
            n_jobs=-1,
        )
    except Exception:
        pass

    try:
        from lightgbm import LGBMClassifier

        models["lightgbm"] = LGBMClassifier(
            n_estimators=500,
            learning_rate=0.03,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            n_jobs=-1,
        )
    except Exception:
        pass

    return models


def feature_importance_frame(model_name: str, pipe: Pipeline, predictors: list[str]) -> pd.DataFrame | None:
    clf = pipe.named_steps["model"]
    if hasattr(clf, "feature_importances_"):
        importances = clf.feature_importances_
        feature_names = get_feature_names(pipe, predictors)
        if len(feature_names) == len(importances):
            return pd.DataFrame(
                {
                    "model": model_name,
                    "feature": feature_names,
                    "importance": importances,
                }
            ).sort_values("importance", ascending=False)
    if hasattr(clf, "coef_"):
        feature_names = get_feature_names(pipe, predictors)
        coefs = clf.coef_.ravel()
        if len(feature_names) == len(coefs):
            return pd.DataFrame(
                {
                    "model": model_name,
                    "feature": feature_names,
                    "coefficient": coefs,
                    "abs_coefficient": np.abs(coefs),
                }
            ).sort_values("abs_coefficient", ascending=False)
    return None


def get_feature_names(pipe: Pipeline, predictors: list[str]) -> list[str]:
    preprocessor = pipe.named_steps["preprocess"]
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        return predictors


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = read_dataset(input_path)
    if args.target not in df.columns:
        raise ValueError(f"Target column not found: {args.target}")
    if args.group_col not in df.columns:
        raise ValueError(f"Group column not found: {args.group_col}")

    df = df.copy()
    df = df[df[args.target].notna()]
    df[args.target] = df[args.target].astype(int)

    predictors = infer_predictor_columns(
        df=df,
        target=args.target,
        group_col=args.group_col,
        include_columns=args.include_columns,
        exclude_columns=args.exclude_columns,
    )

    train_idx, test_idx = split_train_test(
        df=df,
        group_col=args.group_col,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()

    x_train = train_df[predictors]
    y_train = train_df[args.target].to_numpy()
    x_test = test_df[predictors]
    y_test = test_df[args.target].to_numpy()

    base_models: dict[str, Any] = {
        "logistic_l2": LogisticRegression(
            penalty="l2",
            solver="lbfgs",
            max_iter=2000,
            class_weight="balanced",
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=500,
            min_samples_leaf=20,
            random_state=args.random_state,
            n_jobs=-1,
            class_weight="balanced_subsample",
        ),
    }
    base_models.update(get_optional_models(args.random_state))

    metrics = []
    prediction_frames = []

    for model_name, estimator in base_models.items():
        print(f"Training {model_name}...", flush=True)
        pipe = Pipeline(
            steps=[
                ("preprocess", make_preprocessor(x_train)),
                ("model", estimator),
            ]
        )
        pipe.fit(x_train, y_train)
        y_prob = pipe.predict_proba(x_test)[:, 1]

        metrics.append(evaluate_model(model_name, y_test, y_prob))

        pred = test_df[[args.group_col, args.target]].copy()
        if "landmark_hour" in test_df.columns:
            pred["landmark_hour"] = test_df["landmark_hour"].values
        pred["model"] = model_name
        pred["y_prob"] = y_prob
        prediction_frames.append(pred)

        cal = calibration_summary(y_test, y_prob)
        cal.insert(0, "model", model_name)
        cal.to_csv(output_dir / f"calibration_bins_{model_name}.csv", index=False)

        dca = decision_curve_summary(y_test, y_prob)
        dca.insert(0, "model", model_name)
        dca.to_csv(output_dir / f"decision_curve_{model_name}.csv", index=False)

        fi = feature_importance_frame(model_name, pipe, predictors)
        if fi is not None:
            fi.to_csv(output_dir / f"feature_importance_{model_name}.csv", index=False)

        with (output_dir / f"model_{model_name}.pkl").open("wb") as f:
            pickle.dump(pipe, f)

    metrics_df = pd.DataFrame(metrics).sort_values("auroc", ascending=False)
    metrics_df.to_csv(output_dir / "metrics.csv", index=False)

    predictions = pd.concat(prediction_frames, ignore_index=True)
    predictions.to_csv(output_dir / "predictions.csv", index=False)

    config = {
        "input": str(input_path),
        "target": args.target,
        "group_col": args.group_col,
        "test_size": args.test_size,
        "random_state": args.random_state,
        "n_rows": int(len(df)),
        "n_train_rows": int(len(train_df)),
        "n_test_rows": int(len(test_df)),
        "n_groups": int(df[args.group_col].nunique()),
        "n_train_groups": int(train_df[args.group_col].nunique()),
        "n_test_groups": int(test_df[args.group_col].nunique()),
        "event_rate_overall": float(df[args.target].mean()),
        "event_rate_train": float(train_df[args.target].mean()),
        "event_rate_test": float(test_df[args.target].mean()),
        "predictors": predictors,
        "models": list(base_models.keys()),
        "python": sys.version,
    }
    (output_dir / "run_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (output_dir / "predictor_columns.json").write_text(json.dumps(predictors, indent=2), encoding="utf-8")

    print(metrics_df.to_string(index=False), flush=True)
    print(f"Saved outputs to: {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
