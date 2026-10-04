-- VIEWER DIAGNOSIS: profile_viewership_window | Test 6C.2 - Baseline title-origin anchor and Final cross-origin viewing
-- Question:        Once each profile's Baseline viewing centre is fixed, how much Final qualified viewing happens
--                  on parent titles originating outside that ecosystem?
-- Why it matters:  Native language is not observed. home_region, regional plan language and title origin are all
--                  contextual fields, so movement across catalogue ecosystems needs a reference taken from
--                  observed behaviour rather than from identity.
-- Analytical use:  Pairs profiles eligible in both windows (8,199), ranks Baseline qualified minutes by the parent
--                  title's original_language, and fixes the top-ranked origin as the Baseline anchor - ties broken
--                  by minutes descending then language ascending. The anchor is never recomputed from Final
--                  viewing. Final viewing is then classified by the title's origin, not by the audio track
--                  consumed, so a dubbed title stays cross-origin. Rows are aggregated into 5-percentage-point
--                  Baseline anchor-share bands; those bands are sensitivity slices, not segment thresholds.
--                  Shares are clamped to [0,1] before change comparisons, and derived Final shares are reconciled
--                  against their components in the same pass.
--                  Output is descriptive movement, not a language-openness score, a causal plan effect or headroom.
-- Grain:           One row per Baseline anchor-share band.
-- Source:          The query behind the published cross-origin evidence; cross-origin opportunity is reconstructed
--                  separately in Python from the same day-by-day exposure the marts use.

WITH paired_profiles AS (
    SELECT
        profile_id
    FROM ott_viewership.profile_viewership_window
    WHERE is_main_analytical_eligible = 1
      AND window_label IN ('BASELINE_90', 'FINAL_90')
    GROUP BY profile_id
    HAVING COUNT(DISTINCT window_label) = 2
),

parent_origin AS (
    SELECT
        parent_title_id,
        MAX(original_language) AS original_language
    FROM ott_viewership.content_catalogue
    GROUP BY parent_title_id
    HAVING COUNT(DISTINCT original_language) = 1
       AND MAX(original_language) IS NOT NULL
),

profile_window AS (
    SELECT
        p.profile_id,
        p.window_label,
        p.qualified_watch_minutes,
        p.qualified_watch_hours,
        p.active_days,
        p.distinct_meaningful_titles
    FROM ott_viewership.profile_viewership_window p
    JOIN paired_profiles pp
      ON pp.profile_id = p.profile_id
    WHERE p.window_label IN ('BASELINE_90', 'FINAL_90')
      AND p.is_main_analytical_eligible = 1
),

origin_by_window AS (
    SELECT
        ptw.profile_id,
        ptw.window_label,
        po.original_language,
        SUM(ptw.qualified_watch_minutes) AS origin_qualified_minutes,
        COUNT(*) AS meaningful_titles_in_origin
    FROM ott_viewership.profile_title_window ptw
    JOIN paired_profiles pp
      ON pp.profile_id = ptw.profile_id
    JOIN parent_origin po
      ON po.parent_title_id = ptw.parent_title_id
    WHERE ptw.window_label IN ('BASELINE_90', 'FINAL_90')
      AND ptw.is_meaningful_title = 1
    GROUP BY
        ptw.profile_id,
        ptw.window_label,
        po.original_language
),

baseline_ranked AS (
    SELECT
        obw.profile_id,
        obw.original_language,
        obw.origin_qualified_minutes,
        obw.meaningful_titles_in_origin,

        GREATEST(
            0,
            LEAST(
                1,
                obw.origin_qualified_minutes
                    / NULLIF(pw.qualified_watch_minutes, 0)
            )
        ) AS origin_minute_share,

        ROW_NUMBER() OVER (
            PARTITION BY obw.profile_id
            ORDER BY
                obw.origin_qualified_minutes DESC,
                obw.original_language
        ) AS origin_rank,

        SUM(obw.meaningful_titles_in_origin)
            OVER (PARTITION BY obw.profile_id)
            AS baseline_total_meaningful_titles

    FROM origin_by_window obw
    JOIN profile_window pw
      ON pw.profile_id = obw.profile_id
     AND pw.window_label = 'BASELINE_90'
    WHERE obw.window_label = 'BASELINE_90'
),

