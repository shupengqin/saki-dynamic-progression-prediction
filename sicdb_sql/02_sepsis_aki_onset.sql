-- Sepsis and AKI onset skeleton for SICdb.
-- Times are offsets in seconds from ICU admission.

DROP TABLE IF EXISTS saki_sicdb.reference_long;
CREATE TABLE saki_sicdb.reference_long AS
SELECT
    r.DrugID,
    LOWER(COALESCE(r.Name, '')) AS item_name,
    LOWER(COALESCE(r.Unit, '')) AS unit,
    LOWER(COALESCE(r.LOINC, '')) AS loinc
FROM sicdb.d_references r;

DROP TABLE IF EXISTS saki_sicdb.antibiotic_events;
CREATE TABLE saki_sicdb.antibiotic_events AS
SELECT
    m.CaseID AS stay_id,
    m.Offset AS event_offset,
    1 AS antibiotic
FROM sicdb.medication m
INNER JOIN saki_sicdb.reference_long r
    ON m.DrugID = r.DrugID
WHERE r.item_name SIMILAR TO
      '%(cef|vanco|piperacillin|tazobactam|meropenem|imipenem|levofloxacin|ciprofloxacin|azithromycin|metronidazole|linezolid|daptomycin|gentamicin|tobramycin|amikacin)%';

-- If a microbiology/culture table is available locally, replace this table.
-- This fallback treats antibiotic start as suspected infection onset.
DROP TABLE IF EXISTS saki_sicdb.suspected_infection;
CREATE TABLE saki_sicdb.suspected_infection AS
SELECT
    stay_id,
    MIN(event_offset) AS sepsis_onset_offset
FROM saki_sicdb.antibiotic_events
GROUP BY stay_id;

DROP TABLE IF EXISTS saki_sicdb.creatinine_events;
CREATE TABLE saki_sicdb.creatinine_events AS
SELECT
    l.CaseID AS stay_id,
    l.Offset AS chart_offset,
    CAST(l.Value AS DOUBLE PRECISION) AS creatinine,
    r.unit
FROM sicdb.laboratory l
INNER JOIN saki_sicdb.reference_long r
    ON l.DrugID = r.DrugID
WHERE (
        r.item_name SIMILAR TO '%(creatinine|kreatinin)%'
        OR r.loinc IN ('2160-0', '38483-4')
      )
  AND l.Value IS NOT NULL
  AND CAST(l.Value AS DOUBLE PRECISION) > 0;

DROP TABLE IF EXISTS saki_sicdb.baseline_creatinine;
CREATE TABLE saki_sicdb.baseline_creatinine AS
SELECT
    stay_id,
    MIN(creatinine) AS baseline_creatinine
FROM saki_sicdb.creatinine_events
WHERE chart_offset <= 86400
GROUP BY stay_id;

-- Preferred path: use SICdb KDIGO_AKI_168 if available.
-- If unavailable, this creatinine-only KDIGO approximation is used.
DROP TABLE IF EXISTS saki_sicdb.kdigo_creatinine;
CREATE TABLE saki_sicdb.kdigo_creatinine AS
SELECT
    c.stay_id,
    c.chart_offset,
    c.creatinine,
    b.baseline_creatinine,
    CASE
        WHEN c.creatinine >= 4.0 OR c.creatinine >= 3.0 * b.baseline_creatinine THEN 3
        WHEN c.creatinine >= 2.0 * b.baseline_creatinine THEN 2
        WHEN c.creatinine >= 1.5 * b.baseline_creatinine THEN 1
        ELSE 0
    END AS aki_stage_creat
FROM saki_sicdb.creatinine_events c
INNER JOIN saki_sicdb.baseline_creatinine b
    ON c.stay_id = b.stay_id;

DROP TABLE IF EXISTS saki_sicdb.rrt_events;
CREATE TABLE saki_sicdb.rrt_events AS
SELECT
    m.CaseID AS stay_id,
    m.Offset AS chart_offset,
    1 AS rrt
FROM sicdb.medication m
INNER JOIN saki_sicdb.reference_long r
    ON m.DrugID = r.DrugID
WHERE r.item_name SIMILAR TO
      '%(dialysis|renal replacement|crrt|cvvh|cvvhd|cvvhdf|hemodialysis|haemodialysis|hdf)%';

DROP TABLE IF EXISTS saki_sicdb.kdigo_timeline;
CREATE TABLE saki_sicdb.kdigo_timeline AS
SELECT
    k.stay_id,
    k.chart_offset,
    GREATEST(k.aki_stage_creat, CASE WHEN r.rrt = 1 THEN 3 ELSE 0 END) AS aki_stage,
    k.aki_stage_creat
FROM saki_sicdb.kdigo_creatinine k
LEFT JOIN saki_sicdb.rrt_events r
    ON k.stay_id = r.stay_id
   AND r.chart_offset <= k.chart_offset;

DROP TABLE IF EXISTS saki_sicdb.sepsis_icu;
CREATE TABLE saki_sicdb.sepsis_icu AS
SELECT
    b.*,
    si.sepsis_onset_offset
FROM saki_sicdb.base_icu b
INNER JOIN saki_sicdb.suspected_infection si
    ON b.stay_id = si.stay_id;

DROP TABLE IF EXISTS saki_sicdb.saki_onset;
CREATE TABLE saki_sicdb.saki_onset AS
SELECT
    s.*,
    MIN(k.chart_offset) AS saki_onset_offset
FROM saki_sicdb.sepsis_icu s
INNER JOIN saki_sicdb.kdigo_timeline k
    ON s.stay_id = k.stay_id
WHERE k.aki_stage >= 1
  AND k.chart_offset >= s.sepsis_onset_offset
  AND k.chart_offset <= s.icu_outtime
GROUP BY
    s.stay_id, s.subject_id, s.hadm_id, s.gender, s.age,
    s.admissionweight, s.icu_intime, s.icu_outtime, s.los_icu,
    s.unitdischargestatus, s.hospitaldischargestatus,
    s.sepsis_onset_offset;

