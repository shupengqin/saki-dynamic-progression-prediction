-- MIMIC-III external/temporal validation dataset for S-AKI dynamic prediction.
-- This script uses explicit/Angus sepsis approximations and MIMIC-III derived KDIGO/RRT concepts.

DROP TABLE IF EXISTS saki_mimiciii.base_icu;
CREATE TABLE saki_mimiciii.base_icu AS
SELECT
    id.subject_id,
    id.hadm_id,
    id.icustay_id AS stay_id,
    id.gender,
    id.admission_age AS age,
    id.ethnicity AS race,
    id.hospital_expire_flag,
    id.admittime,
    id.dischtime,
    id.intime AS icu_intime,
    id.outtime AS icu_outtime,
    id.los_icu,
    id.first_icu_stay
FROM mimiciii_derived.icustay_detail id
WHERE id.admission_age >= 18
  AND id.first_icu_stay = TRUE
  AND id.los_icu >= 1.0;

DROP TABLE IF EXISTS saki_mimiciii.sepsis_icu;
CREATE TABLE saki_mimiciii.sepsis_icu AS
SELECT DISTINCT
    b.*,
    b.icu_intime AS sepsis_onset_time
FROM saki_mimiciii.base_icu b
LEFT JOIN mimiciii_derived.explicit ex
    ON b.hadm_id = ex.hadm_id
LEFT JOIN mimiciii_derived.angus an
    ON b.hadm_id = an.hadm_id
LEFT JOIN mimiciii_derived.martin ma
    ON b.hadm_id = ma.hadm_id
WHERE COALESCE(ex.sepsis, 0) = 1
   OR COALESCE(ex.severe_sepsis, 0) = 1
   OR COALESCE(ex.septic_shock, 0) = 1
   OR COALESCE(an.angus, 0) = 1
   OR COALESCE(ma.sepsis, 0) = 1;

DROP TABLE IF EXISTS saki_mimiciii.kdigo_timeline;
CREATE TABLE saki_mimiciii.kdigo_timeline AS
SELECT
    icustay_id AS stay_id,
    charttime,
    aki_stage,
    aki_stage_creat,
    aki_stage_uo
FROM mimiciii_derived.kdigo_stages
WHERE aki_stage IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_saki_m3_kdigo_stay_time
    ON saki_mimiciii.kdigo_timeline (stay_id, charttime);

DROP TABLE IF EXISTS saki_mimiciii.rrt_events;
CREATE TABLE saki_mimiciii.rrt_events AS
SELECT
    NULL::INTEGER AS stay_id,
    NULL::TIMESTAMP AS charttime,
    NULL::INTEGER AS rrt
WHERE FALSE;

CREATE INDEX IF NOT EXISTS idx_saki_m3_rrt_stay_time
    ON saki_mimiciii.rrt_events (stay_id, charttime);

DROP TABLE IF EXISTS saki_mimiciii.saki_onset;
CREATE TABLE saki_mimiciii.saki_onset AS
SELECT
    s.*,
    MIN(k.charttime) AS saki_onset_time
FROM saki_mimiciii.sepsis_icu s
INNER JOIN saki_mimiciii.kdigo_timeline k
    ON s.stay_id = k.stay_id
WHERE k.aki_stage >= 1
  AND k.charttime >= s.icu_intime
  AND k.charttime <= s.icu_outtime
GROUP BY
    s.subject_id, s.hadm_id, s.stay_id, s.gender, s.age, s.race,
    s.hospital_expire_flag, s.admittime, s.dischtime, s.icu_intime,
    s.icu_outtime, s.los_icu, s.first_icu_stay, s.sepsis_onset_time;

DROP TABLE IF EXISTS saki_mimiciii.landmarks_raw;
CREATE TABLE saki_mimiciii.landmarks_raw AS
SELECT *, saki_onset_time + INTERVAL '24 hour' AS landmark_time, 24 AS landmark_hour
FROM saki_mimiciii.saki_onset
UNION ALL
SELECT
    subject_id, hadm_id, stay_id, gender, age, race, hospital_expire_flag,
    admittime, dischtime, icu_intime, icu_outtime, los_icu, first_icu_stay,
    sepsis_onset_time, saki_onset_time,
    saki_onset_time + INTERVAL '48 hour' AS landmark_time, 48 AS landmark_hour