baseline_anchor AS (
    SELECT
        profile_id,

        MAX(
            CASE WHEN origin_rank = 1
                 THEN original_language END
        ) AS baseline_dominant_origin_language,

        MAX(
            CASE WHEN origin_rank = 1
                 THEN origin_minute_share END
        ) AS baseline_dominant_origin_share,

        COALESCE(
            MAX(
                CASE WHEN origin_rank = 2
                     THEN origin_minute_share END
            ),
            0
        ) AS baseline_second_origin_share,

        MAX(
            CASE WHEN origin_rank = 1
                 THEN meaningful_titles_in_origin END
        ) AS baseline_anchor_supporting_titles,

        MAX(baseline_total_meaningful_titles)
            AS baseline_total_meaningful_titles

    FROM baseline_ranked
    GROUP BY profile_id
),

baseline_origin_set AS (
    SELECT DISTINCT
        profile_id,
        original_language
    FROM origin_by_window
    WHERE window_label = 'BASELINE_90'
),

final_origin AS (
    SELECT
        obw.profile_id,
        obw.original_language,
        obw.origin_qualified_minutes,
        obw.meaningful_titles_in_origin,

        CASE
            WHEN obw.original_language
                 <> ba.baseline_dominant_origin_language
            THEN 1 ELSE 0
        END AS is_cross_origin,

        CASE
            WHEN bos.original_language IS NULL
            THEN 1 ELSE 0
        END AS is_new_origin_language

    FROM origin_by_window obw
    JOIN baseline_anchor ba
      ON ba.profile_id = obw.profile_id
    LEFT JOIN baseline_origin_set bos
      ON bos.profile_id = obw.profile_id
     AND bos.original_language = obw.original_language
    WHERE obw.window_label = 'FINAL_90'
),

final_profile AS (
    SELECT
        fo.profile_id,

        SUM(fo.origin_qualified_minutes)
            AS reconstructed_final_qualified_minutes,

        SUM(
            CASE WHEN fo.is_cross_origin = 1
                 THEN fo.origin_qualified_minutes
                 ELSE 0 END
        ) AS final_cross_origin_qualified_minutes,

        SUM(
            CASE WHEN fo.is_cross_origin = 1
                 THEN fo.meaningful_titles_in_origin
                 ELSE 0 END
        ) AS final_cross_origin_meaningful_titles,

        COUNT(
            DISTINCT CASE
                WHEN fo.is_cross_origin = 1
                THEN fo.original_language
            END
        ) AS final_distinct_cross_origin_languages,

        COUNT(
            DISTINCT CASE
                WHEN fo.is_new_origin_language = 1
                THEN fo.original_language
            END
        ) AS final_new_origin_languages,

        SUM(
            CASE WHEN fo.is_new_origin_language = 1
                 THEN fo.origin_qualified_minutes
                 ELSE 0 END
        ) AS final_new_origin_qualified_minutes,

        SUM(
            CASE WHEN fo.is_new_origin_language = 1
                 THEN fo.meaningful_titles_in_origin
                 ELSE 0 END
        ) AS final_new_origin_meaningful_titles

    FROM final_origin fo
    GROUP BY fo.profile_id
),

longitudinal_profile AS (
    SELECT
        ba.profile_id,
        ba.baseline_dominant_origin_language,
        ba.baseline_dominant_origin_share,

        GREATEST(
            0,
            LEAST(
                1,
                ba.baseline_dominant_origin_share
                    - ba.baseline_second_origin_share
            )
        ) AS baseline_origin_dominance_gap,

        ba.baseline_anchor_supporting_titles,
        ba.baseline_total_meaningful_titles,

        GREATEST(
            0,
            LEAST(
                1,
                1 - ba.baseline_dominant_origin_share
            )
        ) AS baseline_cross_origin_minute_share,

        b.qualified_watch_hours
            AS baseline_qualified_watch_hours,

        b.active_days
            AS baseline_active_days,

        f.qualified_watch_minutes
            AS final_qualified_watch_minutes,

        f.qualified_watch_hours
            AS final_qualified_watch_hours,

        f.active_days
            AS final_active_days,

        f.distinct_meaningful_titles
            AS final_total_meaningful_titles,

        fp.final_cross_origin_qualified_minutes,
        fp.final_cross_origin_meaningful_titles,
        fp.final_distinct_cross_origin_languages,
        fp.final_new_origin_languages,
        fp.final_new_origin_qualified_minutes,
        fp.final_new_origin_meaningful_titles,

        GREATEST(
            0,
            LEAST(
                1,
                fp.final_cross_origin_qualified_minutes
                    / NULLIF(f.qualified_watch_minutes, 0)
            )
        ) AS final_cross_origin_minute_share,

        GREATEST(
            0,
            LEAST(
                1,
                fp.final_cross_origin_meaningful_titles
                    / NULLIF(f.distinct_meaningful_titles, 0)
            )
        ) AS final_cross_origin_title_share,

        GREATEST(
            0,
            LEAST(
                1,
                fp.final_new_origin_qualified_minutes
                    / NULLIF(f.qualified_watch_minutes, 0)
            )
        ) AS final_new_origin_minute_share,

        fp.reconstructed_final_qualified_minutes
            - f.qualified_watch_minutes
            AS final_reconciliation_diff

    FROM baseline_anchor ba

    JOIN profile_window b
      ON b.profile_id = ba.profile_id
     AND b.window_label = 'BASELINE_90'

    JOIN profile_window f
      ON f.profile_id = ba.profile_id
     AND f.window_label = 'FINAL_90'

    JOIN final_profile fp
      ON fp.profile_id = ba.profile_id
),

