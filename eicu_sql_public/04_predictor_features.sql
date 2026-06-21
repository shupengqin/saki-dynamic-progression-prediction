-- First-pass eICU predictor feature aggregation.

DROP TABLE IF EXISTS saki_eicu.features_vitals;
CREATE TABLE saki_eicu.features_vitals AS
SELECT
    l.stay_id,
    l.landmark_offset,
    AVG(v.heartrate) AS heart_rate_mean,
    MAX(v.heartrate) AS heart_rate_max,
    AVG(v.systemicsystolic) AS sbp_mean,
    MIN(v.systemicsystolic) AS sbp_min,
    AVG(v.systemicdiastolic) AS dbp_mean,
    MIN(v.systemicdiastolic) AS dbp_min,
    AVG(v.systemicmean) AS map_mean,
    MIN(v.systemicmean) AS map_min,
    AVG(v.respiration) AS resp_rate_mean,
    MAX(v.respiration) AS resp_rate_max,
    AVG(v.temperature) AS temp_mean,
    MIN(v.temperature) AS temp_min,
    MAX(v.temperature) AS temp_max,
    AVG(v.sao2) AS spo2_mean,
    MIN(v.sao2) AS spo2_min
FROM saki_eicu.landmarks l
LEFT JOIN public.vitalperiodic v
    ON l.stay_id = v.patientunitstayid
   AND v.observationoffset >= l.saki_onset_offset
   AND v.observationoffset <= l.landmark_offset
GROUP BY l.stay_id, l.landmark_offset;

DROP TABLE IF EXISTS saki_eicu.lab_long;
CREATE TABLE saki_eicu.lab_long AS
SELECT
    patientunitstayid AS stay_id,
    labresultoffset AS chart_offset,
    LOWER(labname) AS labname,
    CAST(labresult AS DOUBLE PRECISION) AS labresult
FROM public.lab
WHERE labresult IS NOT NULL;

DROP TABLE IF EXISTS saki_eicu.features_labs;
CREATE TABLE saki_eicu.features_labs AS
SELECT
    l.stay_id,
    l.landmark_offset,
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
FROM saki_eicu.landmarks l
LEFT JOIN saki_eicu.lab_long lab
    ON l.stay_id = lab.stay_id
   AND lab.chart_offset >= l.saki_onset_offset
   AND lab.chart_offset <= l.landmark_offset
GROUP BY l.stay_id, l.landmark_offset;

DROP TABLE IF EXISTS saki_eicu.features_labs_recent;
CREATE TABLE saki_eicu.features_labs_recent AS
SELECT
    l.stay_id,
    l.landmark_offset,
    (
        SELECT lab.labresult
        FROM saki_eicu.lab_long lab
        WHERE lab.stay_id = l.stay_id
          AND lab.labname = 'creatinine'
          AND lab.chart_offset >= l.saki_onset_offset
          AND lab.chart_offset <= l.landmark_offset
        ORDER BY lab.chart_offset DESC
        LIMIT 1
    ) AS creatinine_recent,
    (
        SELECT lab.labresult
        FROM saki_eicu.lab_long lab
        WHERE lab.stay_id = l.stay_id
          AND lab.labname IN ('bun', 'blood urea nitrogen')
          AND lab.chart_offset >= l.saki_onset_offset
          AND lab.chart_offset <= l.landmark_offset
        ORDER BY lab.chart_offset DESC
        LIMIT 1
    ) AS bun_recent
FROM saki_eicu.landmarks l;

DROP TABLE IF EXISTS saki_eicu.features_urine;
CREATE TABLE saki_eicu.features_urine AS
SELECT
    l.stay_id,
    l.landmark_offset,
    SUM(io.outputtotal) AS urine_output_total,
    COUNT(io.outputtotal) AS urine_output_count
FROM saki_eicu.landmarks l
LEFT JOIN public.intakeoutput io
    ON l.stay_id = io.patientunitstayid
   AND io.intakeoutputoffset >= l.saki_onset_offset
   AND io.intakeoutputoffset <= l.landmark_offset
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

