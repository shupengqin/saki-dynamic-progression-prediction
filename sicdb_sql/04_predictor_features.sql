-- First-pass SICdb predictor feature aggregation.

DROP TABLE IF EXISTS saki_sicdb.observation_long;
CREATE TABLE saki_sicdb.observation_long AS
SELECT
    o.CaseID AS stay_id,
    o.Offset AS chart_offset,
    r.item_name,
    CAST(o.Value AS DOUBLE PRECISION) AS value
FROM sicdb.observations o
LEFT JOIN saki_sicdb.reference_long r
    ON o.DrugID = r.DrugID
WHERE o.Value IS NOT NULL;

DROP TABLE IF EXISTS saki_sicdb.lab_long;
CREATE TABLE saki_sicdb.lab_long AS
SELECT
    l.CaseID AS stay_id,
    l.Offset AS chart_offset,
    r.item_name,
    r.unit,
    r.loinc,
    CAST(l.Value AS DOUBLE PRECISION) AS labresult
FROM sicdb.laboratory l
INNER JOIN saki_sicdb.reference_long r
    ON l.DrugID = r.DrugID
WHERE l.Value IS NOT NULL;

DROP TABLE IF EXISTS saki_sicdb.features_vitals;
CREATE TABLE saki_sicdb.features_vitals AS
SELECT
    l.stay_id,
    l.landmark_offset,
    AVG(CASE WHEN o.item_name SIMILAR TO '%(heart rate|herzfrequenz|pulse)%' THEN o.value END) AS heart_rate_mean,
    MAX(CASE WHEN o.item_name SIMILAR TO '%(heart rate|herzfrequenz|pulse)%' THEN o.value END) AS heart_rate_max,
    AVG(CASE WHEN o.item_name SIMILAR TO '%(systolic|systol)%' THEN o.value END) AS sbp_mean,
    MIN(CASE WHEN o.item_name SIMILAR TO '%(systolic|systol)%' THEN o.value END) AS sbp_min,
    AVG(CASE WHEN o.item_name SIMILAR TO '%(diastolic|diastol)%' THEN o.value END) AS dbp_mean,
    MIN(CASE WHEN o.item_name SIMILAR TO '%(diastolic|diastol)%' THEN o.value END) AS dbp_min,
    AVG(CASE WHEN o.item_name SIMILAR TO '%(mean arterial|map|mittler)%' THEN o.value END) AS map_mean,
    MIN(CASE WHEN o.item_name SIMILAR TO '%(mean arterial|map|mittler)%' THEN o.value END) AS map_min,
    AVG(CASE WHEN o.item_name SIMILAR TO '%(respiratory rate|respiration|atemfrequenz)%' THEN o.value END) AS resp_rate_mean,
    MAX(CASE WHEN o.item_name SIMILAR TO '%(respiratory rate|respiration|atemfrequenz)%' THEN o.value END) AS resp_rate_max,
    AVG(CASE WHEN o.item_name SIMILAR TO '%(temperature|temperatur)%' THEN o.value END) AS temp_mean,
    MIN(CASE WHEN o.item_name SIMILAR TO '%(temperature|temperatur)%' THEN o.value END) AS temp_min,
    MAX(CASE WHEN o.item_name SIMILAR TO '%(temperature|temperatur)%' THEN o.value END) AS temp_max,
    AVG(CASE WHEN o.item_name SIMILAR TO '%(spo2|oxygen saturation|sauerstoff)%' THEN o.value END) AS spo2_mean,
    MIN(CASE WHEN o.item_name SIMILAR TO '%(spo2|oxygen saturation|sauerstoff)%' THEN o.value END) AS spo2_min
FROM saki_sicdb.landmarks l
LEFT JOIN saki_sicdb.observation_long o
    ON l.stay_id = o.stay_id
   AND o.chart_offset >= l.saki_onset_offset
   AND o.chart_offset <= l.landmark_offset
GROUP BY l.stay_id, l.landmark_offset;

DROP TABLE IF EXISTS saki_sicdb.features_labs;
CREATE TABLE saki_sicdb.features_labs AS
SELECT
    l.stay_id,
    l.landmark_offset,
    MAX(CASE WHEN lab.item_name SIMILAR TO '%(creatinine|kreatinin)%' OR lab.loinc IN ('2160-0', '38483-4') THEN lab.labresult END) AS creatinine_max,
    MAX(CASE WHEN lab.item_name SIMILAR TO '%(bun|urea|harnstoff)%' THEN lab.labresult END) AS bun_max,
    MIN(CASE WHEN lab.item_name SIMILAR TO '%(bicarbonate|hco3)%' THEN lab.labresult END) AS bicarbonate_min,
    MIN(CASE WHEN lab.item_name SIMILAR TO '%(sodium|natrium)%' THEN lab.labresult END) AS sodium_min,
    MAX(CASE WHEN lab.item_name SIMILAR TO '%(sodium|natrium)%' THEN lab.labresult END) AS sodium_max,
    MIN(CASE WHEN lab.item_name SIMILAR TO '%(potassium|kalium)%' THEN lab.labresult END) AS potassium_min,
    MAX(CASE WHEN lab.item_name SIMILAR TO '%(potassium|kalium)%' THEN lab.labresult END) AS potassium_max,
    MIN(CASE WHEN lab.item_name SIMILAR TO '%(chloride|chlorid)%' THEN lab.labresult END) AS chloride_min,
    MAX(CASE WHEN lab.item_name SIMILAR TO '%(chloride|chlorid)%' THEN lab.labresult END) AS chloride_max,
    MAX(CASE WHEN lab.item_name SIMILAR TO '%(wbc|leukocyte|leukozyt)%' THEN lab.labresult END) AS wbc_max,
    MIN(CASE WHEN lab.item_name SIMILAR TO '%(hemoglobin|haemoglobin|hgb)%' THEN lab.labresult END) AS hemoglobin_min,
    MIN(CASE WHEN lab.item_name SIMILAR TO '%(platelet|thrombocyte|thrombozyt)%' THEN lab.labresult END) AS platelet_min,
    MIN(CASE WHEN lab.item_name SIMILAR TO '%(hematocrit|haematocrit|hct)%' THEN lab.labresult END) AS hematocrit_min,
    MAX(CASE WHEN lab.item_name SIMILAR TO '%(lactate|laktat)%' THEN lab.labresult END) AS lactate_max,
    MIN(CASE WHEN lab.item_name = 'ph' OR lab.item_name SIMILAR TO '%(blood gas ph)%' THEN lab.labresult END) AS ph_min