analysis_ready AS (
    SELECT
        *,

        final_cross_origin_minute_share
            - baseline_cross_origin_minute_share
            AS cross_origin_share_change,

        CASE
            WHEN final_cross_origin_meaningful_titles = 0
            THEN 1 ELSE 0
        END AS stayed_only_in_baseline_anchor,

        CASE
            WHEN final_new_origin_languages > 0
            THEN 1 ELSE 0
        END AS entered_new_origin_language,

        CASE
            WHEN final_cross_origin_minute_share
                 > baseline_cross_origin_minute_share + 0.000000000001
            THEN 1 ELSE 0
        END AS cross_origin_share_increased,

        FLOOR(
            LEAST(
                baseline_dominant_origin_share,
                0.999999
            ) * 20
        ) / 20.0 AS baseline_anchor_share_band

    FROM longitudinal_profile
)

SELECT
    ROUND(baseline_anchor_share_band, 2)
        AS baseline_dominant_share_from,

    ROUND(baseline_anchor_share_band + 0.05, 2)
        AS baseline_dominant_share_to,

    COUNT(*) AS profiles,

    ROUND(
        100.0 * COUNT(*)
        / SUM(COUNT(*)) OVER (),
        2
    ) AS pct_profiles,

    ROUND(
        AVG(baseline_dominant_origin_share),
        4
    ) AS avg_baseline_dominant_origin_share,

    ROUND(
        AVG(baseline_origin_dominance_gap),
        4
    ) AS avg_baseline_dominance_gap,

    ROUND(
        AVG(baseline_anchor_supporting_titles),
        2
    ) AS avg_baseline_anchor_supporting_titles,

    ROUND(
        AVG(baseline_cross_origin_minute_share),
        4
    ) AS avg_baseline_cross_origin_minute_share,

    ROUND(
        AVG(final_cross_origin_minute_share),
        4
    ) AS avg_final_cross_origin_minute_share,

    ROUND(
        AVG(cross_origin_share_change),
        4
    ) AS avg_cross_origin_share_change,

    ROUND(
        AVG(final_cross_origin_meaningful_titles),
        2
    ) AS avg_final_cross_origin_titles,

    ROUND(
        AVG(final_cross_origin_title_share),
        4
    ) AS avg_final_cross_origin_title_share,

    ROUND(
        AVG(final_distinct_cross_origin_languages),
        2
    ) AS avg_final_distinct_cross_origin_languages,

    ROUND(
        AVG(final_new_origin_languages),
        2
    ) AS avg_final_new_origin_languages,

    ROUND(
        AVG(final_new_origin_meaningful_titles),
        2
    ) AS avg_final_new_origin_titles,

    ROUND(
        AVG(final_new_origin_minute_share),
        4
    ) AS avg_final_new_origin_minute_share,

    ROUND(
        100.0 * AVG(stayed_only_in_baseline_anchor),
        2
    ) AS pct_stayed_only_in_baseline_anchor,

    ROUND(
        100.0 * AVG(entered_new_origin_language),
        2
    ) AS pct_entered_new_origin_language,

    ROUND(
        100.0 * AVG(cross_origin_share_increased),
        2
    ) AS pct_cross_origin_share_increased,

    ROUND(
        AVG(baseline_qualified_watch_hours),
        2
    ) AS avg_baseline_watch_hours,

    ROUND(
        AVG(final_qualified_watch_hours),
        2
    ) AS avg_final_watch_hours,

    ROUND(
        AVG(baseline_active_days),
        2
    ) AS avg_baseline_active_days,

    ROUND(
        AVG(final_active_days),
        2
    ) AS avg_final_active_days,

    SUM(
        ABS(final_reconciliation_diff) > 0.000001
    ) AS final_reconciliation_failures,

    ROUND(
        MAX(ABS(final_reconciliation_diff)),
        8
    ) AS max_abs_final_reconciliation_diff

FROM analysis_ready
GROUP BY baseline_anchor_share_band
ORDER BY baseline_anchor_share_band;
