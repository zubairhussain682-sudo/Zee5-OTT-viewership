-- VIEWER DIAGNOSIS: profile_viewership_window | Test 4D.3 - breadth x concentration with separate activity controls
-- Question:        Do profiles with similar breadth and concentration respond differently after choosing content,
--                  once each is compared with viewers of similar activity?
-- Why it matters:  More watch hours or active days give more chances to accumulate titles, completions and
--                  replays, so raw differences between breadth x concentration cells may only reflect volume.
-- Analytical use:  Places eligible profiles with a meaningful title in within-window concentration (top-title
--                  share) and breadth (meaningful titles) quintiles; NTILE ties are broken by profile_id.
--                  Completion uses the known-outcome denominator (>= 5 known outcomes). 14-day replay needs the
--                  profile-level table audit_profile_rewatch14 (>= 3 known outcomes), written locally by
--                  scripts/diagnostics/rewatch_observability.py and not published. Each profile is compared
--                  separately with the window average for its watch-hours quintile and for its active-days
--                  quintile; a cell's direction is robust only when both deviations share a sign. Cells under 30
--                  profiles are flagged THIN_CELL.
--                  Output rows are candidate behavioural states, not segments, identities or headroom.
-- SELECT-only apart from reading the locally imported audit_profile_rewatch14 table.

