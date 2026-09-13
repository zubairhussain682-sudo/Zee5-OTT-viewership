-- MART AUDIT: profile_viewership_window | Test 2A-2B - activity, volume and session measures
-- Question:        Do the activity, volume and session fields describe viewing coherently, and what
--                  shape does activity take in each window?
-- Why it matters:  Depth, frequency and habit measures will be derived from these fields. If sessions
--                  could outnumber events, or summaries appeared on rows with no sessions, later
--                  behavioural features would inherit contradictions that look like behaviour.
-- Analytical use:  Describes each window's activity shape (descriptive only, no mechanism implied)
--                  and counts violations of the relationships the fields must respect.
-- SELECT-only. Select the intended database before running.

-- 2A. Descriptive shape. Per-profile averages cover profiles with any playback; session summary
-- fields are NULL for profiles without sessions and so drop out of their averages naturally.
SELECT window_label,
       COUNT(*)                                                     AS profiles,
       SUM(events > 0)                                              AS active_profiles,
       ROUND(SUM(watch_minutes), 2)                                 AS total_watch_minutes,
       ROUND(SUM(qualified_watch_minutes), 2)                       AS total_qualified_watch_minutes,
       ROUND(SUM(qualified_watch_minutes) / SUM(watch_minutes), 4)  AS qualified_watch_share,
       SUM(events)                                                  AS total_events,
       SUM(autoplay_events)                                         AS total_autoplay_events,
       SUM(sessions)                                                AS total_sessions,
       ROUND(AVG(CASE WHEN events > 0 THEN watch_minutes END), 2)           AS avg_watch_minutes,
       ROUND(AVG(CASE WHEN events > 0 THEN qualified_watch_minutes END), 2) AS avg_qualified_minutes,
       ROUND(AVG(CASE WHEN events > 0 THEN active_days END), 2)             AS avg_active_days,
       ROUND(AVG(CASE WHEN events > 0 THEN sessions END), 2)                AS avg_sessions,
       ROUND(AVG(mean_session_minutes), 2)                          AS avg_profile_mean_session_minutes,
       ROUND(AVG(median_session_minutes), 2)                        AS avg_profile_median_session_minutes,
       ROUND(AVG(sessions_per_active_day), 2)                       AS avg_sessions_per_active_day
FROM profile_viewership_window
GROUP BY window_label
ORDER BY window_label;

-- 2B. Internal invariants (expected: every count is 0). Derived conversions use the same
-- 0.000001 tolerance applied in the reviewed audit. first_event_ts and last_event_ts are the
-- earliest and latest event START timestamps, so their ordering is checked on starts only.
SELECT window_label,
       SUM(autoplay_events > events)                                    AS autoplay_above_events,
       SUM(qualified_starts > events)                                   AS qualified_starts_above_events,
       SUM(sessions > events)                                           AS sessions_above_events,
       SUM(active_days > window_days)                                   AS active_days_above_window,
       SUM(qualified_active_days > active_days)                         AS qualified_days_above_active_days,
       SUM(ABS(watch_hours - watch_minutes / 60.0e0) > 0.000001)        AS watch_hours_conversion,
       SUM(ABS(qualified_watch_hours - qualified_watch_minutes / 60.0e0) > 0.000001)
                                                                        AS qualified_hours_conversion,
       SUM((active_days > 0
            AND (sessions_per_active_day IS NULL
                 OR ABS(sessions_per_active_day - sessions * 1.0e0 / active_days) > 0.000001))
           OR (active_days = 0 AND sessions_per_active_day IS NOT NULL))
                                                                        AS sessions_per_active_day_derivation,
       SUM(sessions = 0
           AND (session_minutes <> 0 OR mean_session_minutes IS NOT NULL
                OR median_session_minutes IS NOT NULL OR max_session_minutes IS NOT NULL))
                                                                        AS zero_session_rows_with_summaries,
       SUM(sessions > 0
           AND (mean_session_minutes IS NULL OR median_session_minutes IS NULL
                OR max_session_minutes IS NULL))                        AS session_rows_missing_summaries,
       SUM(sessions > 0
           AND (mean_session_minutes   > max_session_minutes + 0.000001
                OR median_session_minutes > max_session_minutes + 0.000001
                OR max_session_minutes > session_minutes + 0.000001))   AS session_summary_order,
       SUM(first_event_ts > last_event_ts)                              AS timestamps_out_of_order,
       SUM(events = 0 AND (first_event_ts IS NOT NULL OR last_event_ts IS NOT NULL))
                                                                        AS timestamps_on_no_playback_rows,
       SUM(events > 0 AND (first_event_ts IS NULL OR last_event_ts IS NULL))
                                                                        AS active_rows_missing_timestamps
FROM profile_viewership_window
GROUP BY window_label
ORDER BY window_label;
