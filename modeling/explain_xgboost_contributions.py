#!/usr/bin/env python
"""TreeSHAP-style contribution summaries for fitted XGBoost pipelines.

The script uses XGBoost's built-in `pred_contribs=True`, so it does not require
the external `shap` or `matplotlib` packages.
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explain a fitted XGBoost prediction pipeline.")
    parser.add_argument("--input", required=True, help="Modeling dataset used for development.")
    parser.add_argument("--model", required=True, help="Pickled sklearn Pipeline containing XGBClassifier.")
    parser.add_argument("--run-config", required=True, help="run_config.json from training.")
    parser.add_argument("--predictors", required=True, help="predictor_columns.json from training.")
    parser.add_argument("--output-dir", required=True, help="Directory for explanation outputs.")
    parser.add_argument("--target", default="aki_progression_48h", help="Binary outcome column.")
    parser.add_argument("--group-col", default="stay_id", help="Group identifier column.")
    parser.add_argument("--sample", type=int, default=0, help="Optional max rows for explanation; 0 means all test rows.")
    parser.add_argument("--top-n", type=int, default=20, help="Number of top features for focused outputs.")
    return parser.parse_args()


def read_dataset(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported dataset type: {path.suffix}")


def get_feature_names(pipe, predictors: list[str]) -> list[str]:
    preprocessor = pipe.named_steps["preprocess"]
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        return predictors


def clean_feature_name(name: str) -> str:
    for prefix in ("numeric__", "categorical__"):
        if name.startswith(prefix):
            return name[len(prefix) :]
    return name


def get_test_set(df: pd.DataFrame, config: dict, group_col: str) -> pd.DataFrame:
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=float(config.get("test_size", 0.2)),
        random_state=int(config.get("random_state", 20260620)),
    )
    _, test_idx = next(splitter.split(df, groups=df[group_col]))
    return df.iloc[test_idx].copy()


def contribution_matrix(pipe, x: pd.DataFrame, feature_names: list[str]) -> np.ndarray:
    import xgboost as xgb

    transformed = pipe.named_steps["preprocess"].transform(x)
    booster = pipe.named_steps["model"].get_booster()
    dmat = xgb.DMatrix(transformed, feature_names=feature_names)
    return booster.predict(dmat, pred_contribs=True, validate_features=False)


def summarize_contributions(contrib: np.ndarray, feature_names: list[str]) -> pd.DataFrame:
    values = contrib[:, :-1]
    abs_values = np.abs(values)
    total = float(abs_values.sum())
    out = pd.DataFrame(
        {
            "feature": feature_names,
            "clean_feature": [clean_feature_name(f) for f in feature_names],
            "mean_abs_contribution": abs_values.mean(axis=0),
            "mean_contribution": values.mean(axis=0),
            "sd_contribution": values.std(axis=0),
            "median_contribution": np.median(values, axis=0),
            "positive_contribution_rate": (values > 0).mean(axis=0),
        }
    )
    out["relative_importance"] = out["mean_abs_contribution"] / out["mean_abs_contribution"].sum()
    out["absolute_contribution_share"] = abs_values.sum(axis=0) / total if total else np.nan
    return out.sort_values("mean_abs_contribution", ascending=False)


def raw_feature_direction(
    eval_df: pd.DataFrame,
    predictors: list[str],
    contribution_summary: pd.DataFrame,
    contrib: np.ndarray,
    feature_names: list[str],
    top_n: int,
) -> pd.DataFrame:
    rows = []
    feature_to_index = {name: idx for idx, name in enumerate(feature_names)}
    for feature in contribution_summary["clean_feature"].head(top_n):
        if feature not in eval_df.columns:
            continue
        if not pd.api.types.is_numeric_dtype(eval_df[feature]):
            continue
        candidates = [f"numeric__{feature}", feature]
        idx = next((feature_to_index[c] for c in candidates if c in feature_to_index), None)
        if idx is None:
            continue
        raw = eval_df[feature].astype(float)
        valid = raw.notna()
        if valid.sum() < 30 or raw[valid].nunique() < 3:
            corr = np.nan
        else:
            corr = float(np.corrcoef(raw[valid], contrib[valid.to_numpy(), idx])[0, 1])
        rows.append(
            {
                "feature": feature,
                "n_nonmissing": int(valid.sum()),
                "raw_median": float(raw.median()) if valid.any() else np.nan,
                "raw_q1": float(raw.quantile(0.25)) if valid.any() else np.nan,
                "raw_q3": float(raw.quantile(0.75)) if valid.any() else np.nan,
                "raw_contribution_correlation": corr,
                "direction_hint": "higher values increase predicted risk"
                if corr > 0.05
                else "higher values decrease predicted risk"
                if corr < -0.05
                else "nonlinear or weak monotonic direction",
            }
        )
    return pd.DataFrame(rows)


def binned_dependence(
    eval_df: pd.DataFrame,
    contribution_summary: pd.DataFrame,
    contrib: np.ndarray,
    feature_names: list[str],
    top_n: int,
) -> pd.DataFrame:
    rows = []
    feature_to_index = {name: idx for idx, name in enumerate(feature_names)}
    for feature in contribution_summary["clean_feature"].head(top_n):
        if feature not in eval_df.columns or not pd.api.types.is_numeric_dtype(eval_df[feature]):
            continue
        candidates = [f"numeric__{feature}", feature]
        idx = next((feature_to_index[c] for c in candidates if c in feature_to_index), None)
        if idx is None:
            continue
        tmp = pd.DataFrame(
            {
                "raw": pd.to_numeric(eval_df[feature], errors="coerce"),
                "contribution": contrib[:, idx],
                "target": eval_df["aki_progression_48h"].astype(int).to_numpy(),
            }
        ).dropna()
        if len(tmp) < 50 or tmp["raw"].nunique() < 5:
            continue
        tmp["bin"] = pd.qcut(tmp["raw"], q=10, duplicates="drop")
        grouped = tmp.groupby("bin", observed=True)
        for bin_id, (_, part) in enumerate(grouped, start=1):
            rows.append(
                {
                    "feature": feature,
                    "bin_id": bin_id,
                    "n": int(len(part)),
                    "raw_min": float(part["raw"].min()),
                    "raw_median": float(part["raw"].median()),
                    "raw_max": float(part["raw"].max()),
                    "mean_contribution": float(part["contribution"].mean()),
                    "event_rate": float(part["target"].mean()),
                }
            )
    return pd.DataFrame(rows)


def individual_explanations(
    eval_df: pd.DataFrame,
    contrib: np.ndarray,
    feature_names: list[str],
    top_n: int,
) -> pd.DataFrame:
    values = contrib[:, :-1]
    base_value = contrib[:, -1]
    logits = values.sum(axis=1) + base_value
    probs = 1.0 / (1.0 + np.exp(-logits))
    selected = pd.DataFrame(
        {
            "row_position": np.arange(len(eval_df)),
            "stay_id": eval_df["stay_id"].to_numpy() if "stay_id" in eval_df.columns else np.arange(len(eval_df)),
            "landmark_hour": eval_df["landmark_hour"].to_numpy() if "landmark_hour" in eval_df.columns else np.nan,
            "target": eval_df["aki_progression_48h"].astype(int).to_numpy(),
            "predicted_risk": probs,
        }
    )
    picks = pd.concat(
        [
            selected.nlargest(3, "predicted_risk").assign(case_type="highest_predicted_risk"),
            selected.nsmallest(3, "predicted_risk").assign(case_type="lowest_predicted_risk"),
        ],
        ignore_index=True,
    )
    rows = []
    for case in picks.itertuples(index=False):
        row_contrib = values[int(case.row_position), :]
        top_idx = np.argsort(np.abs(row_contrib))[::-1][:top_n]
        for rank, idx in enumerate(top_idx, start=1):
            rows.append(
                {
                    "case_type": case.case_type,
                    "stay_id": case.stay_id,
                    "landmark_hour": case.landmark_hour,
                    "target": case.target,
                    "predicted_risk": case.predicted_risk,
                    "rank": rank,
                    "feature": feature_names[idx],
                    "clean_feature": clean_feature_name(feature_names[idx]),
                    "contribution_log_odds": row_contrib[idx],
                }
            )
    return pd.DataFrame(rows)


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = read_dataset(Path(args.input))
    config = json.loads(Path(args.run_config).read_text(encoding="utf-8"))
    predictors = json.loads(Path(args.predictors).read_text(encoding="utf-8"))

    df = df[df[args.target].notna()].copy()
    df[args.target] = df[args.target].astype(int)
    eval_df = get_test_set(df, config, args.group_col)
    if args.sample and len(eval_df) > args.sample:
        eval_df = eval_df.sample(n=args.sample, random_state=int(config.get("random_state", 20260620)))

    with Path(args.model).open("rb") as f:
        pipe = pickle.load(f)

    x_eval = eval_df[predictors]
    feature_names = get_feature_names(pipe, predictors)
    contrib = contribution_matrix(pipe, x_eval, feature_names)

    importance = summarize_contributions(contrib, feature_names)
    importance.to_csv(output_dir / "xgboost_contribution_importance.csv", index=False)

    direction = raw_feature_direction(eval_df, predictors, importance, contrib[:, :-1], feature_names, args.top_n)
    direction.to_csv(output_dir / "xgboost_contribution_direction.csv", index=False)

    dependence = binned_dependence(eval_df, importance, contrib[:, :-1], feature_names, args.top_n)
    dependence.to_csv(output_dir / "xgboost_binned_dependence.csv", index=False)

    cases = individual_explanations(eval_df, contrib, feature_names, min(args.top_n, 10))
    cases.to_csv(output_dir / "xgboost_individual_explanations.csv", index=False)

    metadata = {
        "input": args.input,
        "model": args.model,
        "n_explained_rows": int(len(eval_df)),
        "n_transformed_features": int(len(feature_names)),
        "base_value_mean_log_odds": float(contrib[:, -1].mean()),
        "top_features": importance["clean_feature"].head(args.top_n).tolist(),
        "method": "XGBoost pred_contribs=True, TreeSHAP-style additive feature contributions",
    }
    (output_dir / "xgboost_explanation_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print(importance.head(args.top_n).to_string(index=False), flush=True)
    print(f"Saved explanation outputs to: {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
