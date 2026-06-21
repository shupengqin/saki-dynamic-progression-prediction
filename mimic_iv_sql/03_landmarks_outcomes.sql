-- Create landmark rows and future 48-hour AKI progression outcome.
-- Requires saki_dynamic.saki_onset, saki_dynamic.kdigo_timeline, and mimiciv_derived.rrt.

DROP TABLE IF EXISTS saki_dynamic.rrt_events;
CREATE TABLE saki_dynamic.rrt_events AS
SELECT DISTINCT
    stay_id,
    charttime,
    1 AS rrt
FROM mimiciv_derived.rrt
WHERE dialysis_active = 1 OR dialysis_present = 1;

CREATE INDEX IF NOT EXISTS idx_saki_rrt_events_stay_time
    ON saki_dynamic.rrt_events (stay_id, charttime);

DROP TABLE IF EXISTS saki_dynamic.landmarks_raw;
CREATE TABLE saki_dynamic.landmarks_raw AS
SELECT
    subject_id,
    hadm_id,
    stay_id,
    gender,
    age,
    race,
    hospital_expire_flag,
    admittime,
    dischtime,
    icu_intime,
    icu_outtime,
    los_icu,
    sepsis_onset_time,
    saki_onset_time,
    saki_onset_time + INTERVAL '24 hour' AS landmark_time,
    24 AS landmark_hour
FROM saki_dynamic.saki_onset
UNION ALL
SELECT
    subject_id, hadm_id, stay_id, gender, age, race, hospital_expire_flag,
    admittime, dischtime, icu_intime, icu_outtime, los_icu,
    sepsis_onset_time, saki_onset_time,
    saki_onset_time + INTERVAL '48 hour' AS landmark_time,
    48 AS landmark_hour
FROM saki_dynamic.saki_onset
UNION ALL
SELECT
    subject_id, hadm_id, stay_id, gender, age, race, hospital_expire_flag,
    admittime, dischtime, icu_intime, icu_outtime, los_icu,
    sepsis_onset_time, saki_onset_time,
    saki_onset_time + INTERVAL '72 hour' AS landmark_time,
    72 AS landmark_hour
FROM saki_dynamic.saki_onset;

CREATE INDEX IF NOT EXISTS idx_saki_landmarks_raw_stay_time
    ON saki_dynamic.landmarks_raw (stay_id, landmark_time);
CREATE INDEX IF NOT EXISTS idx_saki_kdigo_timeline_stay_time
    ON saki_dynamic.kdigo_timeline (stay_id, charttime);

DROP TABLE IF EXISTS saki_dynamic.landmark_status;
CREATE TABLE saki_dynamic.landmark_status AS
WITH kdigo_window AS (
    SELECT
        l.stay_id,
        l.landmark_time,
        k.charttime,
        k.aki_stage
    FROM saki_dynamic.landmarks_raw l
    INNER JOIN saki_dynamic.kdigo_timeline k
        ON l.stay_id = k.stay_id
       AND k.charttime <= l.landmark_time + INTERVAL '48 hour'
),
rrt_window AS (
    SELECT
        l.stay_id,
        l.landmark_time,
        r.charttime,
        r.rrt
    FROM saki_dynamic.landmarks_raw l
    INNER JOIN saki_dynamic.rrt_events r
        ON l.stay_id = r.stay_id
       AND r.charttime <= l.landmark_time + INTERVAL '48 hour'
),
current_kdigo AS (
    SELECT DISTINCT ON (l.stay_id, l.landmark_time)
        l.stay_id,
        l.landmark_time,
        k.aki_stage AS current_kdigo
    FROM saki_dynamic.landmarks_raw l
    INNER JOIN kdigo_window k
        ON l.stay_id = k.stay_id
       AND l.landmark_time = k.landmark_time
       AND k.charttime <= l.landmark_time
    ORDER BY l.stay_id, l.landmark_time, k.charttime DESC
),
prior_kdigo AS (
    SELECT
        l.stay_id,
        l.landmark_time,
        MAX(k.aki_stage) AS current_or_prior_max_kdigo
    FROM saki_dynamic.landmarks_raw l
    LEFT JOIN kdigo_window k
        ON l.stay_id = k.stay_id
       AND l.landmark_time = k.landmark_time
       AND k.charttime <= l.landmark_time
    GROUP BY l.stay_id, l.landmark_time
),
prior_rrt AS (
    SELECT
        l.stay_id,
        l.landmark_time,
        MAX(CASE WHEN r.rrt = 1 THEN 1 ELSE 0 END) AS prior_rrt
    FROM saki_dynamic.landmarks_raw l
    LEFT JOIN rrt_window r
        ON l.stay_id = r.stay_id
       AND l.landmark_time = r.landmark_time
       AND r.charttime <= l.landmark_time
    GROUP BY l.stay_id, l.landmark_time
),
future_kdigo AS (
    SELECT
        l.stay_id,
        l.landmark_time,
        MAX(k.aki_stage) AS future_max_kdigo
    FROM saki_dynamic.landmarks_raw l
    LEFT JOIN kdigo_window k
        ON l.stay_id = k.stay_id
       AND l.landmark_time = k.landmark_time
       AND k.charttime > l.landmark_time
       AND k.charttime <= l.landmark_time + INTERVAL '48 hour'
    GROUP BY l.stay_id, l.landmark_time
),
future_rrt AS (
    SELECT
        l.stay_id,
        l.landmark_time,
        MAX(CASE WHEN r.rrt = 1 THEN 1 ELSE 0 END) AS future_rrt
    FROM saki_dynamic.landmarks_raw l
    LEFT JOIN rrt_window r
        ON l.stay_id = r.stay_id
       AND l.landmark_time = r.landmark_time
       AND r.charttime > l.landmark_time
       AND r.charttime <= l.landmark_time + INTERVAL '48 hour'
    GROUP BY l.stay_id, l.landmark_time
)
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
FROM saki_dynamic.landmarks_raw l
LEFT JOIN current_kdigo ck
    ON l.stay_id = ck.stay_id
   AND l.landmark_time = ck.landmark_time
LEFT JOIN prior_kdigo pk
    ON l.stay_id = pk.stay_id
   AND l.landmark_time = pk.landmark_time
LEFT JOIN prior_rrt pr
    ON l.stay_id = pr.stay_id
   AND l.landmark_time = pr.landmark_time
LEFT JOIN future_kdigo fk
    ON l.stay_id = fk.stay_id
   AND l.landmark_time = fk.landmark_time
LEFT JOIN future_rrt fr
    ON l.stay_id = fr.stay_id
   AND l.landmark_time = fr.landmark_time;

DROP TABLE IF EXISTS saki_dynamic.landmarks;
CREATE TABLE saki_dynamic.landmarks AS
SELECT *
FROM saki_dynamic.landmark_status
WHERE landmark_time <= icu_outtime
  AND landmark_time + INTERVAL '48 hour' <= icu_outtime
  AND current_kdigo IN (1, 2)
  AND COALESCE(prior_rrt, 0) = 0;

-- Optional sanity checks:
-- SELECT landmark_hour, COUNT(*) AS n, AVG(aki_progression_48h::numeric) AS event_rate
-- FROM saki_dynamic.landmarks
-- GROUP BY landmark_hour
-- ORDER BY landmark_hour;