FROM saki_mimiciii.saki_onset
UNION ALL
SELECT
    subject_id, hadm_id, stay_id, gender, age, race, hospital_expire_flag,
    admittime, dischtime, icu_intime, icu_outtime, los_icu, first_icu_stay,
    sepsis_onset_time, saki_onset_time,
    saki_onset_time + INTERVAL '72 hour' AS landmark_time, 72 AS landmark_hour
FROM saki_mimiciii.saki_onset;

CREATE INDEX IF NOT EXISTS idx_saki_m3_landmarks_stay_time
    ON saki_mimiciii.landmarks_raw (stay_id, landmark_time);

DROP TABLE IF EXISTS saki_mimiciii.kdigo_window;
CREATE TABLE saki_mimiciii.kdigo_window AS
SELECT
    l.stay_id,
    l.landmark_time,
    k.charttime,
    k.aki_stage
FROM saki_mimiciii.landmarks_raw l
INNER JOIN saki_mimiciii.kdigo_timeline k
    ON l.stay_id = k.stay_id
   AND k.charttime <= l.landmark_time + INTERVAL '48 hour';

CREATE INDEX IF NOT EXISTS idx_saki_m3_kdigo_window_key
    ON saki_mimiciii.kdigo_window (stay_id, landmark_time, charttime);

DROP TABLE IF EXISTS saki_mimiciii.rrt_window;
CREATE TABLE saki_mimiciii.rrt_window AS
SELECT
    l.stay_id,
    l.landmark_time,
    r.charttime,
    r.rrt
FROM saki_mimiciii.landmarks_raw l
INNER JOIN saki_mimiciii.rrt_events r
    ON l.stay_id = r.stay_id
   AND r.charttime <= l.landmark_time + INTERVAL '48 hour';

CREATE INDEX IF NOT EXISTS idx_saki_m3_rrt_window_key
    ON saki_mimiciii.rrt_window (stay_id, landmark_time, charttime);

DROP TABLE IF EXISTS saki_mimiciii.current_kdigo;
CREATE TABLE saki_mimiciii.current_kdigo AS
SELECT DISTINCT ON (stay_id, landmark_time)
    stay_id,
    landmark_time,
    aki_stage AS current_kdigo
FROM saki_mimiciii.kdigo_window
WHERE charttime <= landmark_time
ORDER BY stay_id, landmark_time, charttime DESC;

DROP TABLE IF EXISTS saki_mimiciii.prior_kdigo;
CREATE TABLE saki_mimiciii.prior_kdigo AS
SELECT
    stay_id,
    landmark_time,
    MAX(aki_stage) AS current_or_prior_max_kdigo
FROM saki_mimiciii.kdigo_window
WHERE charttime <= landmark_time
GROUP BY stay_id, landmark_time;

DROP TABLE IF EXISTS saki_mimiciii.prior_rrt;
CREATE TABLE saki_mimiciii.prior_rrt AS
SELECT
    stay_id,
    landmark_time,
    MAX(rrt) AS prior_rrt
FROM saki_mimiciii.rrt_window
WHERE charttime <= landmark_time
GROUP BY stay_id, landmark_time;

DROP TABLE IF EXISTS saki_mimiciii.future_kdigo;
CREATE TABLE saki_mimiciii.future_kdigo AS
SELECT
    stay_id,
    landmark_time,
    MAX(aki_stage) AS future_max_kdigo
FROM saki_mimiciii.kdigo_window
WHERE charttime > landmark_time
  AND charttime <= landmark_time + INTERVAL '48 hour'
GROUP BY stay_id, landmark_time;

DROP TABLE IF EXISTS saki_mimiciii.future_rrt;
CREATE TABLE saki_mimiciii.future_rrt AS
SELECT
    stay_id,
    landmark_time,
    MAX(rrt) AS future_rrt
