-- MART AUDIT: profile_viewership_window | Test 3D - genre concentration
-- Question:        Does genre concentration reproduce the genre mart, and is it simply title concentration
--                  measured another way?
-- Why it matters:  If genre and title concentration were redundant, one could replace the other. If they
--                  differ, genre concentration can later add context to title concentration - but genre
--                  opportunity is not normalised, so it cannot stand alone as evidence of narrow taste.
-- Analytical use:  (1) Rebuilds meaningful-genre counts, top-genre share and genre HHI from
--                  profile_genre_window and checks their bounds (1/m <= share and HHI <= 1, and
--                  top share squared <= HHI <= top share); mismatch counts are expected 0. The last column
--                  counts the bounded caveat: genre_hhi populated on profiles with no meaningful genre,
--                  where genre concentration is undefined; those rows are excluded from interpretation.
--                  (2) Compares title and genre concentration for eligible profiles with valid title HHI.
--                  Raw correlations use all paired profiles; adjusted HHI = (HHI - 1/k) / (1 - 1/k) needs
--                  k >= 2, so adjusted averages and correlation use profiles with >= 2 meaningful genres.
--                  Adjusted HHI is an exploratory Test 3 diagnostic, not a canonical measure.
-- SELECT-only. Select the intended database before running.

WITH genre_rows AS (
    SELECT window_label, profile_id, qualified_starts,
           CASE WHEN qualified_watch_minutes > 0
                THEN qualified_watch_minutes
                     / SUM(qualified_watch_minutes) OVER (PARTITION BY window_label, profile_id)
           END AS share
    FROM profile_genre_window
),
rebuilt AS (
    SELECT window_label, profile_id,
           SUM(qualified_starts > 0) AS meaningful_genres,
           MAX(share)                AS top_genre_share,
           SUM(share * share)        AS genre_hhi
    FROM genre_rows
    GROUP BY window_label, profile_id
)
SELECT pv.window_label,
       SUM(pv.distinct_meaningful_genres <> COALESCE(r.meaningful_genres, 0)) AS meaningful_genre_count_mismatches,
       SUM(pv.distinct_meaningful_genres > 0
           AND (pv.genre_hhi IS NULL OR ABS(pv.genre_hhi - r.genre_hhi) > 0.000001))
                                                                              AS genre_hhi_mismatches,
       SUM(pv.distinct_meaningful_genres > 0
           AND (pv.top_genre_qualified_share IS NULL
                OR ABS(pv.top_genre_qualified_share - r.top_genre_share) > 0.000001))
                                                                              AS top_genre_share_mismatches,
       SUM(pv.distinct_meaningful_genres > 0
           AND (pv.genre_hhi < 1.0e0 / pv.distinct_meaningful_genres - 0.000001
                OR pv.genre_hhi > 1 + 0.000001
                OR pv.top_genre_qualified_share < 1.0e0 / pv.distinct_meaningful_genres - 0.000001
                OR pv.top_genre_qualified_share > 1 + 0.000001))              AS bound_violations,
       SUM(pv.distinct_meaningful_genres > 0
           AND (pv.genre_hhi < pv.top_genre_qualified_share * pv.top_genre_qualified_share - 0.000001
                OR pv.genre_hhi > pv.top_genre_qualified_share + 0.000001))   AS hhi_top_share_relation_violations,
       SUM(pv.genre_hhi IS NOT NULL AND pv.distinct_meaningful_genres = 0)    AS caveat_genre_hhi_without_meaningful_genres
FROM profile_viewership_window pv
LEFT JOIN rebuilt r
       ON r.window_label = pv.window_label AND r.profile_id = pv.profile_id
GROUP BY pv.window_label
ORDER BY pv.window_label;

WITH paired AS (
    SELECT window_label, distinct_meaningful_genres AS k,
           top_title_qualified_share AS top_title, top_genre_qualified_share AS top_genre,
           title_hhi, genre_hhi,
           (title_hhi - 1.0e0 / n_meaningful_titles) / (1 - 1.0e0 / n_meaningful_titles) AS adj_title,
           CASE WHEN distinct_meaningful_genres >= 2
                THEN (genre_hhi - 1.0e0 / distinct_meaningful_genres) / (1 - 1.0e0 / distinct_meaningful_genres)
           END AS adj_genre
    FROM profile_viewership_window
    WHERE is_main_analytical_eligible = 1 AND hhi_is_valid = 1 AND genre_hhi IS NOT NULL
)
SELECT window_label,
       COUNT(*)                                     AS paired_profiles,
       SUM(k >= 2)                                  AS profiles_with_2plus_genres,
       ROUND(AVG(k), 2)                             AS avg_meaningful_genres,
       ROUND(AVG(top_title), 4)                     AS avg_top_title_share,
       ROUND(AVG(top_genre), 4)                     AS avg_top_genre_share,
       ROUND(AVG(title_hhi), 4)                     AS avg_title_hhi,
       ROUND(AVG(genre_hhi), 4)                     AS avg_genre_hhi,
       ROUND((AVG(title_hhi * genre_hhi) - AVG(title_hhi) * AVG(genre_hhi))
             / (STDDEV_POP(title_hhi) * STDDEV_POP(genre_hhi)), 4)          AS raw_hhi_correlation,
       ROUND((AVG(top_title * top_genre) - AVG(top_title) * AVG(top_genre))
             / (STDDEV_POP(top_title) * STDDEV_POP(top_genre)), 4)          AS top_share_correlation,
       ROUND(AVG(CASE WHEN k >= 2 THEN adj_title END), 4)                   AS avg_adjusted_title_hhi,
       ROUND(AVG(adj_genre), 4)                                             AS avg_adjusted_genre_hhi,
       ROUND((AVG(CASE WHEN k >= 2 THEN adj_title * adj_genre END)
              - AVG(CASE WHEN k >= 2 THEN adj_title END) * AVG(adj_genre))
             / (STDDEV_POP(CASE WHEN k >= 2 THEN adj_title END) * STDDEV_POP(adj_genre)), 4)
                                                                            AS adjusted_hhi_correlation
FROM paired
GROUP BY window_label
ORDER BY window_label;
