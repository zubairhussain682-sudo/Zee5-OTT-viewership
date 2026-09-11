-- Question:        Can one playback event be traced cleanly back to a viewer, an account, a title
--                  and the access that permitted it?
-- Why it matters:  Every future segment assignment should be explainable in terms of observed
--                  playback. If a single event cannot be traced without ambiguity, nothing built
--                  on top of it can be either.
-- Analytical use:  Resolves the viewer path (event -> session -> profile -> account) and the
--                  content path (event -> asset -> parent title) independently, and shows the
--                  consumed audio language next to the title's original language.
-- SELECT-only. Select the intended database before running.
--
-- The access join is INNER here for readability. More than one returned row means an interval
-- overlap or another join fan-out; use subscription_timeline.sql to detect missing access.

WITH params AS (
    -- Replace this example with the event identifier you want to trace.
    SELECT 'VE00000001' AS event_id
)
SELECT e.view_event_id, e.event_start_ts, e.watch_seconds,
       v.device_type, p.profile_id, a.account_id, a.home_region,
       c.parent_title_id, c.title_name, c.program_type, c.primary_genre,
       c.original_language, e.audio_language AS consumed_language,
       s.plan_family, s.cycle_start_date, s.cycle_end_date
FROM params
JOIN view_events e       ON e.view_event_id = params.event_id
JOIN viewing_sessions v  ON v.session_id = e.session_id
JOIN profiles p          ON p.profile_id = v.profile_id
JOIN accounts a          ON a.account_id = p.account_id
JOIN content_catalogue c ON c.content_id = e.content_id
JOIN subscription_cycles s
  ON s.account_id = a.account_id
 AND DATE(e.event_start_ts) BETWEEN s.cycle_start_date AND s.cycle_end_date
LIMIT 100;
