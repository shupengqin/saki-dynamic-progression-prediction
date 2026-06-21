-- eICU landmark and future 48-hour AKI progression outcome.

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

DROP TABLE IF EXISTS saki_eicu.landmark_status;
CREATE TABLE saki_eicu.landmark_status AS
WITH current_kdigo AS (
    SELECT
        l.stay_id,
        l.landmark_offset,
        MAX(k.aki_stage) AS current_or_prior_max_kdigo,
        (
            SELECT k2.aki_stage
            FROM saki_eicu.kdigo_timeline k2
            WHERE k2.stay_id = l.stay_id
              AND k2.chart_offset <= l.landmark_offset
            ORDER BY k2.chart_offset DESC
            LIMIT 1
        ) AS current_kdigo
    FROM saki_eicu.landmarks_raw l
    LEFT JOIN saki_eicu.kdigo_timeline k
        ON l.stay_id = k.stay_id
       AND k.chart_offset <= l.landmark_offset
    GROUP BY l.stay_id, l.landmark_offset
),
prior_rrt AS (
    SELECT
        l.stay_id,
        l.landmark_offset,
        MAX(CASE WHEN r.rrt = 1 THEN 1 ELSE 0 END) AS prior_rrt
    FROM saki_eicu.landmarks_raw l
    LEFT JOIN saki_eicu.rrt_events r
        ON l.stay_id = r.stay_id
       AND r.chart_offset <= l.landmark_offset
    GROUP BY l.stay_id, l.landmark_offset
),
future_kdigo AS (
    SELECT
        l.stay_id,
        l.landmark_offset,
        MAX(k.aki_stage) AS future_max_kdigo
    FROM saki_eicu.landmarks_raw l
    LEFT JOIN saki_eicu.kdigo_timeline k
        ON l.stay_id = k.stay_id
       AND k.chart_offset > l.landmark_offset
       AND k.chart_offset <= l.landmark_offset + 2880
    GROUP BY l.stay_id, l.landmark_offset
),
future_rrt AS (
    SELECT
        l.stay_id,
        l.landmark_offset,
        MAX(CASE WHEN r.rrt = 1 THEN 1 ELSE 0 END) AS future_rrt
    FROM saki_eicu.landmarks_raw l
    LEFT JOIN saki_eicu.rrt_events r
        ON l.stay_id = r.stay_id
       AND r.chart_offset > l.landmark_offset
       AND r.chart_offset <= l.landmark_offset + 2880
    GROUP BY l.stay_id, l.landmark_offset
)
SELECT
    l.*,
    ck.current_kdigo,
    ck.current_or_prior_max_kdigo,
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
LEFT JOIN current_kdigo ck
    ON l.stay_id = ck.stay_id
   AND l.landmark_offset = ck.landmark_offset
LEFT JOIN prior_rrt pr
    ON l.stay_id = pr.stay_id
   AND l.landmark_offset = pr.landmark_offset
LEFT JOIN future_kdigo fk
    ON l.stay_id = fk.stay_id
   AND l.landmark_offset = fk.landmark_offset
LEFT JOIN future_rrt fr
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

