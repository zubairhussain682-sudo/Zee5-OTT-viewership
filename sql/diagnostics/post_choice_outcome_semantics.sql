-- VIEWER DIAGNOSIS: profile_viewership_window | Test 4B-4C - post-choice outcome semantics
-- Question:        Which post-choice outcomes can be measured fairly, and do completion and abandonment
--                  carry independent behavioural information?
-- Why it matters:  An unfinished start near the end of the data is unknown, not a non-abandonment. And two
--                  measures that are exact complements would double-weight one behaviour if both entered
--                  later fingerprints.
-- Analytical use:  (1) For eligible profiles, compares the stored abandonment rate (all qualified starts) with
--                  the known-outcome rate (qualified starts minus censored abandonment starts), and reports
--                  profile-average and pooled known-outcome completion, abandonment and continuation rates
--                  (>= 5 known outcomes or observed opportunities). Profile averages weight viewers equally;
--                  pooled rates weight outcomes. The published summary's completion columns use the stored
--                  formulation over all qualified starts instead; see evidence/mart_audit. (2) Places completion and
--                  abandonment on the same known-outcome denominator (>= 5) and tests whether any independent
--                  known outcome remains: correlation, complement gap and residual known-outcome share.
-- SELECT-only. Select the intended database before running.

WITH eligible AS (
    SELECT
        window_label,
        profile_id,
        qualified_asset_starts,
        completed_asset_starts,
        abandoned_asset_starts,
        censored_abandonment_starts,
        abandonment_known_denominator,
        abandonment_rate AS stored_abandonment_rate,
        observed_continuation_opportunities,
        observed_continued,
        continuation_rate,
        CASE
            WHEN abandonment_known_denominator > 0
            THEN abandoned_asset_starts * 1.0 / abandonment_known_denominator
        END AS known_abandonment_rate,
        CASE
            WHEN abandonment_known_denominator > 0
            THEN completed_asset_starts * 1.0 / abandonment_known_denominator
        END AS known_completion_rate
    FROM profile_viewership_window
    WHERE is_main_analytical_eligible = 1
)
SELECT
    window_label,
    COUNT(*) AS eligible_profiles,
    SUM(censored_abandonment_starts > 0) AS profiles_with_censored_abandonment,
    SUM(abandonment_known_denominator >= 5) AS profiles_known_abandonment_ge5,
    AVG(CASE WHEN qualified_asset_starts >= 5 THEN stored_abandonment_rate END) AS avg_stored_abandonment_rate_ge5,
    AVG(CASE WHEN abandonment_known_denominator >= 5 THEN known_abandonment_rate END) AS avg_known_abandonment_rate_ge5,
    SUM(abandoned_asset_starts) * 1.0 / NULLIF(SUM(qualified_asset_starts), 0) AS pooled_stored_abandonment_rate,
    SUM(abandoned_asset_starts) * 1.0 / NULLIF(SUM(abandonment_known_denominator), 0) AS pooled_known_abandonment_rate,
    AVG(CASE WHEN abandonment_known_denominator >= 5 THEN known_completion_rate END) AS avg_known_completion_rate_ge5,
    SUM(completed_asset_starts) * 1.0 / NULLIF(SUM(abandonment_known_denominator), 0) AS pooled_known_completion_rate,
    SUM(observed_continuation_opportunities >= 5) AS profiles_continuation_ge5,
    AVG(CASE WHEN observed_continuation_opportunities >= 5 THEN continuation_rate END) AS avg_continuation_rate_ge5,
    SUM(observed_continued) * 1.0 / NULLIF(SUM(observed_continuation_opportunities), 0) AS pooled_continuation_rate
FROM eligible
GROUP BY window_label
ORDER BY window_label;

WITH rates AS (
    SELECT
        window_label,
        profile_id,
        abandonment_known_denominator,
        completed_asset_starts * 1.0 / abandonment_known_denominator AS completion_known_rate,
        abandoned_asset_starts * 1.0 / abandonment_known_denominator AS abandonment_known_rate,
        (abandonment_known_denominator - completed_asset_starts - abandoned_asset_starts) * 1.0
            / abandonment_known_denominator AS other_known_share
    FROM profile_viewership_window
    WHERE is_main_analytical_eligible = 1
      AND abandonment_known_denominator >= 5
), moments AS (
    SELECT
        window_label,
        COUNT(*) AS profiles,
        AVG(completion_known_rate) AS mean_completion,
        AVG(abandonment_known_rate) AS mean_abandonment
    FROM rates
    GROUP BY window_label
), scored AS (
    SELECT
        r.*,
        m.mean_completion,
        m.mean_abandonment
    FROM rates r
    JOIN moments m USING (window_label)
)
SELECT
    window_label,
    COUNT(*) AS profiles_common_denom_ge5,
    SUM(negative_residual_flag) AS negative_residual_profiles,
    SUM((completion_known_rate - mean_completion) * (abandonment_known_rate - mean_abandonment))
        / NULLIF(
            SQRT(
                SUM(POW(completion_known_rate - mean_completion, 2))
                * SUM(POW(abandonment_known_rate - mean_abandonment, 2))
            ), 0
        ) AS pearson_completion_vs_abandonment,
    AVG(ABS(1.0 - completion_known_rate - abandonment_known_rate)) AS mean_abs_complement_gap,
    AVG(ABS(1.0 - completion_known_rate - abandonment_known_rate) <= 0.05) AS share_profiles_within_5pp_of_complement,
    AVG(other_known_share) AS mean_other_known_outcome_share
FROM (
    SELECT
        scored.*,
        (other_known_share < -1e-12) AS negative_residual_flag
    FROM scored
) x
GROUP BY window_label
ORDER BY window_label;
