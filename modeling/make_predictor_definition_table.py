#!/usr/bin/env python
"""Create a supplementary predictor-definition table for the locked model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


AGGREGATION_SUFFIXES = [
    ("_mean", "mean"),
    ("_max", "maximum"),
    ("_min", "minimum"),
    ("_recent", "most recent"),
    ("_total", "sum"),
    ("_count", "count"),
    ("_missing", "missingness indicator"),
]

ALIASES = {
    "gender": "sex",
    "current_or_prior_max_kdigo": "max_kdigo_prior",
    "heart_rate": "heart_rate",
    "sbp": "sbp",
    "dbp": "dbp",
    "map": "map",
    "resp_rate": "resp_rate",
    "temp": "temp",
    "spo2": "spo2",
    "bun": "bun_recent",
    "creatinine": "creatinine_recent",
    "lactate": "lactate",
    "bicarbonate": "bicarbonate",
    "sodium": "sodium",
    "potassium": "potassium",
    "chloride": "chloride",
    "wbc": "wbc",
    "hemoglobin": "hemoglobin",
    "platelet": "platelet",
    "hematocrit": "hematocrit",
    "ph": "ph",
}

DIRECT_DEFINITIONS = {
    "gender": {
        "domain": "demographic",
        "definition": "Biological sex encoded for modeling",
        "unit": "binary/category",
        "observation_window": "baseline",
        "aggregation": "value",
    },
    "landmark_hour": {
        "domain": "time",
        "definition": "Prediction landmark after S-AKI onset",
        "unit": "hours",
        "observation_window": "landmark",
        "aggregation": "value",
    },
    "current_or_prior_max_kdigo": {
        "domain": "kidney",
        "definition": "Maximum KDIGO stage observed up to and including the landmark",
        "unit": "stage",
        "observation_window": "S-AKI onset to landmark",
        "aggregation": "maximum",
    },
    "bun_missing": {
        "domain": "missingness",
        "definition": "No BUN measurement before landmark",
        "unit": "binary",
        "observation_window": "S-AKI onset to landmark",
        "aggregation": "indicator",
    },
    "hematocrit_min": {
        "domain": "lab",
        "definition": "Hematocrit",
        "unit": "percent",
        "observation_window": "S-AKI onset to landmark",
        "aggregation": "minimum",
        "notes": "Complete blood count marker.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate locked predictor-definition table.")
    parser.add_argument("--variable-dictionary", required=True, help="variable_dictionary.csv")
    parser.add_argument("--predictors", required=True, help="Locked predictor_columns.json")
    parser.add_argument("--output", required=True, help="Output CSV path")
    return parser.parse_args()


def normalize_feature(feature: str) -> tuple[str, str]:
    for suffix, aggregation in AGGREGATION_SUFFIXES:
        if feature.endswith(suffix):
            return feature[: -len(suffix)], aggregation
    return feature, "value"


def lookup_dictionary_row(dictionary: pd.DataFrame, feature: str) -> tuple[pd.Series | None, str]:
    if feature in DIRECT_DEFINITIONS:
        return None, "direct"

    base, inferred_aggregation = normalize_feature(feature)
    candidates = [feature, base, ALIASES.get(base, base)]
    if base in ["bun", "creatinine"]:
        candidates.extend([f"{base}_recent", f"{base}_max"])

    for candidate in candidates:
        hit = dictionary[dictionary["variable_name"] == candidate]
        if not hit.empty:
            return hit.iloc[0], inferred_aggregation
    return None, inferred_aggregation


def build_table(dictionary: pd.DataFrame, predictors: list[str]) -> pd.DataFrame:
    rows = []
    for feature in predictors:
        direct = DIRECT_DEFINITIONS.get(feature)
        dictionary_row, inferred_aggregation = lookup_dictionary_row(dictionary, feature)
        if direct is not None:
            source = direct
        elif dictionary_row is not None:
            source = dictionary_row.to_dict()
        else:
            source = {
                "domain": "unspecified",
                "definition": "Definition not found in variable dictionary",
                "unit": "NA",
                "observation_window": "NA",
                "aggregation": inferred_aggregation,
                "notes": "Requires manual check",
            }

        aggregation = inferred_aggregation
        if aggregation == "value":
            aggregation = source.get("aggregation", "value")

        raw_notes = source.get("notes", "")
        notes = "" if pd.isna(raw_notes) else str(raw_notes)
        if feature in {"bun_recent", "bun_max"}:
            notes = (notes + " SICdb urea (Harnstoff) converted to BUN using urea x 0.467.").strip()
        if feature.startswith("temp_"):
            notes = (notes + " Temperature harmonized to degrees Celsius.").strip()
        if feature == "gender":
            notes = (notes + " Encoded consistently before modeling.").strip()

        rows.append(
            {
                "Predictor": feature,
                "Domain": source.get("domain", "NA"),
                "Definition": source.get("definition", "NA"),
                "Unit": source.get("unit", "NA"),
                "Observation window": source.get("observation_window", "NA"),
                "Model aggregation": aggregation,
                "Cross-database harmonization notes": notes,
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    args = parse_args()
    dictionary = pd.read_csv(args.variable_dictionary)
    predictors = json.loads(Path(args.predictors).read_text(encoding="utf-8"))
    table = build_table(dictionary, predictors)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    print(f"Saved predictor-definition table: {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
