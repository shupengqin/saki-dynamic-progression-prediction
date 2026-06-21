-- Validation checks for the eICU external validation dataset.
-- Run this after 05_modeling_dataset.sql.

-- 1. Cohort attrition.
SELECT 'base_icu' AS step, COUNT(*) AS n_rows, COUNT(DISTINCT stay_id) AS n_stays
FROM saki_eicu.base_icu
UNION ALL
SELECT 'suspected_infection', COUNT(*), COUNT(DISTINCT stay_id)
FROM saki_eicu.suspected_infection
UNION ALL
SELECT 'sepsis_icu', COUNT(*), COUNT(DISTINCT stay_id)
FROM saki_eicu.sepsis_icu
UNION ALL
SELECT 'saki_onset', COUNT(*), COUNT(DISTINCT stay_id)
FROM saki_eicu.saki_onset
UNION ALL
SELECT 'landmarks_raw', COUNT(*), COUNT(DISTINCT stay_id)
FROM saki_eicu.landmarks_raw
UNION ALL
SELECT 'eligible_landmarks', COUNT(*), COUNT(DISTINCT stay_id)
FROM saki_eicu.landmarks
UNION ALL
SELECT 'modeling_dataset', COUNT(*), COUNT(DISTINCT stay_id)
FROM saki_eicu.modeling_dataset;

-- 2. Event rate by landmark.
SELECT
    landmark_hour,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT stay_id) AS n_stays,
    SUM(aki_progression_48h) AS n_events,
    AVG(aki_progression_48h::numeric) AS event_rate
FROM saki_eicu.modeling_dataset
GROUP BY landmark_hour
ORDER BY landmark_hour;

-- 3. KDIGO stage distribution at landmark.
SELECT
    landmark_hour,
    current_kdigo,
    COUNT(*) AS n_rows,
    AVG(aki_progression_48h::numeric) AS event_rate
FROM saki_eicu.modeling_dataset
GROUP BY landmark_hour, current_kdigo
ORDER BY landmark_hour, current_kdigo;

-- 4. Time-order checks.
SELECT
    COUNT(*) AS n_time_order_violations
FROM saki_eicu.modeling_dataset
WHERE NOT (
    0 <= sepsis_onset_offset
    AND sepsis_onset_offset <= saki_onset_offset
    AND saki_onset_offset < landmark_offset
    AND landmark_offset <= icu_outtime
);

-- 5. Full future 48-hour ICU follow-up.
SELECT
    COUNT(*) AS n_rows_without_full_48h_icu_followup
FROM saki_eicu.modeling_dataset
WHERE landmark_offset + 2880 > icu_outtime;

-- 6. Main exclusion check.
SELECT
    COUNT(*) AS n_invalid_landmark_rows
FROM saki_eicu.landmarks
WHERE current_kdigo NOT IN (1, 2)
   OR prior_rrt = 1;

-- 7. Predictor missingness.
SELECT
    AVG(CASE WHEN creatinine_recent IS NULL THEN 1 ELSE 0 END::numeric) AS creatinine_recent_missing,
    AVG(CASE WHEN bun_recent IS NULL THEN 1 ELSE 0 END::numeric) AS bun_recent_missing,
    AVG(CASE WHEN lactate_max IS NULL THEN 1 ELSE 0 END::numeric) AS lactate_missing,
    AVG(CASE WHEN platelet_min IS NULL THEN 1 ELSE 0 END::numeric) AS platelet_missing,
    AVG(CASE WHEN map_mean IS NULL THEN 1 ELSE 0 END::numeric) AS map_missing,
    AVG(CASE WHEN urine_output_total IS NULL THEN 1 ELSE 0 END::numeric) AS urine_output_missing,
    AVG(CASE WHEN sofa_max IS NULL THEN 1 ELSE 0 END::numeric) AS sofa_missing
FROM saki_eicu.modeling_dataset;

-- 8. Outcome components.
SELECT
    landmark_hour,
    SUM(CASE WHEN future_rrt = 1 THEN 1 ELSE 0 END) AS n_future_rrt,
    SUM(CASE WHEN current_kdigo = 1 AND future_max_kdigo >= 2 THEN 1 ELSE 0 END) AS n_stage1_to_2plus,
    SUM(CASE WHEN current_kdigo = 2 AND future_max_kdigo >= 3 THEN 1 ELSE 0 END) AS n_stage2_to_3
FROM saki_eicu.landmarks
GROUP BY landmark_hour
ORDER BY landmark_hour;

-- 9. Duplicate row check.
SELECT
    stay_id,
    landmark_offset,
    COUNT(*) AS n
FROM saki_eicu.modeling_dataset
GROUP BY stay_id, landmark_offset
HAVING COUNT(*) > 1
ORDER BY n DESC;

