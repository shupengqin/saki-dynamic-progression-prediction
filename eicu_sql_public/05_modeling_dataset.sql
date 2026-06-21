-- Assemble eICU external validation modeling dataset.

DROP TABLE IF EXISTS saki_eicu.modeling_dataset;
CREATE TABLE saki_eicu.modeling_dataset AS
SELECT
    l.subject_id,
    l.hadm_id,
    l.stay_id,
    l.gender,
    l.age,
    l.race,
    CASE WHEN LOWER(COALESCE(l.hospitaldischargestatus, '')) = 'expired' THEN 1 ELSE 0 END AS hospital_expire_flag,
    0 AS icu_intime,
    l.unitdischargeoffset AS icu_outtime,
    l.sepsis_onset_offset,
    l.saki_onset_offset,
    l.landmark_offset,
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
    fm.creatinine_missing,
    fm.bun_missing,
    fm.lactate_missing
FROM saki_eicu.landmarks l
LEFT JOIN saki_eicu.features_vitals fv
    ON l.stay_id = fv.stay_id
   AND l.landmark_offset = fv.landmark_offset
LEFT JOIN saki_eicu.features_labs fl
    ON l.stay_id = fl.stay_id
   AND l.landmark_offset = fl.landmark_offset
LEFT JOIN saki_eicu.features_labs_recent lr
    ON l.stay_id = lr.stay_id
   AND l.landmark_offset = lr.landmark_offset
LEFT JOIN saki_eicu.features_urine fu
    ON l.stay_id = fu.stay_id
   AND l.landmark_offset = fu.landmark_offset
LEFT JOIN saki_eicu.features_scores fs
    ON l.stay_id = fs.stay_id
   AND l.landmark_offset = fs.landmark_offset
LEFT JOIN saki_eicu.features_treatments ft
    ON l.stay_id = ft.stay_id
   AND l.landmark_offset = ft.landmark_offset
LEFT JOIN saki_eicu.features_missingness fm
    ON l.stay_id = fm.stay_id
   AND l.landmark_offset = fm.landmark_offset;

SELECT
    landmark_hour,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT stay_id) AS n_stays,
    AVG(aki_progression_48h::numeric) AS event_rate
FROM saki_eicu.modeling_dataset
GROUP BY landmark_hour
ORDER BY landmark_hour;

