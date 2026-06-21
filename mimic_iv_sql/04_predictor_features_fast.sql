-- Faster materialized predictor feature aggregation for PostgreSQL.

DROP TABLE IF EXISTS saki_dynamic.features_vitals;
CREATE TABLE saki_dynamic.features_vitals AS
SELECT
    l.stay_id,
    l.landmark_time,
    AVG(v.heart_rate) AS heart_rate_mean,
    MAX(v.heart_rate) AS heart_rate_max,
    AVG(v.sbp) AS sbp_mean,
    MIN(v.sbp) AS sbp_min,
    AVG(v.dbp) AS dbp_mean,
    MIN(v.dbp) AS dbp_min,
    AVG(v.mbp) AS map_mean,
    MIN(v.mbp) AS map_min,
    AVG(v.resp_rate) AS resp_rate_mean,
    MAX(v.resp_rate) AS resp_rate_max,
    AVG(v.temperature) AS temp_mean,
    MIN(v.temperature) AS temp_min,
    MAX(v.temperature) AS temp_max,
    AVG(v.spo2) AS spo2_mean,
    MIN(v.spo2) AS spo2_min
FROM saki_dynamic.landmarks l
LEFT JOIN mimiciv_derived.vitalsign v
    ON l.stay_id = v.stay_id
   AND v.charttime >= l.saki_onset_time
   AND v.charttime <= l.landmark_time
GROUP BY l.stay_id, l.landmark_time;

DROP TABLE IF EXISTS saki_dynamic.chemistry_window;
CREATE TABLE saki_dynamic.chemistry_window AS
SELECT
    l.stay_id,
    l.hadm_id,
    l.landmark_time,
    ch.charttime,
    ch.creatinine,
    ch.bun,
    ch.bicarbonate,
    ch.sodium,
    ch.potassium,
    ch.chloride
FROM saki_dynamic.landmarks l
LEFT JOIN mimiciv_derived.chemistry ch
    ON l.hadm_id = ch.hadm_id
   AND ch.charttime >= l.saki_onset_time
   AND ch.charttime <= l.landmark_time;

CREATE INDEX IF NOT EXISTS idx_saki_chemistry_window_key
    ON saki_dynamic.chemistry_window (stay_id, landmark_time, charttime);

DROP TABLE IF EXISTS saki_dynamic.features_labs_agg;
CREATE TABLE saki_dynamic.features_labs_agg AS
SELECT
    stay_id,
    landmark_time,
    MAX(creatinine) AS creatinine_max,
    MAX(bun) AS bun_max,
    MIN(bicarbonate) AS bicarbonate_min,
    MIN(sodium) AS sodium_min,
    MAX(sodium) AS sodium_max,
    MIN(potassium) AS potassium_min,
    MAX(potassium) AS potassium_max,
    MIN(chloride) AS chloride_min,
    MAX(chloride) AS chloride_max
FROM saki_dynamic.chemistry_window
GROUP BY stay_id, landmark_time;

DROP TABLE IF EXISTS saki_dynamic.features_labs_recent_creat;
CREATE TABLE saki_dynamic.features_labs_recent_creat AS
SELECT DISTINCT ON (stay_id, landmark_time)
    stay_id,
    landmark_time,
    creatinine AS creatinine_recent
FROM saki_dynamic.chemistry_window
WHERE creatinine IS NOT NULL
ORDER BY stay_id, landmark_time, charttime DESC;

DROP TABLE IF EXISTS saki_dynamic.features_labs_recent_bun;
CREATE TABLE saki_dynamic.features_labs_recent_bun AS
SELECT DISTINCT ON (stay_id, landmark_time)
    stay_id,
    landmark_time,
    bun AS bun_recent
FROM saki_dynamic.chemistry_window
WHERE bun IS NOT NULL
ORDER BY stay_id, landmark_time, charttime DESC;

DROP TABLE IF EXISTS saki_dynamic.features_labs;
CREATE TABLE saki_dynamic.features_labs AS
SELECT
    a.stay_id,
    a.landmark_time,
    a.creatinine_max,
    rc.creatinine_recent,
    a.bun_max,
    rb.bun_recent,
    a.bicarbonate_min,
    a.sodium_min,
    a.sodium_max,
    a.potassium_min,
    a.potassium_max,
    a.chloride_min,
    a.chloride_max
FROM saki_dynamic.features_labs_agg a
LEFT JOIN saki_dynamic.features_labs_recent_creat rc
    ON a.stay_id = rc.stay_id
   AND a.landmark_time = rc.landmark_time
LEFT JOIN saki_dynamic.features_labs_recent_bun rb
    ON a.stay_id = rb.stay_id
   AND a.landmark_time = rb.landmark_time;

