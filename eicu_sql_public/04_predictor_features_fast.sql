-- Faster materialized eICU predictor feature aggregation.

DROP TABLE IF EXISTS saki_eicu.features_vitals;
CREATE TABLE saki_eicu.features_vitals AS
WITH periodic AS (
    SELECT
        l.stay_id,
        l.landmark_offset,
        v.observationoffset,
        v.heartrate,
        v.systemicsystolic AS sbp,
        v.systemicdiastolic AS dbp,
        COALESCE(v.systemicmean, (v.systemicsystolic + 2 * v.systemicdiastolic) / 3.0) AS map_value,
        v.respiration,
        v.temperature,
        v.sao2
    FROM saki_eicu.landmarks l
    LEFT JOIN public.vitalperiodic v
        ON l.stay_id = v.patientunitstayid
       AND v.observationoffset >= l.saki_onset_offset
       AND v.observationoffset <= l.landmark_offset
),
aperiodic AS (
    SELECT
        l.stay_id,
        l.landmark_offset,
        va.observationoffset,
        NULL::DOUBLE PRECISION AS heartrate,
        va.noninvasivesystolic AS sbp,
        va.noninvasivediastolic AS dbp,
        COALESCE(va.noninvasivemean, (va.noninvasivesystolic + 2 * va.noninvasivediastolic) / 3.0) AS map_value,
        NULL::DOUBLE PRECISION AS respiration,
        NULL::DOUBLE PRECISION AS temperature,
        NULL::DOUBLE PRECISION AS sao2
    FROM saki_eicu.landmarks l
    LEFT JOIN public.vitalaperiodic va
        ON l.stay_id = va.patientunitstayid
       AND va.observationoffset >= l.saki_onset_offset
       AND va.observationoffset <= l.landmark_offset
),
vitals AS (
    SELECT * FROM periodic
    UNION ALL
    SELECT * FROM aperiodic
)
SELECT
    stay_id,
    landmark_offset,
    AVG(heartrate) AS heart_rate_mean,
    MAX(heartrate) AS heart_rate_max,
    AVG(sbp) AS sbp_mean,
    MIN(sbp) AS sbp_min,
    AVG(dbp) AS dbp_mean,
    MIN(dbp) AS dbp_min,
    AVG(map_value) AS map_mean,
    MIN(map_value) AS map_min,
    AVG(respiration) AS resp_rate_mean,
    MAX(respiration) AS resp_rate_max,
    AVG(temperature) AS temp_mean,
    MIN(temperature) AS temp_min,
    MAX(temperature) AS temp_max,
    AVG(sao2) AS spo2_mean,
    MIN(sao2) AS spo2_min
FROM vitals
GROUP BY stay_id, landmark_offset;

DROP TABLE IF EXISTS saki_eicu.lab_window;
CREATE TABLE saki_eicu.lab_window AS
SELECT
    l.stay_id,
    l.landmark_offset,
    lab.labresultoffset AS chart_offset,
    LOWER(lab.labname) AS labname,
    CAST(lab.labresult AS DOUBLE PRECISION) AS labresult
FROM saki_eicu.landmarks l
LEFT JOIN public.lab lab
    ON l.stay_id = lab.patientunitstayid
   AND lab.labresultoffset >= l.saki_onset_offset
   AND lab.labresultoffset <= l.landmark_offset
WHERE lab.labresult IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_saki_eicu_lab_window_key
    ON saki_eicu.lab_window (stay_id, landmark_offset, chart_offset);

DROP TABLE IF EXISTS saki_eicu.features_labs;
CREATE TABLE saki_eicu.features_labs AS
SELECT
    stay_id,
    landmark_offset,
    MAX(CASE WHEN labname = 'creatinine' THEN labresult END) AS creatinine_max,
    MAX(CASE WHEN labname IN ('bun', 'blood urea nitrogen') THEN labresult END) AS bun_max,
    MIN(CASE WHEN labname IN ('bicarbonate', 'hco3') THEN labresult END) AS bicarbonate_min,
    MIN(CASE WHEN labname = 'sodium' THEN labresult END) AS sodium_min,
    MAX(CASE WHEN labname = 'sodium' THEN labresult END) AS sodium_max,
    MIN(CASE WHEN labname = 'potassium' THEN labresult END) AS potassium_min,
    MAX(CASE WHEN labname = 'potassium' THEN labresult END) AS potassium_max,
    MIN(CASE WHEN labname = 'chloride' THEN labresult END) AS chloride_min,
    MAX(CASE WHEN labname = 'chloride' THEN labresult END) AS chloride_max,
    MAX(CASE WHEN labname IN ('wbc x 1000', 'wbc') THEN labresult END) AS wbc_max,
    MIN(CASE WHEN labname IN ('hgb', 'hemoglobin') THEN labresult END) AS hemoglobin_min,
    MIN(CASE WHEN labname IN ('platelets x 1000', 'platelets') THEN labresult END) AS platelet_min,
    MIN(CASE WHEN labname IN ('hct', 'hematocrit') THEN labresult END) AS hematocrit_min,
    MAX(CASE WHEN labname = 'lactate' THEN labresult END) AS lactate_max,
    MIN(CASE WHEN labname = 'ph' THEN labresult END) AS ph_min
