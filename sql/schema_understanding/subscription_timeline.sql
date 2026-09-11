-- Question:        What access did an account actually hold on the day a viewing event happened?
-- Why it matters:  Accounts hold a sequence of access intervals. Joining events to subscriptions
--                  on account alone duplicates each event across every interval and can apply a
--                  later plan to earlier viewing.
-- Analytical use:  Confirms access intervals do not overlap and that a date-aware join resolves
--                  each event to exactly one interval, the rule every opportunity measure follows.
-- SELECT-only. Select the intended database before running.

-- Access intervals for the same account must not overlap (expected: 0 rows).
SELECT a.account_id, a.subscription_cycle_id, b.subscription_cycle_id AS overlapping_cycle_id
FROM subscription_cycles a
JOIN subscription_cycles b
  ON b.account_id = a.account_id
 AND b.subscription_cycle_id > a.subscription_cycle_id
 AND b.cycle_start_date <= a.cycle_end_date
 AND b.cycle_end_date   >= a.cycle_start_date;

-- A date-aware join must resolve each event to exactly one access interval (expected: 0 rows).
-- The LEFT JOIN keeps events with no access, so a missing interval is detected, not hidden.
SELECT e.view_event_id, COUNT(c.subscription_cycle_id) AS access_matches
FROM view_events e
JOIN viewing_sessions s ON s.session_id = e.session_id
JOIN profiles p ON p.profile_id = s.profile_id
LEFT JOIN subscription_cycles c
  ON c.account_id = p.account_id
 AND DATE(e.event_start_ts) BETWEEN c.cycle_start_date AND c.cycle_end_date
GROUP BY e.view_event_id
HAVING COUNT(c.subscription_cycle_id) <> 1;