FROM saki_mimiciii.rrt_window
WHERE charttime > landmark_time
  AND charttime <= landmark_time + INTERVAL '48 hour'
GROUP BY stay_id, landmark_time;

DROP TABLE IF EXISTS saki_mimiciii.landmark_status;
CREATE TABLE saki_mimiciii.landmark_status AS
SELECT
    l.*,
    ck.current_kdigo,
    pk.current_or_prior_max_kdigo,
    COALESCE(pr.prior_rrt, 0) AS prior_rrt,
    fk.future_max_kdigo,
    COALESCE(fr.future_rrt, 0) AS future_rrt,
    CASE
        WHEN ck.current_kdigo = 1 AND fk.future_max_kdigo >= 2 THEN 1
        WHEN ck.current_kdigo = 2 AND fk.future_max_kdigo >= 3 THEN 1
        WHEN COALESCE(fr.future_rrt, 0) = 1 THEN 1
        ELSE 0
    END AS aki_progression_48h
FROM saki_mimiciii.landmarks_raw l
LEFT JOIN saki_mimiciii.current_kdigo ck
    ON l.stay_id = ck.stay_id
   AND l.landmark_time = ck.landmark_time
LEFT JOIN saki_mimiciii.prior_kdigo pk
    ON l.stay_id = pk.stay_id
   AND l.landmark_time = pk.landmark_time
LEFT JOIN saki_mimiciii.prior_rrt pr
    ON l.stay_id = pr.stay_id
   AND l.landmark_time = pr.landmark_time
LEFT JOIN saki_mimiciii.future_kdigo fk
    ON l.stay_id = fk.stay_id
   AND l.landmark_time = fk.landmark_time
LEFT JOIN saki_mimiciii.future_rrt fr
    ON l.stay_id = fr.stay_id
   AND l.landmark_time = fr.landmark_time;

DROP TABLE IF EXISTS saki_mimiciii.landmarks;
CREATE TABLE saki_mimiciii.landmarks AS
SELECT *
FROM saki_mimiciii.landmark_status
WHERE landmark_time <= icu_outtime
  AND landmark_time + INTERVAL '48 hour' <= icu_outtime
  AND current_kdigo IN (1, 2)
  AND COALESCE(prior_rrt, 0) = 0;

-- Feature extraction.
DROP TABLE IF EXISTS saki_mimiciii.vitals_window;
CREATE TABLE saki_mimiciii.vitals_window AS
SELECT
    l.stay_id,
    l.landmark_time,
    ce.charttime,
    di.label,
    ce.valuenum
FROM saki_mimiciii.landmarks l
INNER JOIN mimiciii.chartevents ce
    ON l.stay_id = ce.icustay_id
   AND ce.charttime >= l.saki_onset_time
   AND ce.charttime <= l.landmark_time
INNER JOIN mimiciii.d_items di
    ON ce.itemid = di.itemid
WHERE ce.valuenum IS NOT NULL
  AND LOWER(di.label) SIMILAR TO '%(heart rate|respiratory rate|temperature|spo2|o2 saturation|arterial blood pressure systolic|arterial blood pressure diastolic|arterial blood pressure mean|non invasive blood pressure systolic|non invasive blood pressure diastolic|non invasive blood pressure mean)%';

CREATE INDEX IF NOT EXISTS idx_saki_m3_vitals_window_key
    ON saki_mimiciii.vitals_window (stay_id, landmark_time);

