-- Question:        After a viewer finishes an episode, did they go on to the next one?
-- Why it matters:  Continuation is a core signal of stickiness, but only where a next episode
--                  was genuinely reachable and the follow-up period was fully observed. Treating
--                  "not yet observed" as "did not continue" would make recent viewing look less
--                  sticky simply because less time had passed.
-- Analytical use:  Confirms each opportunity has exactly one outcome state (continued, observed
--                  negative, or unknown), that the continuation rate uses only known outcomes as
--                  its denominator, and that the profile total equals the sum of its title rows.
-- SELECT-only. Select the intended database before running. Each query should return no rows.

-- Outcome states are mutually exclusive at title grain.
SELECT profile_id, parent_title_id, window_label
FROM profile_title_window
WHERE continued_opportunities + censored_continuation_opportunities > continuation_opportunities;

-- The profile continuation rate pools known positives over known positives plus known
-- negatives. Unknown outcomes are excluded from the denominator, never counted as failures.
SELECT profile_id, window_label
FROM profile_viewership_window
WHERE observed_continuation_opportunities <> continuation_opportunities - censored_continuation_opportunities
   OR observed_continued <> continued_opportunities
   OR NOT (continuation_rate_is_valid <=> (observed_continuation_opportunities > 0))
   OR (observed_continuation_opportunities = 0 AND continuation_rate IS NOT NULL)
   OR (observed_continuation_opportunities > 0 AND
       (continuation_rate IS NULL
        OR ABS(continuation_rate - continued_opportunities * 1.0e0 / observed_continuation_opportunities) > 1e-14));

-- Profile-level opportunity counts equal the sum of the profile's title rows.
SELECT pv.profile_id, pv.window_label
FROM profile_viewership_window pv
LEFT JOIN (
    SELECT profile_id, window_label,
           SUM(continuation_opportunities)          AS opportunities,
           SUM(continued_opportunities)             AS continued,
           SUM(censored_continuation_opportunities) AS censored
    FROM profile_title_window
    GROUP BY profile_id, window_label
) pt ON pt.profile_id = pv.profile_id AND pt.window_label = pv.window_label
WHERE pv.continuation_opportunities          <> COALESCE(pt.opportunities, 0)
   OR pv.continued_opportunities             <> COALESCE(pt.continued, 0)
   OR pv.censored_continuation_opportunities <> COALESCE(pt.censored, 0);
