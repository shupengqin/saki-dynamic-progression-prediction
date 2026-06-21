-- Assemble final first-pass modeling dataset.

DROP TABLE IF EXISTS saki_dynamic.modeling_dataset;
CREATE TABLE saki_dynamic.modeling_dataset AS
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
    fl.creatinine_recent,
    fl.creatinine_max,
    fl.bun_recent,
    fl.bun_max,
    fl.bicarbonate_min,
    fl.sodium_min,
    fl.sodium_max,
    fl.potassium_min,
    fl.potassium_max,
    fl.chloride_min,
    fl.chloride_max,
    fc.wbc_max,
    fc.hemoglobin_min,
    fc.platelet_min,
    fc.hematocrit_min,
    fbg.lactate_max,
    fbg.ph_min,
    fu.urine_output_total,
    fu.urine_output_count,
    fs.sofa_max,
    fs.oasis,
    fs.sapsii,
    ft.mechanical_ventilation,
    ft.vasopressor,
    fm.creatinine_missing,
    fm.bun_missing,
    fm.lactate_missing
FROM saki_dynamic.landmarks l
LEFT JOIN saki_dynamic.features_vitals fv
    ON l.stay_id = fv.stay_id
   AND l.landmark_time = fv.landmark_time
LEFT JOIN saki_dynamic.features_labs fl
    ON l.stay_id = fl.stay_id
   AND l.landmark_time = fl.landmark_time
LEFT JOIN saki_dynamic.features_cbc fc
    ON l.stay_id = fc.stay_id
   AND l.landmark_time = fc.landmark_time
LEFT JOIN saki_dynamic.features_bg fbg
    ON l.stay_id = fbg.stay_id
   AND l.landmark_time = fbg.landmark_time
LEFT JOIN saki_dynamic.features_urine fu
    ON l.stay_id = fu.stay_id
   AND l.landmark_time = fu.landmark_time
LEFT JOIN saki_dynamic.features_scores fs
    ON l.stay_id = fs.stay_id
   AND l.landmark_time = fs.landmark_time
LEFT JOIN saki_dynamic.features_treatments ft
    ON l.stay_id = ft.stay_id
   AND l.landmark_time = ft.landmark_time
LEFT JOIN saki_dynamic.features_missingness fm
    ON l.stay_id = fm.stay_id
   AND l.landmark_time = fm.landmark_time;

-- Basic study counts.
SELECT
    landmark_hour,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT stay_id) AS n_stays,
    AVG(aki_progression_48h::numeric) AS event_rate
FROM saki_dynamic.modeling_dataset
GROUP BY landmark_hour
ORDER BY landmark_hour;

-- Missingness overview for core predictors.
SELECT
    AVG(creatinine_missing::numeric) AS creatinine_missing_rate,
    AVG(bun_missing::numeric) AS bun_missing_rate,
    AVG(lactate_missing::numeric) AS lactate_missing_rate,
    AVG(CASE WHEN urine_output_total IS NULL THEN 1 ELSE 0 END::numeric) AS urine_output_missing_rate
FROM saki_dynamic.modeling_dataset;