DROP TABLE IF EXISTS saki_mimiciii.features_vitals;
CREATE TABLE saki_mimiciii.features_vitals AS
WITH normalized AS (
    SELECT
        stay_id,
        landmark_time,
        label,
        valuenum,
        CASE
            WHEN LOWER(label) SIMILAR TO '%(temperature)%' AND valuenum BETWEEN 80 AND 120
                THEN (valuenum - 32.0) * 5.0 / 9.0
            WHEN LOWER(label) SIMILAR TO '%(temperature)%' AND valuenum BETWEEN 25 AND 45
                THEN valuenum
            ELSE NULL
        END AS temp_c
    FROM saki_mimiciii.vitals_window
)
SELECT
    stay_id,
    landmark_time,
    AVG(CASE WHEN LOWER(label) = 'heart rate' THEN valuenum END) AS heart_rate_mean,
    MAX(CASE WHEN LOWER(label) = 'heart rate' THEN valuenum END) AS heart_rate_max,
    AVG(CASE WHEN LOWER(label) SIMILAR TO '%(systolic)%' THEN valuenum END) AS sbp_mean,
    MIN(CASE WHEN LOWER(label) SIMILAR TO '%(systolic)%' THEN valuenum END) AS sbp_min,
    AVG(CASE WHEN LOWER(label) SIMILAR TO '%(diastolic)%' THEN valuenum END) AS dbp_mean,
    MIN(CASE WHEN LOWER(label) SIMILAR TO '%(diastolic)%' THEN valuenum END) AS dbp_min,
    AVG(CASE WHEN LOWER(label) SIMILAR TO '%(mean)%' THEN valuenum END) AS map_mean,
    MIN(CASE WHEN LOWER(label) SIMILAR TO '%(mean)%' THEN valuenum END) AS map_min,
    AVG(CASE WHEN LOWER(label) = 'respiratory rate' THEN valuenum END) AS resp_rate_mean,
    MAX(CASE WHEN LOWER(label) = 'respiratory rate' THEN valuenum END) AS resp_rate_max,
    AVG(temp_c) AS temp_mean,
    MIN(temp_c) AS temp_min,
    MAX(temp_c) AS temp_max,
    AVG(CASE WHEN LOWER(label) SIMILAR TO '%(spo2|o2 saturation)%' THEN valuenum END) AS spo2_mean,
    MIN(CASE WHEN LOWER(label) SIMILAR TO '%(spo2|o2 saturation)%' THEN valuenum END) AS spo2_min
FROM normalized
GROUP BY stay_id, landmark_time;

DROP TABLE IF EXISTS saki_mimiciii.lab_window;
CREATE TABLE saki_mimiciii.lab_window AS
SELECT
    l.stay_id,
    l.hadm_id,
    l.landmark_time,
    le.charttime,
    LOWER(dli.label) AS labname,
    le.valuenum
FROM saki_mimiciii.landmarks l
INNER JOIN mimiciii.labevents le
    ON l.hadm_id = le.hadm_id
   AND le.charttime >= l.saki_onset_time
   AND le.charttime <= l.landmark_time
INNER JOIN mimiciii.d_labitems dli
    ON le.itemid = dli.itemid
WHERE le.valuenum IS NOT NULL
  AND LOWER(dli.label) SIMILAR TO '%(creatinine|urea nitrogen|bun|bicarbonate|sodium|potassium|chloride|white blood cells|hemoglobin|platelet|hematocrit|lactate|ph)%';

CREATE INDEX IF NOT EXISTS idx_saki_m3_lab_window_key
    ON saki_mimiciii.lab_window (stay_id, landmark_time, charttime);

DROP TABLE IF EXISTS saki_mimiciii.features_labs;
CREATE TABLE saki_mimiciii.features_labs AS
SELECT
    stay_id,
    landmark_time,
    MAX(CASE WHEN labname = 'creatinine' THEN valuenum END) AS creatinine_max,
    MAX(CASE WHEN labname IN ('urea nitrogen', 'bun') THEN valuenum END) AS bun_max,
    MIN(CASE WHEN labname = 'bicarbonate' THEN valuenum END) AS bicarbonate_min,
    MIN(CASE WHEN labname = 'sodium' THEN valuenum END) AS sodium_min,
    MAX(CASE WHEN labname = 'sodium' THEN valuenum END) AS sodium_max,
    MIN(CASE WHEN labname = 'potassium' THEN valuenum END) AS potassium_min,
    MAX(CASE WHEN labname = 'potassium' THEN valuenum END) AS potassium_max,
    MIN(CASE WHEN labname = 'chloride' THEN valuenum END) AS chloride_min,
    MAX(CASE WHEN labname = 'chloride' THEN valuenum END) AS chloride_max,
    MAX(CASE WHEN labname = 'white blood cells' THEN valuenum END) AS wbc_max,
    MIN(CASE WHEN labname = 'hemoglobin' THEN valuenum END) AS hemoglobin_min,
    MIN(CASE WHEN labname = 'platelet count' THEN valuenum END) AS platelet_min,
    MIN(CASE WHEN labname = 'hematocrit' THEN valuenum END) AS hematocrit_min,
    MAX(CASE WHEN labname = 'lactate' THEN valuenum END) AS lactate_max,
    MIN(CASE WHEN labname = 'ph' THEN valuenum END) AS ph_min
