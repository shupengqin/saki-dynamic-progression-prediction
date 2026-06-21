-- Faster materialized eICU landmark/outcome construction.

DROP TABLE IF EXISTS saki_eicu.landmarks_raw;
CREATE TABLE saki_eicu.landmarks_raw AS
SELECT *, saki_onset_offset + 1440 AS landmark_offset, 24 AS landmark_hour
FROM saki_eicu.saki_onset
UNION ALL
SELECT *, saki_onset_offset + 2880 AS landmark_offset, 48 AS landmark_hour
FROM saki_eicu.saki_onset
UNION ALL
SELECT *, saki_onset_offset + 4320 AS landmark_offset, 72 AS landmark_hour
FROM saki_eicu.saki_onset;

CREATE INDEX IF NOT EXISTS idx_saki_eicu_landmarks_raw_stay_time
    ON saki_eicu.landmarks_raw (stay_id, landmark_offset);
CREATE INDEX IF NOT EXISTS idx_saki_eicu_kdigo_timeline_stay_time
    ON saki_eicu.kdigo_timeline (stay_id, chart_offset);
CREATE INDEX IF NOT EXISTS idx_saki_eicu_rrt_events_stay_time
    ON saki_eicu.rrt_events (stay_id, chart_offset);

DROP TABLE IF EXISTS saki_eicu.kdigo_window;
CREATE TABLE saki_eicu.kdigo_window AS
SELECT
    l.stay_id,
    l.landmark_offset,
    k.chart_offset,
    k.aki_stage
FROM saki_eicu.landmarks_raw l
INNER JOIN saki_eicu.kdigo_timeline k
    ON l.stay_id = k.stay_id
   AND k.chart_offset <= l.landmark_offset + 2880;

CREATE INDEX IF NOT EXISTS idx_saki_eicu_kdigo_window_key
    ON saki_eicu.kdigo_window (stay_id, landmark_offset, chart_offset);

DROP TABLE IF EXISTS saki_eicu.rrt_window;
CREATE TABLE saki_eicu.rrt_window AS
SELECT
    l.stay_id,
    l.landmark_offset,
    r.chart_offset,
    r.rrt
FROM saki_eicu.landmarks_raw l
INNER JOIN saki_eicu.rrt_events r
    ON l.stay_id = r.stay_id
   AND r.chart_offset <= l.landmark_offset + 2880;

CREATE INDEX IF NOT EXISTS idx_saki_eicu_rrt_window_key
    ON saki_eicu.rrt_window (stay_id, landmark_offset, chart_offset);

DROP TABLE IF EXISTS saki_eicu.current_kdigo;
CREATE TABLE saki_eicu.current_kdigo AS
SELECT DISTINCT ON (stay_id, landmark_offset)
    stay_id,
    landmark_offset,
    aki_stage AS current_kdigo
FROM saki_eicu.kdigo_window
WHERE chart_offset <= landmark_offset
ORDER BY stay_id, landmark_offset, chart_offset DESC;

DROP TABLE IF EXISTS saki_eicu.prior_kdigo;
CREATE TABLE saki_eicu.prior_kdigo AS
SELECT
    stay_id,
    landmark_offset,
    MAX(aki_stage) AS current_or_prior_max_kdigo
FROM saki_eicu.kdigo_window
WHERE chart_offset <= landmark_offset
GROUP BY stay_id, landmark_offset;

DROP TABLE IF EXISTS saki_eicu.prior_rrt;
CREATE TABLE saki_eicu.prior_rrt AS
SELECT
    stay_id,
    landmark_offset,
    MAX(rrt) AS prior_rrt
FROM saki_eicu.rrt_window
WHERE chart_offset <= landmark_offset
GROUP BY stay_id, landmark_offset;

DROP TABLE IF EXISTS saki_eicu.future_kdigo;
CREATE TABLE saki_eicu.future_kdigo AS
SELECT
    stay_id,
    landmark_offset,
    MAX(aki_stage) AS future_max_kdigo
FROM saki_eicu.kdigo_window
WHERE chart_offset > landmark_offset
  AND chart_offset <= landmark_offset + 2880
GROUP BY stay_id, landmark_offset;

DROP TABLE IF EXISTS saki_eicu.future_rrt;
CREATE TABLE saki_eicu.future_rrt AS
SELECT
    stay_id,
    landmark_offset,
    MAX(rrt) AS future_rrt
FROM saki_eicu.rrt_window
WHERE chart_offset > landmark_offset
  AND chart_offset <= landmark_offset + 2880
GROUP BY stay_id, landmark_offset;

DROP TABLE IF EXISTS saki_eicu.landmark_status;
CREATE TABLE saki_eicu.landmark_status AS
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
FROM saki_eicu.landmarks_raw l
LEFT JOIN saki_eicu.current_kdigo ck
    ON l.stay_id = ck.stay_id
   AND l.landmark_offset = ck.landmark_offset
LEFT JOIN saki_eicu.prior_kdigo pk
    ON l.stay_id = pk.stay_id
   AND l.landmark_offset = pk.landmark_offset
LEFT JOIN saki_eicu.prior_rrt pr
    ON l.stay_id = pr.stay_id
   AND l.landmark_offset = pr.landmark_offset
LEFT JOIN saki_eicu.future_kdigo fk
    ON l.stay_id = fk.stay_id
   AND l.landmark_offset = fk.landmark_offset
LEFT JOIN saki_eicu.future_rrt fr
    ON l.stay_id = fr.stay_id
   AND l.landmark_offset = fr.landmark_offset;

DROP TABLE IF EXISTS saki_eicu.landmarks;
CREATE TABLE saki_eicu.landmarks AS
SELECT *
FROM saki_eicu.landmark_status
WHERE landmark_offset <= unitdischargeoffset
  AND landmark_offset + 2880 <= unitdischargeoffset
  AND current_kdigo IN (1, 2)
  AND COALESCE(prior_rrt, 0) = 0;

SELECT
    landmark_hour,
    COUNT(*) AS n,
    AVG(aki_progression_48h::numeric) AS event_rate
FROM saki_eicu.landmarks
GROUP BY landmark_hour
ORDER BY landmark_hour;

