#!/usr/bin/env python
"""Extract a SICdb external-validation dataset for the S-AKI dynamic model.

This extractor reads the public SICdb CSV.GZ files directly. It intentionally
keeps the phenotype conservative and transparent:

* adult ICU cases with admission-form sepsis marked "Yes";
* S-AKI onset is the first serum creatinine KDIGO stage >= 1 after ICU start;
* landmarks are 24, 48, and 72 hours after S-AKI onset;
* outcome is creatinine-stage progression or CRRT signal in the next 48 hours.

SICdb does not expose the same minute-by-minute KDIGO table as MIMIC in this
workspace, so this should be reported as a sensitivity external validation.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
UREA_TO_BUN = 0.467

SEX_MALE = 735
SEX_FEMALE = 736
SEPSIS_YES = 740
DEATH_DISCHARGE_TYPE = 3130

CREATININE_IDS = {339, 367, 368}
BUN_IDS = {355}
BICARBONATE_IDS = {451, 456, 666, 667}
SODIUM_IDS = {469}  # BGA sodium has documented validity issues in SICdb.
POTASSIUM_IDS = {453, 463, 685}
CHLORIDE_IDS = {450, 683}
WBC_IDS = {301}
HEMOGLOBIN_IDS = {288, 289, 658}
PLATELET_IDS = {314, 315}
HEMATOCRIT_IDS = {183, 217, 682}
LACTATE_IDS = {454, 465, 657}
PH_IDS = {538, 663, 688, 697, 698, 700}

VITAL_IDS = {
    "sbp": {701, 704},
    "dbp": {702, 705},
    "map": {703, 706},
    "heart_rate": {707, 708, 724},
    "temp": {709},
    "spo2": {710},
    "resp_rate": {719, 2274, 2280},
    "urine": {725},
    "vent": {711, 712, 713, 714, 715, 717, 718, 727, 2019, 2020, 2279, 2281, 2282, 2283, 2284, 3035, 3040},
    "crrt": {723, 730, 731, 732, 2022, 3071},
}

VASOPRESSOR_DRUG_IDS = {1502, 1550, 1562, 1593}
VASOPRESSOR_SIGNAL_IDS = {733, 734, 772, 773, 2306, 2307}


@dataclass
class LandmarkAgg:
    row: dict[str, Any]
    labs: dict[str, list[tuple[int, float]]] = field(default_factory=lambda: defaultdict(list))
    vitals: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    urine_values: list[float] = field(default_factory=list)
    mechanical_ventilation: int = 0
    vasopressor: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract SICdb modeling rows for external validation.")
    parser.add_argument("--sicdb-dir", required=True, help="Directory containing SICdb CSV.GZ files.")
    parser.add_argument(
        "--output",
        required=True,
        help="Output modeling CSV.",
    )
    parser.add_argument(
        "--summary-output",
        default="results/sicdb_external_validation_summary.json",
        help="Extraction summary JSON.",
    )
    parser.add_argument("--min-age", type=float, default=18.0)
    parser.add_argument("--min-los-hours", type=float, default=24.0)
    return parser.parse_args()


def to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        out = float(value)
    except ValueError:
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def to_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def gz_dict_reader(path: Path):
    with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as f:
        yield from csv.DictReader(f)


def load_cases(path: Path, min_age: float, min_los_hours: float) -> dict[int, dict[str, Any]]:
    cases: dict[int, dict[str, Any]] = {}
    min_los_seconds = min_los_hours * SECONDS_PER_HOUR
    for row in gz_dict_reader(path):
        case_id = to_int(row.get("CaseID"))
        patient_id = to_int(row.get("PatientID"))
        age = to_float(row.get("AgeOnAdmission"))
        los_seconds = to_float(row.get("TimeOfStay"))
        sepsis = to_int(row.get("AdmissionFormHasSepsis"))
        if case_id is None or patient_id is None or age is None or los_seconds is None:
            continue
        if age < min_age or los_seconds < min_los_seconds or sepsis != SEPSIS_YES:
            continue
        sex_code = to_int(row.get("Sex"))
        gender = "M" if sex_code == SEX_MALE else "F" if sex_code == SEX_FEMALE else None
        discharge_type = to_int(row.get("HospitalDischargeType"))
        cases[case_id] = {
            "subject_id": patient_id,
            "hadm_id": case_id,
            "stay_id": case_id,
            "gender": gender,
            "age": age,
            "race": None,
            "hospital_expire_flag": int(discharge_type == DEATH_DISCHARGE_TYPE),
            "icu_intime": 0,
            "icu_outtime": int(los_seconds),
            "los_icu": los_seconds / SECONDS_PER_DAY,
            "hours_of_crrt": to_float(row.get("HoursOfCRRT")) or 0.0,
        }
    return cases


def kdigo_stage(creatinine: float, baseline: float) -> int:
    if baseline <= 0:
        return 0
    if creatinine >= 4.0 or creatinine >= 3.0 * baseline:
        return 3
    if creatinine >= 2.0 * baseline:
        return 2
    if creatinine >= 1.5 * baseline or creatinine - baseline >= 0.3:
        return 1
    return 0


def load_creatinine_events(path: Path, case_ids: set[int]) -> dict[int, list[tuple[int, float]]]:
    events: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for row in gz_dict_reader(path):
        lab_id = to_int(row.get("LaboratoryID"))
        if lab_id not in CREATININE_IDS:
            continue
        case_id = to_int(row.get("CaseID"))
        if case_id not in case_ids:
            continue
        offset = to_int(row.get("Offset"))
        value = to_float(row.get("LaboratoryValue"))
        if offset is None or value is None or value <= 0 or value > 20:
            continue
        events[case_id].append((offset, value))
    for case_id in list(events):
        events[case_id].sort()
    return events


def build_landmarks(
    cases: dict[int, dict[str, Any]],
    creatinine_events: dict[int, list[tuple[int, float]]],
) -> dict[int, list[LandmarkAgg]]:
    by_case: dict[int, list[LandmarkAgg]] = defaultdict(list)
    for case_id, case in cases.items():
        events = creatinine_events.get(case_id, [])
        if not events:
            continue
        baseline = min(value for _, value in events)
        staged = [(offset, value, kdigo_stage(value, baseline)) for offset, value in events]
        onset_candidates = [offset for offset, _, stage in staged if stage >= 1]
        if not onset_candidates:
            continue
        saki_onset = min(onset_candidates)
        icu_out = int(case["icu_outtime"])
        for landmark_hour in (24, 48, 72):
            landmark_offset = saki_onset + landmark_hour * SECONDS_PER_HOUR
            if landmark_offset > icu_out or landmark_offset + 48 * SECONDS_PER_HOUR > icu_out:
                continue
            current_events = [x for x in staged if x[0] <= landmark_offset]
            future_events = [x for x in staged if landmark_offset < x[0] <= landmark_offset + 48 * SECONDS_PER_HOUR]
            if not current_events:
                continue
            current_kdigo = current_events[-1][2]
            current_or_prior_max = max(x[2] for x in current_events)
            if current_kdigo not in {1, 2}:
                continue
            future_max = max([x[2] for x in future_events], default=current_kdigo)
            outcome = int(
                (current_kdigo == 1 and future_max >= 2)
                or (current_kdigo == 2 and future_max >= 3)
            )
            row = {
                **{k: case[k] for k in [
                    "subject_id",
                    "hadm_id",
                    "stay_id",
                    "gender",
                    "age",
                    "race",
                    "hospital_expire_flag",
                    "icu_intime",
                    "icu_outtime",
                    "los_icu",
                ]},
                "admittime": None,
                "dischtime": None,
                "sepsis_onset_time": 0,
                "saki_onset_time": saki_onset,
                "landmark_time": landmark_offset,
                "landmark_hour": landmark_hour,
                "current_kdigo": current_kdigo,
                "current_or_prior_max_kdigo": current_or_prior_max,
                "prior_rrt": 0,
                "future_rrt": 0,
                "aki_progression_48h": outcome,
                "baseline_creatinine_sicdb": baseline,
            }
            by_case[case_id].append(LandmarkAgg(row=row))
    return by_case


def candidate_cases(landmarks_by_case: dict[int, list[LandmarkAgg]]) -> set[int]:
    return {case_id for case_id, rows in landmarks_by_case.items() if rows}


def add_lab_value(agg: LandmarkAgg, name: str, offset: int, value: float) -> None:
    agg.labs[name].append((offset, value))


def scan_labs(path: Path, landmarks_by_case: dict[int, list[LandmarkAgg]]) -> None:
    keep = candidate_cases(landmarks_by_case)
    lab_id_sets = [
        ("creatinine", CREATININE_IDS),
        ("bun", BUN_IDS),
        ("bicarbonate", BICARBONATE_IDS),
        ("sodium", SODIUM_IDS),
        ("potassium", POTASSIUM_IDS),
        ("chloride", CHLORIDE_IDS),
        ("wbc", WBC_IDS),
        ("hemoglobin", HEMOGLOBIN_IDS),
        ("platelet", PLATELET_IDS),
        ("hematocrit", HEMATOCRIT_IDS),
        ("lactate", LACTATE_IDS),
        ("ph", PH_IDS),
    ]
    wanted = set().union(*(ids for _, ids in lab_id_sets))
    for row in gz_dict_reader(path):
        lab_id = to_int(row.get("LaboratoryID"))
        if lab_id not in wanted:
            continue
        case_id = to_int(row.get("CaseID"))
        if case_id not in keep:
            continue
        offset = to_int(row.get("Offset"))
        value = to_float(row.get("LaboratoryValue"))
        if offset is None or value is None:
            continue
        names = [name for name, ids in lab_id_sets if lab_id in ids]
        for agg in landmarks_by_case[case_id]:
            if agg.row["saki_onset_time"] <= offset <= agg.row["landmark_time"]:
                for name in names:
                    harmonized_value = value * UREA_TO_BUN if name == "bun" else value
                    add_lab_value(agg, name, offset, harmonized_value)


def scan_float_signals(path: Path, landmarks_by_case: dict[int, list[LandmarkAgg]]) -> None:
    keep = candidate_cases(landmarks_by_case)
    wanted = set().union(*VITAL_IDS.values(), VASOPRESSOR_SIGNAL_IDS)
    for row in gz_dict_reader(path):
        data_id = to_int(row.get("DataID"))
        if data_id not in wanted:
            continue
        case_id = to_int(row.get("CaseID"))
        if case_id not in keep:
            continue
        offset = to_int(row.get("Offset"))
        value = to_float(row.get("Val"))
        count = to_float(row.get("cnt")) or 1.0
        if offset is None or value is None:
            continue
        for agg in landmarks_by_case[case_id]:
            if data_id in VITAL_IDS["crrt"] and value > 0:
                if agg.row["saki_onset_time"] <= offset <= agg.row["landmark_time"]:
                    agg.row["prior_rrt"] = 1
                elif agg.row["landmark_time"] < offset <= agg.row["landmark_time"] + 48 * SECONDS_PER_HOUR:
                    agg.row["future_rrt"] = 1
                    agg.row["aki_progression_48h"] = 1
                continue
            if not (agg.row["saki_onset_time"] <= offset <= agg.row["landmark_time"]):
                continue
            if data_id in VITAL_IDS["heart_rate"] and 20 <= value <= 250:
                agg.vitals["heart_rate"].append(value)
            if data_id in VITAL_IDS["sbp"] and 40 <= value <= 260:
                agg.vitals["sbp"].append(value)
            if data_id in VITAL_IDS["dbp"] and 20 <= value <= 180:
                agg.vitals["dbp"].append(value)
            if data_id in VITAL_IDS["map"] and 25 <= value <= 200:
                agg.vitals["map"].append(value)
            if data_id in VITAL_IDS["resp_rate"] and 3 <= value <= 80:
                agg.vitals["resp_rate"].append(value)
            if data_id in VITAL_IDS["temp"] and 25 <= value <= 45:
                agg.vitals["temp"].append(value)
            if data_id in VITAL_IDS["spo2"] and 40 <= value <= 100:
                agg.vitals["spo2"].append(value)
            if data_id in VITAL_IDS["urine"] and value > 0:
                # data_float_h stores hourly aggregates; Val is representative and
                # cnt is the number of raw points in the compressed hour.
                agg.urine_values.append(value)
            if data_id in VITAL_IDS["vent"] and value > 0:
                agg.mechanical_ventilation = 1
            if data_id in VASOPRESSOR_SIGNAL_IDS and value > 0:
                agg.vasopressor = 1


def intervals_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a <= end_b and start_b <= end_a


def scan_medications(path: Path, landmarks_by_case: dict[int, list[LandmarkAgg]]) -> None:
    keep = candidate_cases(landmarks_by_case)
    for row in gz_dict_reader(path):
        drug_id = to_int(row.get("DrugID"))
        if drug_id not in VASOPRESSOR_DRUG_IDS:
            continue
        case_id = to_int(row.get("CaseID"))
        if case_id not in keep:
            continue
        start = to_int(row.get("Offset"))
        end = to_int(row.get("OffsetDrugEnd")) or start
        if start is None:
            continue
        for agg in landmarks_by_case[case_id]:
            if intervals_overlap(start, end or start, agg.row["saki_onset_time"], agg.row["landmark_time"]):
                agg.vasopressor = 1


def last_value(events: list[tuple[int, float]]) -> float | None:
    if not events:
        return None
    return sorted(events, key=lambda x: x[0])[-1][1]


def values(events: list[tuple[int, float]]) -> list[float]:
    return [v for _, v in events]


def mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def finalize_rows(landmarks_by_case: dict[int, list[LandmarkAgg]]) -> pd.DataFrame:
    rows = []
    for aggs in landmarks_by_case.values():
        for agg in aggs:
            row = dict(agg.row)
            for name in ["heart_rate", "sbp", "dbp", "map", "resp_rate", "temp", "spo2"]:
                xs = agg.vitals.get(name, [])
                if name in {"heart_rate", "resp_rate"}:
                    row[f"{name}_mean"] = mean(xs)
                    row[f"{name}_max"] = max(xs) if xs else None
                elif name in {"sbp", "dbp", "map"}:
                    row[f"{name}_mean"] = mean(xs)
                    row[f"{name}_min"] = min(xs) if xs else None
                elif name == "temp":
                    row["temp_mean"] = mean(xs)
                    row["temp_min"] = min(xs) if xs else None
                    row["temp_max"] = max(xs) if xs else None
                elif name == "spo2":
                    row["spo2_mean"] = mean(xs)
                    row["spo2_min"] = min(xs) if xs else None

            row["creatinine_recent"] = last_value(agg.labs.get("creatinine", []))
            row["creatinine_max"] = max(values(agg.labs.get("creatinine", [])), default=None)
            row["bun_recent"] = last_value(agg.labs.get("bun", []))
            row["bun_max"] = max(values(agg.labs.get("bun", [])), default=None)
            row["bicarbonate_min"] = min(values(agg.labs.get("bicarbonate", [])), default=None)
            row["sodium_min"] = min(values(agg.labs.get("sodium", [])), default=None)
            row["sodium_max"] = max(values(agg.labs.get("sodium", [])), default=None)
            row["potassium_min"] = min(values(agg.labs.get("potassium", [])), default=None)
            row["potassium_max"] = max(values(agg.labs.get("potassium", [])), default=None)
            row["chloride_min"] = min(values(agg.labs.get("chloride", [])), default=None)
            row["chloride_max"] = max(values(agg.labs.get("chloride", [])), default=None)
            row["wbc_max"] = max(values(agg.labs.get("wbc", [])), default=None)
            row["hemoglobin_min"] = min(values(agg.labs.get("hemoglobin", [])), default=None)
            row["platelet_min"] = min(values(agg.labs.get("platelet", [])), default=None)
            row["hematocrit_min"] = min(values(agg.labs.get("hematocrit", [])), default=None)
            row["lactate_max"] = max(values(agg.labs.get("lactate", [])), default=None)
            row["ph_min"] = min(values(agg.labs.get("ph", [])), default=None)

            row["urine_output_total"] = sum(agg.urine_values) if agg.urine_values else None
            row["urine_output_count"] = len(agg.urine_values)
            row["sofa_max"] = None
            row["oasis"] = None
            row["sapsii"] = None
            row["mechanical_ventilation"] = agg.mechanical_ventilation
            row["vasopressor"] = agg.vasopressor
            row["creatinine_missing"] = int(row["creatinine_recent"] is None)
            row["bun_missing"] = int(row["bun_recent"] is None)
            row["lactate_missing"] = int(row["lactate_max"] is None)
            rows.append(row)
    df = pd.DataFrame(rows)
    if not df.empty and "prior_rrt" in df.columns:
        df = df[df["prior_rrt"].fillna(0).astype(int) == 0].copy()
    return df


def main() -> int:
    args = parse_args()
    sicdb_dir = Path(args.sicdb_dir)
    output = Path(args.output)
    summary_output = Path(args.summary_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.parent.mkdir(parents=True, exist_ok=True)

    print("Loading SICdb cases...", flush=True)
    cases = load_cases(sicdb_dir / "cases.csv.gz", args.min_age, args.min_los_hours)
    print(f"Eligible adult admission-sepsis cases: {len(cases)}", flush=True)

    print("Scanning creatinine events...", flush=True)
    creatinine_events = load_creatinine_events(sicdb_dir / "laboratory.csv.gz", set(cases))
    landmarks_by_case = build_landmarks(cases, creatinine_events)
    n_landmark_cases = len(candidate_cases(landmarks_by_case))
    n_landmark_rows = sum(len(v) for v in landmarks_by_case.values())
    print(f"Initial landmark rows: {n_landmark_rows} across {n_landmark_cases} cases", flush=True)

    print("Aggregating laboratory predictors...", flush=True)
    scan_labs(sicdb_dir / "laboratory.csv.gz", landmarks_by_case)

    print("Aggregating medication predictors...", flush=True)
    scan_medications(sicdb_dir / "medication.csv.gz", landmarks_by_case)

    print("Aggregating hourly signal predictors...", flush=True)
    scan_float_signals(sicdb_dir / "data_float_h.csv.gz", landmarks_by_case)

    df = finalize_rows(landmarks_by_case)
    df = df.sort_values(["stay_id", "landmark_hour"]).reset_index(drop=True)
    df.to_csv(output, index=False)

    summary = {
        "sicdb_dir": str(sicdb_dir),
        "output": str(output),
        "eligible_adult_admission_sepsis_cases": len(cases),
        "cases_with_landmarks": int(df["stay_id"].nunique()) if not df.empty else 0,
        "rows": int(len(df)),
        "event_rate": float(df["aki_progression_48h"].mean()) if not df.empty else None,
        "landmark_distribution": {str(k): int(v) for k, v in df["landmark_hour"].value_counts().sort_index().items()} if not df.empty else {},
            "notes": [
            "S-AKI onset reconstructed from serum creatinine KDIGO using minimum observed creatinine as baseline.",
            "AdmissionFormHasSepsis=Yes used as the sepsis criterion.",
            "SICdb Harnstoff (urea, mg/dL) was converted to BUN as urea x 0.467.",
            "SICdb validation should be reported as sensitivity/exploratory because KDIGO timing is reconstructed.",
        ],
    }
    summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
