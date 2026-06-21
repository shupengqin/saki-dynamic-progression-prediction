-- Predictor feature aggregation before each landmark.
-- This is a compact first-pass feature table. Expand after sample size checks.

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

DROP TABLE IF EXISTS saki_dynamic.features_labs;
CREATE TABLE saki_dynamic.features_labs AS
SELECT
    l.stay_id,
    l.landmark_time,
    MAX(ch.creatinine) AS creatinine_max,
    (
        SELECT ch2.creatinine
        FROM mimiciv_derived.chemistry ch2
        WHERE ch2.hadm_id = l.hadm_id
          AND ch2.charttime <= l.landmark_time
          AND ch2.charttime >= l.saki_onset_time
          AND ch2.creatinine IS NOT NULL
        ORDER BY ch2.charttime DESC
        LIMIT 1
    ) AS creatinine_recent,
    MAX(ch.bun) AS bun_max,
    (
        SELECT ch2.bun
        FROM mimiciv_derived.chemistry ch2
        WHERE ch2.hadm_id = l.hadm_id
          AND ch2.charttime <= l.landmark_time
          AND ch2.charttime >= l.saki_onset_time
          AND ch2.bun IS NOT NULL
        ORDER BY ch2.charttime DESC
        LIMIT 1
    ) AS bun_recent,
    MIN(ch.bicarbonate) AS bicarbonate_min,
    MIN(ch.sodium) AS sodium_min,
    MAX(ch.sodium) AS sodium_max,
    MIN(ch.potassium) AS potassium_min,
    MAX(ch.potassium) AS potassium_max,
    MIN(ch.chloride) AS chloride_min,
    MAX(ch.chloride) AS chloride_max
FROM saki_dynamic.landmarks l
LEFT JOIN mimiciv_derived.chemistry ch
    ON l.hadm_id = ch.hadm_id
   AND ch.charttime >= l.saki_onset_time
   AND ch.charttime <= l.landmark_time
GROUP BY l.stay_id, l.hadm_id, l.landmark_time, l.saki_onset_time;

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
    MAX(CASE WHEN ie.itemid IS NOT NULL THEN 1 ELSE 0 END) AS vasopressor
FROM saki_dynamic.landmarks l
LEFT JOIN mimiciv_derived.ventilation vent
    ON l.stay_id = vent.stay_id
   AND vent.starttime <= l.landmark_time
   AND vent.endtime >= l.saki_onset_time
LEFT JOIN mimiciv_icu.inputevents ie
    ON l.stay_id = ie.stay_id
   AND ie.starttime >= l.saki_onset_time
   AND ie.starttime <= l.landmark_time
   -- TODO: replace itemid list with the local vasopressor concept or derived table.
   AND ie.itemid IN (221906, 221289, 221749, 222315, 221662)
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
