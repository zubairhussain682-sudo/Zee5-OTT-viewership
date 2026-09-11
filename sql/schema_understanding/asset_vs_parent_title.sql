-- Question:        Is a playable asset the same unit as a catalogue title?
-- Why it matters:  An episodic programme contributes many assets but only one parent title.
--                  Counting assets as titles would read ten episodes of one series as exploration
--                  of ten programmes, confusing episodic depth with catalogue breadth.
-- Analytical use:  Shows that parent_title_id repeats across assets, and where that repetition
--                  concentrates, which is why title breadth is measured at parent-title grain.
-- SELECT-only. Select the intended database before running.

-- Different grains, not competing estimates of the same count.
SELECT COUNT(*) AS playable_assets,
       COUNT(DISTINCT parent_title_id) AS parent_titles
FROM content_catalogue;

-- The asset-to-title ratio differs by programme type: episodic formats carry the depth.
SELECT program_type,
       COUNT(*) AS playable_assets,
       COUNT(DISTINCT parent_title_id) AS parent_titles
FROM content_catalogue
GROUP BY program_type
ORDER BY program_type;
