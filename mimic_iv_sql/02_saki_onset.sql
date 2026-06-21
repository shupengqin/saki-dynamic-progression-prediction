-- Define S-AKI onset using Sepsis-3 plus KDIGO AKI stage >= 1.
-- Requires mimiciv_derived.kdigo_stages with stay_id, charttime, aki_stage.

DROP TABLE IF EXISTS saki_dynamic.kdigo_timeline;
CREATE TABLE saki_dynamic.kdigo_timeline AS
SELECT
    stay_id,
    charttime,
    aki_stage,
    aki_stage_creat,
    aki_stage_uo
FROM mimiciv_derived.kdigo_stages
WHERE aki_stage IS NOT NULL;

DROP TABLE IF EXISTS saki_dynamic.saki_onset;
CREATE TABLE saki_dynamic.saki_onset AS
WITH aki_active AS (
    SELECT
        s.subject_id,
        s.hadm_id,
        s.stay_id,
        s.icu_intime,
        s.icu_outtime,
        s.sepsis_onset_time,
        k.charttime,
        k.aki_stage
    FROM saki_dynamic.sepsis_icu s
    INNER JOIN saki_dynamic.kdigo_timeline k
        ON s.stay_id = k.stay_id
    WHERE k.aki_stage >= 1
      AND k.charttime >= s.icu_intime
      AND k.charttime <= s.icu_outtime
),
first_aki_after_sepsis AS (
    SELECT
        subject_id,
        hadm_id,
        stay_id,
        MIN(charttime) AS first_aki_after_sepsis_time
    FROM aki_active
    WHERE charttime >= sepsis_onset_time
    GROUP BY subject_id, hadm_id, stay_id
),
aki_at_sepsis AS (
    SELECT
        a.subject_id,
        a.hadm_id,
        a.stay_id,
        MIN(a.sepsis_onset_time) AS sepsis_time_with_active_aki
    FROM aki_active a
    WHERE a.charttime <= a.sepsis_onset_time
      AND a.charttime >= a.sepsis_onset_time - INTERVAL '48 hour'
    GROUP BY a.subject_id, a.hadm_id, a.stay_id
)
SELECT
    s.subject_id,
    s.hadm_id,
    s.stay_id,
    s.gender,
    s.age,
    s.race,
    s.hospital_expire_flag,
    s.admittime,
    s.dischtime,
    s.icu_intime,
    s.icu_outtime,
    s.los_icu,
    s.sepsis_onset_time,
    COALESCE(f.first_aki_after_sepsis_time, ats.sepsis_time_with_active_aki) AS saki_onset_time
FROM saki_dynamic.sepsis_icu s
LEFT JOIN first_aki_after_sepsis f
    ON s.stay_id = f.stay_id
LEFT JOIN aki_at_sepsis ats
    ON s.stay_id = ats.stay_id
WHERE COALESCE(f.first_aki_after_sepsis_time, ats.sepsis_time_with_active_aki) IS NOT NULL;

-- Optional sanity checks:
-- SELECT COUNT(*) AS n_saki FROM saki_dynamic.saki_onset;
-- SELECT MIN(saki_onset_time), MAX(saki_onset_time) FROM saki_dynamic.saki_onset;