FROM saki_mimiciii.lab_window
GROUP BY stay_id, landmark_time;

DROP TABLE IF EXISTS saki_mimiciii.features_labs_recent_creat;
CREATE TABLE saki_mimiciii.features_labs_recent_creat AS
SELECT DISTINCT ON (stay_id, landmark_time)
    stay_id, landmark_time, valuenum AS creatinine_recent
FROM saki_mimiciii.lab_window
WHERE labname = 'creatinine'
ORDER BY stay_id, landmark_time, charttime DESC;

DROP TABLE IF EXISTS saki_mimiciii.features_labs_recent_bun;
CREATE TABLE saki_mimiciii.features_labs_recent_bun AS
SELECT DISTINCT ON (stay_id, landmark_time)
    stay_id, landmark_time, valuenum AS bun_recent
FROM saki_mimiciii.lab_window
WHERE labname IN ('urea nitrogen', 'bun')
ORDER BY stay_id, landmark_time, charttime DESC;

DROP TABLE IF EXISTS saki_mimiciii.features_labs_recent;
CREATE TABLE saki_mimiciii.features_labs_recent AS
SELECT
    l.stay_id,
    l.landmark_time,
    c.creatinine_recent,
    b.bun_recent
FROM saki_mimiciii.landmarks l
LEFT JOIN saki_mimiciii.features_labs_recent_creat c
    ON l.stay_id = c.stay_id AND l.landmark_time = c.landmark_time
LEFT JOIN saki_mimiciii.features_labs_recent_bun b
    ON l.stay_id = b.stay_id AND l.landmark_time = b.landmark_time;

DROP TABLE IF EXISTS saki_mimiciii.features_urine;
CREATE TABLE saki_mimiciii.features_urine AS
SELECT
    l.stay_id,
    l.landmark_time,
    SUM(uo.value) AS urine_output_total,
    COUNT(uo.value) AS urine_output_count
FROM saki_mimiciii.landmarks l
LEFT JOIN mimiciii_derived.urine_output uo
    ON l.stay_id = uo.icustay_id
   AND uo.charttime >= l.saki_onset_time
   AND uo.charttime <= l.landmark_time
GROUP BY l.stay_id, l.landmark_time;

DROP TABLE IF EXISTS saki_mimiciii.features_scores;
CREATE TABLE saki_mimiciii.features_scores AS
SELECT
    l.stay_id,
    l.landmark_time,
    MAX(sf.sofa) AS sofa_max,
    MAX(oa.oasis) AS oasis,
    MAX(sa.sapsii) AS sapsii
FROM saki_mimiciii.landmarks l
LEFT JOIN mimiciii_derived.sofa sf ON l.stay_id = sf.icustay_id
LEFT JOIN mimiciii_derived.oasis oa ON l.stay_id = oa.icustay_id
LEFT JOIN mimiciii_derived.sapsii sa ON l.stay_id = sa.icustay_id
GROUP BY l.stay_id, l.landmark_time;

DROP TABLE IF EXISTS saki_mimiciii.features_treatments;
CREATE TABLE saki_mimiciii.features_treatments AS
SELECT
    l.stay_id,
    l.landmark_time,
    MAX(CASE WHEN vd.icustay_id IS NOT NULL THEN 1 ELSE 0 END) AS mechanical_ventilation,
    MAX(CASE WHEN vp.icustay_id IS NOT NULL THEN 1 ELSE 0 END) AS vasopressor