FROM saki_eicu.lab_window
GROUP BY stay_id, landmark_offset;

DROP TABLE IF EXISTS saki_eicu.features_labs_recent_creat;
CREATE TABLE saki_eicu.features_labs_recent_creat AS
SELECT DISTINCT ON (stay_id, landmark_offset)
    stay_id,
    landmark_offset,
    labresult AS creatinine_recent
FROM saki_eicu.lab_window
WHERE labname = 'creatinine'
ORDER BY stay_id, landmark_offset, chart_offset DESC;

DROP TABLE IF EXISTS saki_eicu.features_labs_recent_bun;
CREATE TABLE saki_eicu.features_labs_recent_bun AS
SELECT DISTINCT ON (stay_id, landmark_offset)
    stay_id,
    landmark_offset,
    labresult AS bun_recent
FROM saki_eicu.lab_window
WHERE labname IN ('bun', 'blood urea nitrogen')
ORDER BY stay_id, landmark_offset, chart_offset DESC;

DROP TABLE IF EXISTS saki_eicu.features_labs_recent;
CREATE TABLE saki_eicu.features_labs_recent AS
SELECT
    l.stay_id,
    l.landmark_offset,
    c.creatinine_recent,
    b.bun_recent
FROM saki_eicu.landmarks l
LEFT JOIN saki_eicu.features_labs_recent_creat c
    ON l.stay_id = c.stay_id
   AND l.landmark_offset = c.landmark_offset
LEFT JOIN saki_eicu.features_labs_recent_bun b
    ON l.stay_id = b.stay_id
   AND l.landmark_offset = b.landmark_offset;

DROP TABLE IF EXISTS saki_eicu.features_urine;
CREATE TABLE saki_eicu.features_urine AS
SELECT
    l.stay_id,
    l.landmark_offset,
    SUM(io.cellvaluenumeric) AS urine_output_total,
    COUNT(io.cellvaluenumeric) AS urine_output_count
FROM saki_eicu.landmarks l
LEFT JOIN public.intakeoutput io
    ON l.stay_id = io.patientunitstayid
   AND io.intakeoutputoffset >= l.saki_onset_offset
   AND io.intakeoutputoffset <= l.landmark_offset
   AND LOWER(COALESCE(io.cellpath, '') || ' ' || COALESCE(io.celllabel, '')) LIKE '%urine%'
   AND io.cellvaluenumeric IS NOT NULL
GROUP BY l.stay_id, l.landmark_offset;

DROP TABLE IF EXISTS saki_eicu.features_scores;
CREATE TABLE saki_eicu.features_scores AS
SELECT
    l.stay_id,
    l.landmark_offset,
    NULL::DOUBLE PRECISION AS sofa_max,
    NULL::DOUBLE PRECISION AS oasis,
    NULL::DOUBLE PRECISION AS sapsii
FROM saki_eicu.landmarks l;

DROP TABLE IF EXISTS saki_eicu.features_treatments;
CREATE TABLE saki_eicu.features_treatments AS
SELECT
    l.stay_id,
    l.landmark_offset,
    MAX(CASE WHEN LOWER(COALESCE(t.treatmentstring, '')) SIMILAR TO '%(ventilation|ventilator|mechanical ventilation)%' THEN 1 ELSE 0 END) AS mechanical_ventilation,
    MAX(CASE WHEN LOWER(COALESCE(i.drugname, '')) SIMILAR TO '%(norepinephrine|levophed|epinephrine|vasopressin|phenylephrine|dopamine)%' THEN 1 ELSE 0 END) AS vasopressor
FROM saki_eicu.landmarks l
LEFT JOIN public.treatment t
    ON l.stay_id = t.patientunitstayid
   AND t.treatmentoffset >= l.saki_onset_offset
   AND t.treatmentoffset <= l.landmark_offset
LEFT JOIN public.infusiondrug i
    ON l.stay_id = i.patientunitstayid
   AND i.infusionoffset >= l.saki_onset_offset
   AND i.infusionoffset <= l.landmark_offset
GROUP BY l.stay_id, l.landmark_offset;

DROP TABLE IF EXISTS saki_eicu.features_missingness;
CREATE TABLE saki_eicu.features_missingness AS
SELECT
    l.stay_id,
    l.landmark_offset,
    CASE WHEN lr.creatinine_recent IS NULL THEN 1 ELSE 0 END AS creatinine_missing,
    CASE WHEN lr.bun_recent IS NULL THEN 1 ELSE 0 END AS bun_missing,
    CASE WHEN fl.lactate_max IS NULL THEN 1 ELSE 0 END AS lactate_missing
FROM saki_eicu.landmarks l
LEFT JOIN saki_eicu.features_labs_recent lr
    ON l.stay_id = lr.stay_id
   AND l.landmark_offset = lr.landmark_offset
LEFT JOIN saki_eicu.features_labs fl
    ON l.stay_id = fl.stay_id
   AND l.landmark_offset = fl.landmark_offset;
