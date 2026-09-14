-- MART AUDIT: profile_viewership_window | Test 3A-3B - breadth reconciliation and qualification effect
-- Question:        Does viewer-level breadth reproduce raw playback and the title and genre marts, and
--                  how much does qualification change it?
-- Why it matters:  Breadth must count parent titles, not episodes, and shallow touches must not inflate
--                  catalogue reach. Qualification should remove those touches without silently rewriting
--                  the breadth structure every later concentration measure depends on.
-- Analytical use:  (1) Rebuilds distinct assets, parent titles, genres and consumed audio languages from
--                  raw playback. (2) Reconciles breadth and meaningful breadth with profile_title_window
--                  and profile_genre_window. Both return mismatch counts, expected 0. (3) Describes the
--                  raw-to-meaningful breadth reduction for profiles with any playback; genre changes are
--                  descriptive only, because genre opportunity is not normalised.
-- SELECT-only. Select the intended database before running.

WITH windows AS (
    SELECT DISTINCT window_label, window_start, window_end
    FROM profile_viewership_window
),
raw_breadth AS (
    SELECT w.window_label, s.profile_id,
           COUNT(DISTINCT e.content_id)       AS assets,
           COUNT(DISTINCT c.parent_title_id)  AS parent_titles,
           COUNT(DISTINCT c.primary_genre)    AS genres,
           COUNT(DISTINCT e.audio_language)   AS audio_languages
    FROM view_events e
    JOIN viewing_sessions s  ON s.session_id = e.session_id
    JOIN content_catalogue c ON c.content_id = e.content_id
    JOIN windows w
      ON e.event_start_ts >= w.window_start
     AND e.event_start_ts <  w.window_end + INTERVAL 1 DAY
    GROUP BY w.window_label, s.profile_id
)
SELECT pv.window_label,
       SUM(pv.distinct_assets                   <> COALESCE(r.assets, 0))          AS asset_mismatches,
       SUM(pv.distinct_parent_titles            <> COALESCE(r.parent_titles, 0))   AS parent_title_mismatches,
       SUM(pv.distinct_genres                   <> COALESCE(r.genres, 0))          AS genre_mismatches,
       SUM(pv.distinct_audio_languages_consumed <> COALESCE(r.audio_languages, 0)) AS audio_language_mismatches
FROM profile_viewership_window pv
LEFT JOIN raw_breadth r
       ON r.window_label = pv.window_label AND r.profile_id = pv.profile_id
GROUP BY pv.window_label
ORDER BY pv.window_label;

SELECT pv.window_label,
       SUM(pv.distinct_parent_titles     <> COALESCE(t.watched_titles, 0))    AS parent_titles_vs_title_mart,
       SUM(pv.distinct_assets            <> COALESCE(t.assets, 0))            AS assets_vs_title_mart,
       SUM(pv.distinct_meaningful_titles <> COALESCE(t.meaningful_titles, 0)) AS meaningful_titles_vs_title_mart,
       SUM(pv.distinct_genres            <> COALESCE(g.genres, 0))            AS genres_vs_genre_mart,
       SUM(pv.distinct_meaningful_genres <> COALESCE(g.meaningful_genres, 0)) AS meaningful_genres_vs_genre_mart
FROM profile_viewership_window pv
LEFT JOIN (
    SELECT window_label, profile_id,
           SUM(events > 0)              AS watched_titles,
           SUM(distinct_assets_watched) AS assets,
           SUM(is_meaningful_title)     AS meaningful_titles
    FROM profile_title_window
    GROUP BY window_label, profile_id
) t ON t.window_label = pv.window_label AND t.profile_id = pv.profile_id
LEFT JOIN (
    SELECT window_label, profile_id,
           COUNT(*)              AS genres,
           SUM(qualified_starts > 0) AS meaningful_genres
    FROM profile_genre_window
    GROUP BY window_label, profile_id
) g ON g.window_label = pv.window_label AND g.profile_id = pv.profile_id
GROUP BY pv.window_label
ORDER BY pv.window_label;

WITH active AS (
    SELECT window_label, is_main_analytical_eligible,
           distinct_parent_titles, distinct_meaningful_titles, distinct_genres, distinct_meaningful_genres,
           CAST(distinct_parent_titles AS SIGNED) - distinct_meaningful_titles AS title_reduction,
           CAST(distinct_genres AS SIGNED) - distinct_meaningful_genres       AS genre_reduction
    FROM profile_viewership_window
    WHERE events > 0
)
SELECT window_label,
       COUNT(*)                                                           AS active_profiles,
       SUM(title_reduction > 0)                                           AS profiles_losing_title,
       ROUND(100 * AVG(title_reduction > 0), 2)                           AS pct_losing_title,
       ROUND(AVG(distinct_parent_titles), 2)                              AS avg_raw_titles,
       ROUND(AVG(distinct_meaningful_titles), 2)                          AS avg_meaningful_titles,
       ROUND(AVG(title_reduction), 2)                                     AS avg_title_reduction,
       ROUND(100 * AVG(distinct_meaningful_titles / distinct_parent_titles), 2) AS avg_title_retention_pct,
       SUM(genre_reduction > 0)                                           AS profiles_losing_genre,
       ROUND(100 * AVG(genre_reduction > 0), 2)                           AS pct_losing_genre,
       ROUND(AVG(genre_reduction), 2)                                     AS avg_genre_reduction,
       ROUND(100 * AVG(distinct_meaningful_genres / distinct_genres), 2)  AS avg_genre_retention_pct,
       SUM(title_reduction = 0)                                           AS titles_lost_0,
       SUM(title_reduction = 1)                                           AS titles_lost_1,
       SUM(title_reduction = 2)                                           AS titles_lost_2,
       SUM(title_reduction >= 3)                                          AS titles_lost_3_plus,
       SUM(is_main_analytical_eligible AND title_reduction > 0)           AS eligible_profiles_losing_title,
       SUM(is_main_analytical_eligible)                                   AS eligible_profiles
FROM active
GROUP BY window_label
ORDER BY window_label;
