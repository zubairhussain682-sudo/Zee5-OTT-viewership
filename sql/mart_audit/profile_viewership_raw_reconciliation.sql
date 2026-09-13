-- MART AUDIT: profile_viewership_window | Test 2C-2D - reconciliation with raw playback
-- Question:        Can the mart's activity and session measures be rebuilt independently from
--                  viewing_sessions and view_events?
-- Why it matters:  Agreement with raw playback is what makes later statements about depth, habit
--                  and recency trustworthy. Disagreement would mean a grain, window or aggregation
--                  error sitting underneath every behavioural measure.
-- Analytical use:  Counts and timestamps must match exactly. Minute differences are inspected in
--                  tolerance bands. In this audit, sub-0.001-minute differences are treated as
--                  numerical residue only after exact count/timestamp reconciliation and inspection
--                  of their magnitude and direction.
-- SELECT-only. Select the intended database before running.
--
-- Events belong to a window by event_start_ts and sessions by session_start_ts, using the half-open
-- interval [window_start, window_end + 1 day). Watch minutes (playback summed over events) and
-- session minutes (elapsed session time) are different constructs and are never compared to each other.

-- 2C. Events: exact counts and timestamps, banded watch minutes.
WITH windows AS (
    SELECT DISTINCT window_label, window_start, window_end
    FROM profile_viewership_window
),
raw_events AS (
    SELECT w.window_label, s.profile_id,
           COUNT(*)                               AS events,
           SUM(e.is_autoplay)                     AS autoplay_events,
           COUNT(DISTINCT DATE(e.event_start_ts)) AS active_days,
           MIN(e.event_start_ts)                  AS first_event_start,
           MAX(e.event_start_ts)                  AS last_event_start,
           SUM(e.watch_seconds) / 60              AS watch_minutes
    FROM view_events e
    JOIN viewing_sessions s ON s.session_id = e.session_id
    JOIN windows w
      ON e.event_start_ts >= w.window_start
     AND e.event_start_ts <  w.window_end + INTERVAL 1 DAY
    GROUP BY w.window_label, s.profile_id
),
compared AS (
    SELECT pv.window_label,
           pv.events          <> COALESCE(r.events, 0)          AS event_mismatch,
           pv.autoplay_events <> COALESCE(r.autoplay_events, 0) AS autoplay_mismatch,
           pv.active_days     <> COALESCE(r.active_days, 0)     AS active_day_mismatch,
           NOT (pv.first_event_ts <=> r.first_event_start)       AS first_ts_mismatch,
           NOT (pv.last_event_ts  <=> r.last_event_start)        AS last_ts_mismatch,
           pv.watch_minutes - COALESCE(r.watch_minutes, 0)       AS watch_diff
    FROM profile_viewership_window pv
    LEFT JOIN raw_events r
           ON r.window_label = pv.window_label AND r.profile_id = pv.profile_id
)
SELECT window_label,
       COUNT(*)                        AS profiles,
       SUM(event_mismatch)             AS event_count_mismatches,
       SUM(autoplay_mismatch)          AS autoplay_mismatches,
       SUM(active_day_mismatch)        AS active_day_mismatches,
       SUM(first_ts_mismatch)          AS first_event_ts_mismatches,
       SUM(last_ts_mismatch)           AS last_event_ts_mismatches,
       SUM(ABS(watch_diff) > 0.000001) AS watch_diff_above_0_000001_min,
       SUM(ABS(watch_diff) > 0.001)    AS watch_diff_above_0_001_min,
       SUM(ABS(watch_diff) > 0.01)     AS watch_diff_above_0_01_min,
       SUM(ABS(watch_diff) > 0.1)      AS watch_diff_above_0_1_min,
       SUM(ABS(watch_diff) > 1)        AS watch_diff_above_1_min,
       MAX(ABS(watch_diff))            AS max_abs_watch_diff,
       AVG(ABS(watch_diff))            AS avg_abs_watch_diff,
       SUM(ABS(watch_diff))            AS total_abs_watch_diff,
       SUM(watch_diff)                 AS net_signed_watch_diff
FROM compared
GROUP BY window_label
ORDER BY window_label;

-- 2D. Sessions: exact counts, banded elapsed durations. The median is rebuilt explicitly because
-- MySQL has no MEDIAN aggregate; with an even number of sessions it averages the two middle values.
WITH windows AS (
    SELECT DISTINCT window_label, window_start, window_end
    FROM profile_viewership_window
),
raw_sessions AS (
    SELECT w.window_label, s.profile_id,
           TIMESTAMPDIFF(MICROSECOND, s.session_start_ts, s.session_end_ts) / 60000000 AS elapsed_minutes
    FROM viewing_sessions s
    JOIN windows w
      ON s.session_start_ts >= w.window_start
     AND s.session_start_ts <  w.window_end + INTERVAL 1 DAY
),
ranked AS (
    SELECT window_label, profile_id, elapsed_minutes,
           ROW_NUMBER() OVER (PARTITION BY window_label, profile_id ORDER BY elapsed_minutes) AS rn,
           COUNT(*)     OVER (PARTITION BY window_label, profile_id)                          AS n
    FROM raw_sessions
),
rebuilt AS (
    SELECT window_label, profile_id,
           COUNT(*)             AS sessions,
           SUM(elapsed_minutes) AS session_minutes,
           AVG(elapsed_minutes) AS mean_minutes,
           AVG(CASE WHEN rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2)) THEN elapsed_minutes END)
                                AS median_minutes,
           MAX(elapsed_minutes) AS max_minutes
    FROM ranked
    GROUP BY window_label, profile_id
),
compared AS (
    SELECT pv.window_label,
           pv.sessions <> COALESCE(rb.sessions, 0)                   AS count_mismatch,
           ABS(pv.session_minutes - COALESCE(rb.session_minutes, 0)) AS total_diff,
           ABS(pv.mean_session_minutes   - rb.mean_minutes)          AS mean_diff,
           ABS(pv.median_session_minutes - rb.median_minutes)        AS median_diff,
           ABS(pv.max_session_minutes    - rb.max_minutes)           AS max_diff
    FROM profile_viewership_window pv
    LEFT JOIN rebuilt rb
           ON rb.window_label = pv.window_label AND rb.profile_id = pv.profile_id
)
SELECT window_label,
       SUM(count_mismatch)          AS session_count_mismatches,
       SUM(total_diff  > 0.000001)  AS total_minutes_above_0_000001,
       SUM(mean_diff   > 0.000001)  AS mean_minutes_above_0_000001,
       SUM(median_diff > 0.000001)  AS median_minutes_above_0_000001,
       SUM(max_diff    > 0.000001)  AS max_minutes_above_0_000001,
       SUM(total_diff > 0.001 OR mean_diff > 0.001 OR median_diff > 0.001 OR max_diff > 0.001)
                                    AS any_duration_above_0_001,
       MAX(total_diff)              AS max_total_minutes_diff,
       MAX(mean_diff)               AS max_mean_minutes_diff,
       MAX(median_diff)             AS max_median_minutes_diff,
       MAX(max_diff)                AS max_longest_session_diff
FROM compared
GROUP BY window_label
ORDER BY window_label;
