#!/usr/bin/env python
"""Convert manuscript citation keys to Vancouver-style numbered references."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REFERENCE_TEXT = {
    "Hoste2015AKIEPI": "Hoste EAJ, Bagshaw SM, Bellomo R, Cely CM, Colman R, Cruz DN, et al. Epidemiology of acute kidney injury in critically ill patients: the multinational AKI-EPI study. Intensive Care Med. 2015;41:1411-1423. doi:10.1007/s00134-015-3934-7.",
    "Kellum2021AKIPrimer": "Kellum JA, Romagnani P, Ashuntantang G, Ronco C, Zarbock A, Anders HJ. Acute kidney injury. Nat Rev Dis Primers. 2021;7:52. doi:10.1038/s41572-021-00284-z.",
    "Bagshaw2007SepticAKI": "Bagshaw SM, Uchino S, Bellomo R, Morimatsu H, Morgera S, Schetz M, et al. Septic acute kidney injury in critically ill patients: clinical characteristics and outcomes. Clin J Am Soc Nephrol. 2007;2:431-439. doi:10.2215/CJN.03681106.",
    "KDIGO2012AKI": "Kidney Disease: Improving Global Outcomes Acute Kidney Injury Work Group. KDIGO Clinical Practice Guideline for Acute Kidney Injury. Kidney Int Suppl. 2012;2:1-138. doi:10.1038/kisup.2012.1.",
    "Flechet2017AKIpredictor": "Flechet M, Guiza F, Schetz M, Wouters PJ, Vanhorebeek I, Derese I, et al. AKIpredictor, an online prognostic calculator for acute kidney injury in adult critically ill patients: development, validation and comparison to serum neutrophil gelatinase-associated lipocalin. Crit Care. 2017;21:39. doi:10.1186/s13054-017-1648-4.",
    "Koyner2018MLAKI": "Koyner JL, Carey KA, Edelson DP, Churpek MM. The development of a machine learning inpatient acute kidney injury prediction model. Crit Care Med. 2018;46:1070-1077. doi:10.1097/CCM.0000000000003123.",
    "Tomasev2019AKI": "Tomasev N, Glorot X, Rae JW, Zielinski M, Askham H, Saraiva A, et al. A clinically applicable approach to continuous prediction of future acute kidney injury. Nature. 2019;572:116-119. doi:10.1038/s41586-019-1390-1.",
    "VanHouwelingen2007Landmarking": "van Houwelingen HC. Dynamic prediction by landmarking in event history analysis. Scand J Stat. 2007;34:70-85. doi:10.1111/j.1467-9469.2006.00529.x.",
    "Putter2017Landmarking": "Putter H, van Houwelingen HC. Dynamic prediction by landmarking as an alternative for multi-state modeling: an application to acute lymphoid leukemia data. Biometrics. 2017;73:563-572. doi:10.1111/biom.12438.",
    "Collins2015TRIPOD": "Collins GS, Reitsma JB, Altman DG, Moons KGM. Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis (TRIPOD): the TRIPOD statement. Ann Intern Med. 2015;162:55-63. doi:10.7326/M14-0697.",
    "Wolff2019PROBAST": "Wolff RF, Moons KGM, Riley RD, Whiting PF, Westwood M, Collins GS, et al. PROBAST: a tool to assess the risk of bias and applicability of prediction model studies. Ann Intern Med. 2019;170:51-58. doi:10.7326/M18-1376.",
    "Collins2024TRIPODAI": "Collins GS, Dhiman P, Andaur Navarro CL, Ma J, Hooft L, Reitsma JB, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ. 2024;385:e078378. doi:10.1136/bmj-2023-078378.",
    "Steyerberg2014Validation": "Steyerberg EW, Vergouwe Y. Towards better clinical prediction models: seven steps for development and an ABCD for validation. Eur Heart J. 2014;35:1925-1931. doi:10.1093/eurheartj/ehu207.",
    "VanCalster2019Calibration": "Van Calster B, McLernon DJ, van Smeden M, Wynants L, Steyerberg EW. Calibration: the Achilles heel of predictive analytics. BMC Med. 2019;17:230. doi:10.1186/s12916-019-1466-7.",
    "Vickers2006DecisionCurve": "Vickers AJ, Elkin EB. Decision curve analysis: a novel method for evaluating prediction models. Med Decis Making. 2006;26:565-574. doi:10.1177/0272989X06295361.",
    "Johnson2023MIMICIV": "Johnson AEW, Bulgarelli L, Shen L, Gayles A, Shammout A, Horng S, et al. MIMIC-IV, a freely accessible electronic health record dataset. Sci Data. 2023;10:1. doi:10.1038/s41597-022-01899-x.",
    "Johnson2016MIMICIII": "Johnson AEW, Pollard TJ, Shen L, Lehman L-WH, Feng M, Ghassemi M, et al. MIMIC-III, a freely accessible critical care database. Sci Data. 2016;3:160035. doi:10.1038/sdata.2016.35.",
    "Pollard2018EICU": "Pollard TJ, Johnson AEW, Raffa JD, Celi LA, Mark RG, Badawi O. The eICU Collaborative Research Database, a freely available multi-center database for critical care research. Sci Data. 2018;5:180178. doi:10.1038/sdata.2018.178.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Vancouver-numbered manuscript draft.")
    parser.add_argument("--input", required=True, help="Input manuscript Markdown with bracketed citation keys.")
    parser.add_argument("--output", required=True, help="Output manuscript Markdown.")
    parser.add_argument("--reference-output", required=True, help="Standalone numbered reference list Markdown.")
    return parser.parse_args()


def split_keys(citation: str) -> list[str]:
    return [part.strip() for part in re.split(r";|,", citation) if part.strip()]


def main() -> int:
    args = parse_args()
    text = Path(args.input).read_text(encoding="utf-8")
    assigned: dict[str, int] = {}

    def replace(match: re.Match[str]) -> str:
        body = match.group(1)
        keys = split_keys(body)
        if not keys:
            return match.group(0)
        if not all(key in REFERENCE_TEXT for key in keys):
            return match.group(0)
        numbers = []
        for key in keys:
            if key not in assigned:
                assigned[key] = len(assigned) + 1
            numbers.append(str(assigned[key]))
        return "[" + ",".join(numbers) + "]"

    converted = re.sub(r"\[([A-Za-z0-9_;,\s-]+)\]", replace, text)

    references = ["## References", ""]
    for key, number in sorted(assigned.items(), key=lambda item: item[1]):
        references.append(f"{number}. {REFERENCE_TEXT[key]}")

    reference_text = "\n".join(references) + "\n"
    converted = re.sub(
        r"## References\s*\n\s*Reference metadata are curated.*?(?=\n## |\Z)",
        reference_text.rstrip(),
        converted,
        flags=re.S,
    )
    if "## References" not in converted:
        converted = converted.rstrip() + "\n\n" + reference_text

    Path(args.output).write_text(converted, encoding="utf-8")
    Path(args.reference_output).write_text(reference_text, encoding="utf-8")
    print(f"Saved Vancouver manuscript: {args.output}", flush=True)
    print(f"Saved reference list: {args.reference_output}", flush=True)
    print(f"References used: {len(assigned)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
