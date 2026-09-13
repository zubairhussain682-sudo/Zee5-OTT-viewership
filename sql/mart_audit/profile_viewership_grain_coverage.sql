-- MART AUDIT: profile_viewership_window | Test 1 - grain, coverage and row semantics
-- Question:        Does each row mean one profile in one window, and does the mart keep every
--                  profile whether or not it watched anything?
-- Why it matters:  Dropping profiles that watched nothing would hide the gap between access and
--                  demand. A row that contradicts itself - qualified viewing above total viewing,
--                  meaningful titles without a qualified start - would corrupt every measure built on it.
-- Analytical use:  Confirms full profile x window coverage, shows how raw activity, qualified
--                  engagement and analytical eligibility separate, and counts semantic contradictions.
-- SELECT-only. Select the intended database before running.

-- One row per profile and window (expected: no rows).
SELECT profile_id, window_label, COUNT(*) AS rows_at_grain
FROM profile_viewership_window
GROUP BY profile_id, window_label
HAVING COUNT(*) > 1;

-- Every profile appears in both windows, including profiles with no playback (expected: no rows).
SELECT p.profile_id,
       b.profile_id IS NOT NULL AS in_baseline,
       f.profile_id IS NOT NULL AS in_final
FROM profiles p
LEFT JOIN profile_viewership_window b
       ON b.profile_id = p.profile_id AND b.window_label = 'BASELINE_90'
LEFT JOIN profile_viewership_window f
       ON f.profile_id = p.profile_id AND f.window_label = 'FINAL_90'
WHERE b.profile_id IS NULL OR f.profile_id IS NULL;

-- Row states. Playback, qualified engagement and eligibility are nested but distinct:
-- eligibility is a test of evidence sufficiency, not a behavioural state.
SELECT window_label,
       MIN(window_start)                        AS window_start,
       MAX(window_end)                          AS window_end,
       COUNT(*)                                 AS profile_rows,
       COUNT(DISTINCT profile_id)               AS distinct_profiles,
       SUM(events = 0)                          AS no_playback,
       SUM(events > 0 AND qualified_starts = 0) AS playback_without_qualified_start,
       SUM(qualified_starts > 0)                AS with_qualified_start,
       SUM(distinct_meaningful_titles = 0)      AS no_meaningful_title,
       SUM(is_main_analytical_eligible)         AS analytically_eligible
FROM profile_viewership_window
GROUP BY window_label
ORDER BY window_label;

-- Semantic contradictions (expected: every count is 0). These are logical state checks;
-- no tolerance is needed because the reviewed audit found no contradictions.
SELECT pv.window_label,
       SUM(pv.qualified_watch_minutes > pv.watch_minutes)               AS qualified_minutes_above_total,
       SUM(pv.qualified_active_days > pv.active_days)                   AS qualified_days_above_active_days,
       SUM(pv.distinct_meaningful_titles > pv.distinct_parent_titles)   AS meaningful_titles_above_titles,
       SUM(pv.distinct_meaningful_titles <> pv.n_meaningful_titles
           OR pv.distinct_meaningful_titles <> COALESCE(pt.meaningful_titles, 0))
                                                                        AS meaningful_title_fields_disagree,
       SUM(pv.events = 0
           AND (pv.watch_minutes <> 0 OR pv.active_days <> 0 OR pv.sessions <> 0
                OR pv.qualified_starts <> 0 OR pv.first_event_ts IS NOT NULL))
                                                                        AS no_playback_rows_with_activity,
       SUM(pv.qualified_starts = 0 AND pv.distinct_meaningful_titles > 0)
                                                                        AS meaningful_titles_without_qualified_start
FROM profile_viewership_window pv
LEFT JOIN (
    SELECT profile_id, window_label, SUM(is_meaningful_title) AS meaningful_titles
    FROM profile_title_window
    GROUP BY profile_id, window_label
) pt ON pt.profile_id = pv.profile_id AND pt.window_label = pv.window_label
GROUP BY pv.window_label
ORDER BY pv.window_label;