DROP TABLE IF EXISTS saki_dynamic.features_cbc;
CREATE TABLE saki_dynamic.features_cbc AS
SELECT
    l.stay_id,
    l.landmark_time,
    MAX(cbc.wbc) AS wbc_max,
    MIN(cbc.hemoglobin) AS hemoglobin_min,
    MIN(cbc.platelet) AS platelet_min,
    MIN(cbc.hematocrit) AS hematocrit_min
FROM saki_dynamic.landmarks l
LEFT JOIN mimiciv_derived.complete_blood_count cbc
    ON l.hadm_id = cbc.hadm_id
   AND cbc.charttime >= l.saki_onset_time
   AND cbc.charttime <= l.landmark_time
GROUP BY l.stay_id, l.landmark_time;

DROP TABLE IF EXISTS saki_dynamic.features_bg;
CREATE TABLE saki_dynamic.features_bg AS
SELECT
    l.stay_id,
    l.landmark_time,
    MAX(bg.lactate) AS lactate_max,
    MIN(bg.ph) AS ph_min
FROM saki_dynamic.landmarks l
LEFT JOIN mimiciv_derived.bg bg
    ON l.hadm_id = bg.hadm_id
   AND bg.charttime >= l.saki_onset_time
   AND bg.charttime <= l.landmark_time
GROUP BY l.stay_id, l.landmark_time;

DROP TABLE IF EXISTS saki_dynamic.features_urine;
CREATE TABLE saki_dynamic.features_urine AS
SELECT
    l.stay_id,
    l.landmark_time,
    SUM(uo.urineoutput) AS urine_output_total,
    COUNT(uo.urineoutput) AS urine_output_count
FROM saki_dynamic.landmarks l
LEFT JOIN mimiciv_derived.urine_output uo
    ON l.stay_id = uo.stay_id
   AND uo.charttime >= l.saki_onset_time
   AND uo.charttime <= l.landmark_time
GROUP BY l.stay_id, l.landmark_time;

DROP TABLE IF EXISTS saki_dynamic.features_scores;
CREATE TABLE saki_dynamic.features_scores AS
SELECT
    l.stay_id,
    l.landmark_time,
    MAX(sf.sofa_24hours) AS sofa_max,
    MAX(oa.oasis) AS oasis,
    MAX(sa.sapsii) AS sapsii
FROM saki_dynamic.landmarks l
LEFT JOIN mimiciv_derived.sofa sf
    ON l.stay_id = sf.stay_id
   AND sf.starttime >= l.saki_onset_time
   AND sf.endtime <= l.landmark_time
LEFT JOIN mimiciv_derived.oasis oa
    ON l.stay_id = oa.stay_id
LEFT JOIN mimiciv_derived.sapsii sa
    ON l.stay_id = sa.stay_id
GROUP BY l.stay_id, l.landmark_time;

DROP TABLE IF EXISTS saki_dynamic.features_treatments;
CREATE TABLE saki_dynamic.features_treatments AS
SELECT
    l.stay_id,
    l.landmark_time,
    MAX(CASE WHEN vent.ventilation_status IS NOT NULL THEN 1 ELSE 0 END) AS mechanical_ventilation,
    MAX(CASE WHEN va.stay_id IS NOT NULL THEN 1 ELSE 0 END) AS vasopressor
FROM saki_dynamic.landmarks l
LEFT JOIN mimiciv_derived.ventilation vent
    ON l.stay_id = vent.stay_id
   AND vent.starttime <= l.landmark_time
   AND vent.endtime >= l.saki_onset_time
LEFT JOIN mimiciv_derived.vasoactive_agent va
    ON l.stay_id = va.stay_id
   AND va.starttime <= l.landmark_time
   AND va.endtime >= l.saki_onset_time
GROUP BY l.stay_id, l.landmark_time;

DROP TABLE IF EXISTS saki_dynamic.features_missingness;
CREATE TABLE saki_dynamic.features_missingness AS
SELECT
    l.stay_id,
    l.landmark_time,
    CASE WHEN fl.creatinine_recent IS NULL THEN 1 ELSE 0 END AS creatinine_missing,
    CASE WHEN fl.bun_recent IS NULL THEN 1 ELSE 0 END AS bun_missing,
    CASE WHEN fbg.lactate_max IS NULL THEN 1 ELSE 0 END AS lactate_missing
FROM saki_dynamic.landmarks l
LEFT JOIN saki_dynamic.features_labs fl
    ON l.stay_id = fl.stay_id
   AND l.landmark_time = fl.landmark_time
LEFT JOIN saki_dynamic.features_bg fbg
    ON l.stay_id = fbg.stay_id
   AND l.landmark_time = fbg.landmark_time;