FROM saki_mimiciii.landmarks l
LEFT JOIN mimiciii_derived.ventilation_durations vd
    ON l.stay_id = vd.icustay_id
   AND vd.starttime <= l.landmark_time
   AND vd.endtime >= l.saki_onset_time
LEFT JOIN mimiciii_derived.vasopressor_durations vp
    ON l.stay_id = vp.icustay_id
   AND vp.starttime <= l.landmark_time
   AND vp.endtime >= l.saki_onset_time
GROUP BY l.stay_id, l.landmark_time;

DROP TABLE IF EXISTS saki_mimiciii.modeling_dataset;
CREATE TABLE saki_mimiciii.modeling_dataset AS
SELECT
    l.subject_id,
    l.hadm_id,
    l.stay_id,
    l.gender,
    l.age,
    l.race,
    l.hospital_expire_flag,
    l.admittime,
    l.dischtime,
    l.icu_intime,
    l.icu_outtime,
    l.sepsis_onset_time,
    l.saki_onset_time,
    l.landmark_time,
    l.landmark_hour,
    l.current_kdigo,
    l.current_or_prior_max_kdigo,
    l.aki_progression_48h,
    fv.heart_rate_mean,
    fv.heart_rate_max,
    fv.sbp_mean,
    fv.sbp_min,
    fv.dbp_mean,
    fv.dbp_min,
    fv.map_mean,
    fv.map_min,
    fv.resp_rate_mean,
    fv.resp_rate_max,
    fv.temp_mean,
    fv.temp_min,
    fv.temp_max,
    fv.spo2_mean,
    fv.spo2_min,
    lr.creatinine_recent,
    fl.creatinine_max,
    lr.bun_recent,
    fl.bun_max,
    fl.bicarbonate_min,
    fl.sodium_min,
    fl.sodium_max,
    fl.potassium_min,
    fl.potassium_max,
    fl.chloride_min,
    fl.chloride_max,
    fl.wbc_max,
    fl.hemoglobin_min,
    fl.platelet_min,
    fl.hematocrit_min,
    fl.lactate_max,
    fl.ph_min,
    fu.urine_output_total,
    fu.urine_output_count,
    fs.sofa_max,
    fs.oasis,
    fs.sapsii,
    ft.mechanical_ventilation,
    ft.vasopressor,
    CASE WHEN lr.creatinine_recent IS NULL THEN 1 ELSE 0 END AS creatinine_missing,
    CASE WHEN lr.bun_recent IS NULL THEN 1 ELSE 0 END AS bun_missing,
    CASE WHEN fl.lactate_max IS NULL THEN 1 ELSE 0 END AS lactate_missing
FROM saki_mimiciii.landmarks l
LEFT JOIN saki_mimiciii.features_vitals fv ON l.stay_id = fv.stay_id AND l.landmark_time = fv.landmark_time
LEFT JOIN saki_mimiciii.features_labs fl ON l.stay_id = fl.stay_id AND l.landmark_time = fl.landmark_time
LEFT JOIN saki_mimiciii.features_labs_recent lr ON l.stay_id = lr.stay_id AND l.landmark_time = lr.landmark_time
LEFT JOIN saki_mimiciii.features_urine fu ON l.stay_id = fu.stay_id AND l.landmark_time = fu.landmark_time
LEFT JOIN saki_mimiciii.features_scores fs ON l.stay_id = fs.stay_id AND l.landmark_time = fs.landmark_time
LEFT JOIN saki_mimiciii.features_treatments ft ON l.stay_id = ft.stay_id AND l.landmark_time = ft.landmark_time;

SELECT landmark_hour, COUNT(*) AS n_rows, COUNT(DISTINCT stay_id) AS n_stays, AVG(aki_progression_48h::numeric) AS event_rate
FROM saki_mimiciii.modeling_dataset
GROUP BY landmark_hour
ORDER BY landmark_hour;