FROM saki_sicdb.landmarks l
LEFT JOIN saki_sicdb.lab_long lab
    ON l.stay_id = lab.stay_id
   AND lab.chart_offset >= l.saki_onset_offset
   AND lab.chart_offset <= l.landmark_offset
GROUP BY l.stay_id, l.landmark_offset;

DROP TABLE IF EXISTS saki_sicdb.features_labs_recent;
CREATE TABLE saki_sicdb.features_labs_recent AS
SELECT
    l.stay_id,
    l.landmark_offset,
    (
        SELECT lab.labresult
        FROM saki_sicdb.lab_long lab
        WHERE lab.stay_id = l.stay_id
          AND (lab.item_name SIMILAR TO '%(creatinine|kreatinin)%' OR lab.loinc IN ('2160-0', '38483-4'))
          AND lab.chart_offset >= l.saki_onset_offset
          AND lab.chart_offset <= l.landmark_offset
        ORDER BY lab.chart_offset DESC
        LIMIT 1
    ) AS creatinine_recent,
    (
        SELECT lab.labresult
        FROM saki_sicdb.lab_long lab
        WHERE lab.stay_id = l.stay_id
          AND lab.item_name SIMILAR TO '%(bun|urea|harnstoff)%'
          AND lab.chart_offset >= l.saki_onset_offset
          AND lab.chart_offset <= l.landmark_offset
        ORDER BY lab.chart_offset DESC
        LIMIT 1
    ) AS bun_recent
FROM saki_sicdb.landmarks l;

DROP TABLE IF EXISTS saki_sicdb.features_urine;
CREATE TABLE saki_sicdb.features_urine AS
SELECT
    l.stay_id,
    l.landmark_offset,
    SUM(CASE WHEN o.item_name SIMILAR TO '%(urine|urin|diuresis)%' THEN o.value END) AS urine_output_total,
    COUNT(CASE WHEN o.item_name SIMILAR TO '%(urine|urin|diuresis)%' THEN 1 END) AS urine_output_count
FROM saki_sicdb.landmarks l
LEFT JOIN saki_sicdb.observation_long o
    ON l.stay_id = o.stay_id
   AND o.chart_offset >= l.saki_onset_offset
   AND o.chart_offset <= l.landmark_offset
GROUP BY l.stay_id, l.landmark_offset;

DROP TABLE IF EXISTS saki_sicdb.features_scores;
CREATE TABLE saki_sicdb.features_scores AS
SELECT
    l.stay_id,
    l.landmark_offset,
    NULL::DOUBLE PRECISION AS sofa_max,
    NULL::DOUBLE PRECISION AS oasis,
    NULL::DOUBLE PRECISION AS sapsii
FROM saki_sicdb.landmarks l;

DROP TABLE IF EXISTS saki_sicdb.features_treatments;
CREATE TABLE saki_sicdb.features_treatments AS
SELECT
    l.stay_id,
    l.landmark_offset,
    MAX(CASE WHEN r.item_name SIMILAR TO '%(ventilation|ventilator|beatmung)%' THEN 1 ELSE 0 END) AS mechanical_ventilation,
    MAX(CASE WHEN r.item_name SIMILAR TO '%(norepinephrine|noradrenaline|epinephrine|adrenaline|vasopressin|phenylephrine|dopamine)%' THEN 1 ELSE 0 END) AS vasopressor
FROM saki_sicdb.landmarks l
LEFT JOIN sicdb.medication m
    ON l.stay_id = m.CaseID
   AND m.Offset >= l.saki_onset_offset
   AND m.Offset <= l.landmark_offset
LEFT JOIN saki_sicdb.reference_long r
    ON m.DrugID = r.DrugID
GROUP BY l.stay_id, l.landmark_offset;

DROP TABLE IF EXISTS saki_sicdb.features_missingness;
CREATE TABLE saki_sicdb.features_missingness AS
SELECT
    l.stay_id,
    l.landmark_offset,
    CASE WHEN lr.creatinine_recent IS NULL THEN 1 ELSE 0 END AS creatinine_missing,
    CASE WHEN lr.bun_recent IS NULL THEN 1 ELSE 0 END AS bun_missing,
    CASE WHEN fl.lactate_max IS NULL THEN 1 ELSE 0 END AS lactate_missing
FROM saki_sicdb.landmarks l
LEFT JOIN saki_sicdb.features_labs_recent lr
    ON l.stay_id = lr.stay_id
   AND l.landmark_offset = lr.landmark_offset
LEFT JOIN saki_sicdb.features_labs fl
    ON l.stay_id = fl.stay_id
   AND l.landmark_offset = fl.landmark_offset;
