-- Sepsis and AKI onset skeleton for public.
-- Times are offsets in minutes from ICU admission.

DROP TABLE IF EXISTS saki_eicu.antibiotic_events;
CREATE TABLE saki_eicu.antibiotic_events AS
SELECT
    m.patientunitstayid AS stay_id,
    m.drugstartoffset AS event_offset,
    1 AS antibiotic
FROM public.medication m
WHERE LOWER(COALESCE(m.drugname, '')) SIMILAR TO
      '%(cef|vanco|piperacillin|tazobactam|meropenem|imipenem|levofloxacin|ciprofloxacin|azithromycin|metronidazole|linezolid|daptomycin|gentamicin|tobramycin|amikacin)%';

DROP TABLE IF EXISTS saki_eicu.culture_events;
CREATE TABLE saki_eicu.culture_events AS
SELECT
    ml.patientunitstayid AS stay_id,
    ml.culturetakenoffset AS event_offset,
    1 AS culture
FROM public.microlab ml
WHERE ml.culturetakenoffset IS NOT NULL;

DROP TABLE IF EXISTS saki_eicu.suspected_infection;
CREATE TABLE saki_eicu.suspected_infection AS
SELECT
    stay_id,
    MIN(event_offset) AS suspected_infection_offset
FROM saki_eicu.antibiotic_events
GROUP BY stay_id;

DROP TABLE IF EXISTS saki_eicu.creatinine_events;
CREATE TABLE saki_eicu.creatinine_events AS
SELECT
    l.patientunitstayid AS stay_id,
    l.labresultoffset AS chart_offset,
    CAST(l.labresult AS DOUBLE PRECISION) AS creatinine
FROM public.lab l
WHERE LOWER(l.labname) IN ('creatinine')
  AND l.labresult IS NOT NULL
  AND CAST(l.labresult AS DOUBLE PRECISION) > 0;

DROP TABLE IF EXISTS saki_eicu.baseline_creatinine;
CREATE TABLE saki_eicu.baseline_creatinine AS
SELECT
    stay_id,
    MIN(creatinine) AS baseline_creatinine
FROM saki_eicu.creatinine_events
WHERE chart_offset <= 1440
GROUP BY stay_id;

DROP TABLE IF EXISTS saki_eicu.kdigo_creatinine;
CREATE TABLE saki_eicu.kdigo_creatinine AS
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
FROM saki_eicu.creatinine_events c
INNER JOIN saki_eicu.baseline_creatinine b
    ON c.stay_id = b.stay_id;

DROP TABLE IF EXISTS saki_eicu.rrt_events;
CREATE TABLE saki_eicu.rrt_events AS
SELECT
    t.patientunitstayid AS stay_id,
    t.treatmentoffset AS chart_offset,
    1 AS rrt
FROM public.treatment t
WHERE LOWER(COALESCE(t.treatmentstring, '')) SIMILAR TO
      '%(dialysis|renal replacement|crrt|cvvh|cvvhd|cvvhdf|hemodialysis|haemodialysis)%'
UNION
SELECT
    io.patientunitstayid AS stay_id,
    io.intakeoutputoffset AS chart_offset,
    1 AS rrt
FROM public.intakeoutput io
WHERE COALESCE(io.dialysistotal, 0) > 0;

DROP TABLE IF EXISTS saki_eicu.kdigo_timeline;
CREATE TABLE saki_eicu.kdigo_timeline AS
SELECT
    k.stay_id,
    k.chart_offset,
    GREATEST(k.aki_stage_creat, CASE WHEN r.rrt = 1 THEN 3 ELSE 0 END) AS aki_stage,
    k.aki_stage_creat
FROM saki_eicu.kdigo_creatinine k
LEFT JOIN saki_eicu.rrt_events r
    ON k.stay_id = r.stay_id
   AND r.chart_offset <= k.chart_offset;

DROP TABLE IF EXISTS saki_eicu.sepsis_icu;
CREATE TABLE saki_eicu.sepsis_icu AS
SELECT
    b.*,
    si.suspected_infection_offset AS sepsis_onset_offset
FROM saki_eicu.base_icu b
INNER JOIN saki_eicu.suspected_infection si
    ON b.stay_id = si.stay_id;

DROP TABLE IF EXISTS saki_eicu.saki_onset;
CREATE TABLE saki_eicu.saki_onset AS
SELECT
    s.*,
    MIN(k.chart_offset) AS saki_onset_offset
FROM saki_eicu.sepsis_icu s
INNER JOIN saki_eicu.kdigo_timeline k
    ON s.stay_id = k.stay_id
WHERE k.aki_stage >= 1
  AND k.chart_offset >= s.sepsis_onset_offset
  AND k.chart_offset <= s.unitdischargeoffset
GROUP BY
    s.stay_id, s.subject_id, s.hadm_id, s.gender, s.age, s.race,
    s.apacheadmissiondx, s.admissionheight, s.admissionweight,
    s.unitadmitsource, s.unittype, s.unitdischargeoffset,
    s.hospitaldischargeoffset, s.unitdischargestatus,
    s.hospitaldischargestatus, s.sepsis_onset_offset;