WITH base AS (
    SELECT
        pv.profile_id,
        pv.window_label,
        pv.distinct_meaningful_titles,
        pv.top_title_qualified_share,
        pv.qualified_watch_hours,
        pv.active_days,
        pv.abandonment_known_denominator,
        pv.completed_asset_starts,
        CASE
            WHEN pv.abandonment_known_denominator >= 5
            THEN pv.completed_asset_starts * 1.0 / pv.abandonment_known_denominator
        END AS completion_known_rate,
        rw.rewatch_14d_known_denominator,
        CASE
            WHEN rw.rewatch_14d_known_denominator >= 3
            THEN rw.rewatch_14d_rate
        END AS rewatch_14d_rate
    FROM profile_viewership_window pv
    LEFT JOIN audit_profile_rewatch14 rw
      ON rw.profile_id = pv.profile_id
     AND rw.window_label = pv.window_label
    WHERE pv.is_main_analytical_eligible = 1
      AND pv.distinct_meaningful_titles > 0
      AND pv.top_title_qualified_share IS NOT NULL
), ranked AS (
    SELECT
        base.*,
        NTILE(5) OVER (
            PARTITION BY window_label
            ORDER BY top_title_qualified_share, profile_id
        ) AS concentration_quintile,
        NTILE(5) OVER (
            PARTITION BY window_label
            ORDER BY distinct_meaningful_titles, profile_id
        ) AS breadth_quintile,
        NTILE(5) OVER (
            PARTITION BY window_label
            ORDER BY qualified_watch_hours, profile_id
        ) AS watch_hours_quintile,
        NTILE(5) OVER (
            PARTITION BY window_label
            ORDER BY active_days, profile_id
        ) AS active_days_quintile
    FROM base
), completion_watch_benchmark AS (
    SELECT
        window_label,
        watch_hours_quintile,
        AVG(completion_known_rate) AS benchmark_rate,
        COUNT(completion_known_rate) AS benchmark_n
    FROM ranked
    GROUP BY window_label, watch_hours_quintile
), completion_day_benchmark AS (
    SELECT
        window_label,
        active_days_quintile,
        AVG(completion_known_rate) AS benchmark_rate,
        COUNT(completion_known_rate) AS benchmark_n
    FROM ranked
    GROUP BY window_label, active_days_quintile
), replay_watch_benchmark AS (
    SELECT
        window_label,
        watch_hours_quintile,
        AVG(rewatch_14d_rate) AS benchmark_rate,
        COUNT(rewatch_14d_rate) AS benchmark_n
    FROM ranked
    GROUP BY window_label, watch_hours_quintile
), replay_day_benchmark AS (
    SELECT
        window_label,
        active_days_quintile,
        AVG(rewatch_14d_rate) AS benchmark_rate,
        COUNT(rewatch_14d_rate) AS benchmark_n
    FROM ranked
    GROUP BY window_label, active_days_quintile
), scored AS (
    SELECT
        r.*,
        cw.benchmark_rate AS completion_watch_benchmark,
        cw.benchmark_n AS completion_watch_benchmark_n,
        cd.benchmark_rate AS completion_day_benchmark,
        cd.benchmark_n AS completion_day_benchmark_n,
        rw.benchmark_rate AS replay_watch_benchmark,
        rw.benchmark_n AS replay_watch_benchmark_n,
        rd.benchmark_rate AS replay_day_benchmark,
        rd.benchmark_n AS replay_day_benchmark_n,
        r.completion_known_rate - cw.benchmark_rate AS completion_watch_residual,
        r.completion_known_rate - cd.benchmark_rate AS completion_day_residual,
        r.rewatch_14d_rate - rw.benchmark_rate AS replay_watch_residual,
        r.rewatch_14d_rate - rd.benchmark_rate AS replay_day_residual
    FROM ranked r
    JOIN completion_watch_benchmark cw
      ON cw.window_label = r.window_label
     AND cw.watch_hours_quintile = r.watch_hours_quintile
    JOIN completion_day_benchmark cd
      ON cd.window_label = r.window_label
     AND cd.active_days_quintile = r.active_days_quintile
    JOIN replay_watch_benchmark rw
      ON rw.window_label = r.window_label
     AND rw.watch_hours_quintile = r.watch_hours_quintile
    JOIN replay_day_benchmark rd
      ON rd.window_label = r.window_label
     AND rd.active_days_quintile = r.active_days_quintile
), completion_cells AS (
    SELECT
        'completion' AS metric,
        window_label,
        concentration_quintile,
        breadth_quintile,
        COUNT(*) AS profiles,
        AVG(distinct_meaningful_titles) AS avg_meaningful_titles,
        AVG(top_title_qualified_share) AS avg_top_title_share,
        AVG(qualified_watch_hours) AS avg_watch_hours,
        AVG(active_days) AS avg_active_days,
        COUNT(completion_known_rate) AS profiles_measured,
        SUM(CASE WHEN completion_known_rate IS NOT NULL THEN abandonment_known_denominator ELSE 0 END) AS known_outcomes,
        AVG(completion_known_rate) AS raw_avg_rate,
        AVG(completion_watch_residual) AS deviation_vs_watch_context,
        AVG(CASE WHEN completion_known_rate IS NOT NULL THEN completion_known_rate > completion_watch_benchmark END) AS share_above_watch_context,
        MIN(CASE WHEN completion_known_rate IS NOT NULL THEN completion_watch_benchmark_n END) AS min_watch_benchmark_n,
        AVG(completion_day_residual) AS deviation_vs_active_day_context,
        AVG(CASE WHEN completion_known_rate IS NOT NULL THEN completion_known_rate > completion_day_benchmark END) AS share_above_active_day_context,
        MIN(CASE WHEN completion_known_rate IS NOT NULL THEN completion_day_benchmark_n END) AS min_active_day_benchmark_n
    FROM scored
    GROUP BY window_label, concentration_quintile, breadth_quintile
), replay_cells AS (
    SELECT
        'rewatch_14d' AS metric,
        window_label,
        concentration_quintile,
        breadth_quintile,
        COUNT(*) AS profiles,
        AVG(distinct_meaningful_titles) AS avg_meaningful_titles,
        AVG(top_title_qualified_share) AS avg_top_title_share,
        AVG(qualified_watch_hours) AS avg_watch_hours,
        AVG(active_days) AS avg_active_days,
        COUNT(rewatch_14d_rate) AS profiles_measured,
        SUM(CASE WHEN rewatch_14d_rate IS NOT NULL THEN rewatch_14d_known_denominator ELSE 0 END) AS known_outcomes,
        AVG(rewatch_14d_rate) AS raw_avg_rate,
        AVG(replay_watch_residual) AS deviation_vs_watch_context,
        AVG(CASE WHEN rewatch_14d_rate IS NOT NULL THEN rewatch_14d_rate > replay_watch_benchmark END) AS share_above_watch_context,
        MIN(CASE WHEN rewatch_14d_rate IS NOT NULL THEN replay_watch_benchmark_n END) AS min_watch_benchmark_n,
        AVG(replay_day_residual) AS deviation_vs_active_day_context,
        AVG(CASE WHEN rewatch_14d_rate IS NOT NULL THEN rewatch_14d_rate > replay_day_benchmark END) AS share_above_active_day_context,
        MIN(CASE WHEN rewatch_14d_rate IS NOT NULL THEN replay_day_benchmark_n END) AS min_active_day_benchmark_n
    FROM scored
    GROUP BY window_label, concentration_quintile, breadth_quintile
), combined AS (
    SELECT * FROM completion_cells
    UNION ALL
    SELECT * FROM replay_cells
)
SELECT
    *,
    CASE
        WHEN deviation_vs_watch_context > 0 AND deviation_vs_active_day_context > 0 THEN 'BOTH_POSITIVE'
        WHEN deviation_vs_watch_context < 0 AND deviation_vs_active_day_context < 0 THEN 'BOTH_NEGATIVE'
        ELSE 'MIXED_OR_ZERO'
    END AS control_directions,
    CASE
        WHEN profiles < 30 THEN 'THIN_CELL'
        ELSE 'STANDARD'
    END AS support_note
FROM combined
ORDER BY metric, window_label, concentration_quintile, breadth_quintile;
