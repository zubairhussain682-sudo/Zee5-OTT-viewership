-- Question:        What could a profile realistically have watched during a measurement window?
-- Why it matters:  Low breadth only signals unrealised viewing if the alternatives were actually
--                  reachable. A profile created halfway through a window, an account between
--                  subscriptions, or a regional plan without a title's language all shrink the
--                  real choice set. Measuring against the whole catalogue would call constrained
--                  access disengagement.
-- Analytical use:  Confirms opportunity never exceeds the days a profile could observably have
--                  existed in the window, that the eligibility flag follows its stated rule, and
--                  that account eligible-profile counts add up from profiles.
-- SELECT-only. Select the intended database before running. Each query should return no rows.
--
-- The calendar span is an UPPER BOUND only. The actual denominator comes from the day-by-day
-- intersection of profile existence, historical plan access and available, eligible catalogue.

-- Profile entitled days cannot exceed the days the profile existed inside the window.
SELECT pv.profile_id, pv.window_label,
       pv.entitled_days_in_window, pv.vod_entitled_days_in_window
FROM profile_viewership_window pv
JOIN profiles p ON p.profile_id = pv.profile_id
WHERE pv.entitled_days_in_window IS NULL
   OR pv.vod_entitled_days_in_window IS NULL
   OR pv.entitled_days_in_window     > GREATEST(0, DATEDIFF(pv.window_end, GREATEST(pv.window_start, p.profile_created_date)) + 1)
   OR pv.vod_entitled_days_in_window > GREATEST(0, DATEDIFF(pv.window_end, GREATEST(pv.window_start, p.profile_created_date)) + 1);

-- Title opportunity is bounded the same way.
SELECT pt.profile_id, pt.parent_title_id, pt.window_label, pt.available_days_in_window
FROM profile_title_window pt
JOIN profiles p ON p.profile_id = pt.profile_id
WHERE pt.available_days_in_window IS NULL
   OR pt.available_days_in_window > GREATEST(0, DATEDIFF(pt.window_end, GREATEST(pt.window_start, p.profile_created_date)) + 1);

-- Eligibility: at least 30 entitled days, 3 active days and 120 qualified watch minutes.
SELECT profile_id, window_label
FROM profile_viewership_window
WHERE NOT (is_main_analytical_eligible <=>
    (vod_entitled_days_in_window >= 30 AND active_days >= 3 AND qualified_watch_minutes >= 120));

-- One row per account and window, so the additivity check below is well defined.
SELECT account_id, window_label, COUNT(*) AS rows_at_grain
FROM account_viewership_window
GROUP BY account_id, window_label
HAVING COUNT(*) > 1;

-- Eligible-profile counts are additive across an account's profiles; distinct behavioural
-- breadth generally is not.
SELECT av.account_id, av.window_label, av.n_eligible_profiles,
       COALESCE(p.expected_eligible_profiles, 0) AS expected_eligible_profiles
FROM account_viewership_window av
LEFT JOIN (
    SELECT account_id, window_label,
           SUM(is_main_analytical_eligible) AS expected_eligible_profiles
    FROM profile_viewership_window
    GROUP BY account_id, window_label
) p ON p.account_id = av.account_id AND p.window_label = av.window_label
WHERE NOT (av.n_eligible_profiles <=> COALESCE(p.expected_eligible_profiles, 0));
