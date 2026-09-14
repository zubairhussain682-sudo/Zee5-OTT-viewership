-- MART AUDIT: profile_viewership_window | Test 3C - title concentration and breadth
-- Question:        Do top-title share and title HHI reproduce the title mart, and are breadth and
--                  concentration separate signals once HHI's breadth-dependent floor is accounted for?
-- Why it matters:  HHI = sum of squared qualified-minute shares across meaningful titles. Its minimum is
--                  1/n for n titles, so raw HHI falls with breadth for arithmetic reasons alone. Reading it
--                  as a breadth-independent trait would mistake a mathematical floor for behaviour.
-- Analytical use:  (1) Rebuilds qualified minutes, meaningful-title counts, top-title minutes and share,
--                  title HHI and HHI validity (>= 3 meaningful titles) from profile_title_window; mismatch
--                  counts are expected 0, with a 0.000001 tolerance on floating-point quantities.
--                  (2) Describes breadth and concentration for eligible profiles with valid HHI.
--                  (3) Compares concentration among profiles with exactly the same meaningful-title count,
--                  using nearest-rank percentiles (value at rank CEIL(q * N)) and only breadth groups of at
--                  least 30 profiles. Adjusted HHI = (HHI - 1/n) / (1 - 1/n) and adjusted top dominance
--                  apply the same rescaling to top-title share; both are exploratory Test 3 diagnostics,
--                  not canonical measures. HHI describes concentration; it does not explain it.
-- SELECT-only. Select the intended database before running.

WITH title_rows AS (
    SELECT window_label, profile_id, is_meaningful_title, qualified_watch_minutes,
           CASE WHEN qualified_watch_minutes > 0
                THEN qualified_watch_minutes
                     / SUM(qualified_watch_minutes) OVER (PARTITION BY window_label, profile_id)
           END AS share
    FROM profile_title_window
),
rebuilt AS (
    SELECT window_label, profile_id,
           SUM(qualified_watch_minutes)                                        AS qualified_minutes,
           SUM(CASE WHEN is_meaningful_title = 0 THEN qualified_watch_minutes ELSE 0 END)
                                                                               AS minutes_outside_meaningful,
           SUM(is_meaningful_title)                                            AS meaningful_titles,
           MAX(CASE WHEN qualified_watch_minutes > 0 THEN qualified_watch_minutes END) AS top_title_minutes,
           MAX(share)                                                          AS top_title_share,
           SUM(share * share)                                                  AS title_hhi
    FROM title_rows
    GROUP BY window_label, profile_id
)
SELECT pv.window_label,
       SUM(ABS(pv.qualified_watch_minutes - COALESCE(r.qualified_minutes, 0)) > 0.000001)
                                                                        AS qualified_minutes_mismatches,
       SUM(COALESCE(r.minutes_outside_meaningful, 0) > 0)               AS minutes_outside_meaningful_titles,
       SUM(pv.n_meaningful_titles <> COALESCE(r.meaningful_titles, 0))   AS meaningful_title_count_mismatches,
       SUM(NOT ((pv.top_title_qualified_minutes IS NULL) <=> (r.top_title_minutes IS NULL))
           OR ABS(pv.top_title_qualified_minutes - r.top_title_minutes) > 0.000001)
                                                                        AS top_title_minutes_mismatches,
       SUM(NOT ((pv.top_title_qualified_share IS NULL) <=> (r.top_title_share IS NULL))
           OR ABS(pv.top_title_qualified_share - r.top_title_share) > 0.000001)
                                                                        AS top_title_share_mismatches,
       SUM(pv.hhi_is_valid = 1 AND ABS(pv.title_hhi - r.title_hhi) > 0.000001) AS title_hhi_mismatches,
       SUM(pv.hhi_is_valid <> (COALESCE(r.meaningful_titles, 0) >= 3))  AS hhi_validity_mismatches,
       SUM((pv.title_hhi IS NULL) = (pv.hhi_is_valid = 1))              AS hhi_null_state_mismatches
FROM profile_viewership_window pv
LEFT JOIN rebuilt r
       ON r.window_label = pv.window_label AND r.profile_id = pv.profile_id
GROUP BY pv.window_label
ORDER BY pv.window_label;

SELECT window_label,
       COUNT(*)                                                        AS profiles,
       MIN(n_meaningful_titles)                                        AS min_meaningful_titles,
       ROUND(AVG(n_meaningful_titles), 2)                              AS avg_meaningful_titles,
       MAX(n_meaningful_titles)                                        AS max_meaningful_titles,
       ROUND(AVG(top_title_qualified_share), 4)                        AS avg_top_title_share,
       ROUND(AVG((top_title_qualified_share - 1.0e0 / n_meaningful_titles)
                 / (1 - 1.0e0 / n_meaningful_titles)), 4)              AS avg_adjusted_top_dominance,
       ROUND(AVG(title_hhi), 4)                                        AS avg_raw_hhi,
       ROUND(AVG((title_hhi - 1.0e0 / n_meaningful_titles)
                 / (1 - 1.0e0 / n_meaningful_titles)), 4)              AS avg_adjusted_hhi,
       ROUND(AVG(qualified_watch_hours), 2)                            AS avg_qualified_watch_hours
FROM profile_viewership_window
WHERE is_main_analytical_eligible = 1 AND hhi_is_valid = 1
GROUP BY window_label
ORDER BY window_label;

WITH eligible AS (
    SELECT window_label, n_meaningful_titles AS n, title_hhi, top_title_qualified_share AS top_share,
           (title_hhi - 1.0e0 / n_meaningful_titles) / (1 - 1.0e0 / n_meaningful_titles) AS adjusted_hhi
    FROM profile_viewership_window
    WHERE is_main_analytical_eligible = 1 AND hhi_is_valid = 1
),
ranked AS (
    SELECT eligible.*,
           COUNT(*)     OVER (PARTITION BY window_label, n)                        AS profiles,
           ROW_NUMBER() OVER (PARTITION BY window_label, n ORDER BY title_hhi)     AS rn_hhi,
           ROW_NUMBER() OVER (PARTITION BY window_label, n ORDER BY top_share)     AS rn_top,
           ROW_NUMBER() OVER (PARTITION BY window_label, n ORDER BY adjusted_hhi)  AS rn_adjusted
    FROM eligible
)
SELECT window_label,
       n                                                                   AS n_meaningful_titles,
       MAX(profiles)                                                       AS profiles,
       1.0e0 / n                                                           AS hhi_floor,
       MAX(CASE WHEN rn_hhi      = CEIL(0.5 * profiles) THEN title_hhi END)    AS median_raw_hhi,
       MAX(CASE WHEN rn_top      = CEIL(0.5 * profiles) THEN top_share END)    AS median_top_title_share,
       MAX(CASE WHEN rn_top      = CEIL(0.9 * profiles) THEN top_share END)    AS p90_top_title_share,
       MAX(CASE WHEN rn_adjusted = CEIL(0.5 * profiles) THEN adjusted_hhi END) AS median_adjusted_hhi,
       MAX(CASE WHEN rn_adjusted = CEIL(0.9 * profiles) THEN adjusted_hhi END) AS p90_adjusted_hhi
FROM ranked
GROUP BY window_label, n
HAVING MAX(profiles) >= 30
ORDER BY window_label, n;
