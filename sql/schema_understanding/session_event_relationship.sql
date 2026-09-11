-- Question:        How do sessions, playback events and playable assets relate?
-- Why it matters:  A session can contain several events, and each event touches one asset.
--                  Counting events as engagement, or sessions as titles, overstates both.
-- Analytical use:  Confirms playback identifiers are unique at their declared grains and that
--                  every event resolves to one session and one asset before any aggregation.
-- SELECT-only. Select the intended database before running.

-- Playback identifiers must be unique at their declared grains.
SELECT 'sessions' AS entity, COUNT(*) AS rows_total,
       COUNT(DISTINCT session_id) AS unique_ids
FROM viewing_sessions
UNION ALL
SELECT 'events', COUNT(*), COUNT(DISTINCT view_event_id)
FROM view_events;

-- Every event must belong to one session and touch one playable asset (expected: 0 orphans).
SELECT 'event_session' AS relationship, COUNT(*) AS orphan_rows
FROM view_events e LEFT JOIN viewing_sessions s ON s.session_id = e.session_id
WHERE s.session_id IS NULL
UNION ALL
SELECT 'event_asset', COUNT(*)
FROM view_events e LEFT JOIN content_catalogue c ON c.content_id = e.content_id
WHERE c.content_id IS NULL;
