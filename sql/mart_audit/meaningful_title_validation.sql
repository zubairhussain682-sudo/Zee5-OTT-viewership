-- Question:        When does a parent title count as part of a viewer's genuine catalogue breadth?
-- Why it matters:  A few seconds of playback is insufficient evidence of meaningful title
--                  engagement. Counting every touched title as breadth would inflate exploration,
--                  and counting a title that was merely available as engagement would confuse
--                  opportunity with choice.
-- Analytical use:  Confirms each title-level mart row sits at one profile x title x window grain,
--                  and that "meaningful title" means exactly one thing: at least one qualified
--                  start. Title rows that record opportunity without any qualified viewing never
--                  count as meaningful.
-- SELECT-only. Select the intended database before running. Each query should return no rows.

-- One row per profile, parent title and window.
SELECT profile_id, parent_title_id, window_label, COUNT(*) AS rows_at_grain
FROM profile_title_window
GROUP BY profile_id, parent_title_id, window_label
HAVING COUNT(*) > 1;

-- One row per profile and window in the profile measurement base.
SELECT profile_id, window_label, COUNT(*) AS rows_at_grain
FROM profile_viewership_window
GROUP BY profile_id, window_label
HAVING COUNT(*) > 1;

-- A title is meaningful if and only if it has at least one qualified start.
SELECT profile_id, parent_title_id, window_label
FROM profile_title_window
WHERE NOT (is_meaningful_title <=> (qualified_starts > 0));
