-- Adult first ICU stays with Sepsis-3.
-- Requires mimiciv_derived.icustay_detail and mimiciv_derived.sepsis3.

DROP TABLE IF EXISTS saki_dynamic.base_icu;
CREATE TABLE saki_dynamic.base_icu AS
SELECT
    id.subject_id,
    id.hadm_id,
    id.stay_id,
    id.gender,
    id.admission_age AS age,
    id.race,
    id.hospital_expire_flag,
    id.admittime,
    id.dischtime,
    id.icu_intime,
    id.icu_outtime,
    id.los_icu,
    id.first_icu_stay
FROM mimiciv_derived.icustay_detail id
WHERE id.admission_age >= 18
  AND id.first_icu_stay = TRUE
  AND id.los_icu >= 1.0;

DROP TABLE IF EXISTS saki_dynamic.sepsis_icu;
CREATE TABLE saki_dynamic.sepsis_icu AS
SELECT
    b.*,
    s.suspected_infection_time,
    s.sofa_time,
    s.sofa_score,
    COALESCE(s.sofa_time, s.suspected_infection_time, b.icu_intime) AS sepsis_onset_time
FROM saki_dynamic.base_icu b
INNER JOIN mimiciv_derived.sepsis3 s
    ON b.stay_id = s.stay_id
WHERE s.sepsis3 = TRUE;

-- Optional sanity check:
-- SELECT COUNT(*) AS n_icu, COUNT(DISTINCT stay_id) AS n_stays FROM saki_dynamic.sepsis_icu;
