# Viewer-diagnosis evidence

**Question:** does similar surface concentration conceal different responses after content is chosen?

**Why it matters:** concentration describes where attention accumulated, not whether the concentrated choices worked. If similar concentration sits above different post-choice behaviour, concentration cannot define a segment on its own.

This folder holds behavioural mechanism evidence. The measurement decisions it depends on — known-outcome completion, the 14-day replay horizon and the separation of resume from replay — are recorded with their evidence in [`../mart_audit`](../mart_audit/README.md#test-4--post-choice-response-and-the-bridge-from-concentration-to-mechanism). Everything here is a compact result extract, not a profile-level or mart dataset.

## `concentration_mechanism_controls.csv`

**Produced by:** [`concentration_mechanism_controls.sql`](../../sql/diagnostics/concentration_mechanism_controls.sql), using the profile-level 14-day replay table written by [`rewatch_observability.py`](../../scripts/diagnostics/rewatch_observability.py). That profile-level table is not published.

**Population and window:** analytically eligible profiles with at least one meaningful title, in `BASELINE_90` (2025-09-01 to 2025-11-29) and `FINAL_90` (2025-11-30 to 2026-02-27). Each window is analysed separately.

**Grain:** one row per metric × window × concentration quintile × breadth quintile. Quintiles are formed within each window: concentration by top-title qualified share and breadth by meaningful parent titles, with Q1 the lowest and Q5 the highest. Each profile-window sits in exactly one cell, so a cell is a behavioural state, `state(profile, window)` — the same profile can occupy a different cell in the other window. Breadth × concentration combinations with no profiles do not appear, which leaves 21 cells per metric in each window.

**Denominators:**

| Metric | Profile-level rate | Included when |
| --- | --- | --- |
| `completion` | completed asset starts ÷ known outcomes (qualified asset starts − censored abandonment starts) | at least 5 known outcomes |
| `rewatch_14d` | completed assets rewatched within 14 days ÷ known 14-day outcomes | at least 3 known outcomes |

**Columns:**

| Column | Meaning |
| --- | --- |
| `profiles` | Profiles in the cell |
| `avg_meaningful_titles`, `avg_top_title_share`, `avg_watch_hours`, `avg_active_days` | Cell profile, averaged over all profiles in the cell |
| `profiles_measured` | Profiles meeting the metric's evidence threshold |
| `known_outcomes` | Known outcomes summed over measured profiles |
| `raw_avg_rate` | Profile-average rate over measured profiles (each profile weighted equally) |
| `deviation_vs_watch_context` | Average of each profile's rate minus the window average for profiles in its qualified-watch-hours quintile |
| `deviation_vs_active_day_context` | The same comparison against profiles in its active-days quintile |
| `share_above_watch_context`, `share_above_active_day_context` | Share of measured profiles above their benchmark |
| `min_watch_benchmark_n`, `min_active_day_benchmark_n` | Smallest benchmark group used by the cell's profiles |
| `control_directions` | `BOTH_POSITIVE`, `BOTH_NEGATIVE` or `MIXED_OR_ZERO` across the two controls |
| `support_note` | `THIN_CELL` under 30 profiles; otherwise `STANDARD` |

Values are rounded to four decimal places.

**Reading a deviation:** a completion deviation of +0.10 against watch-hours context means the cell's profiles completed about ten percentage points more than profiles in the same window with similar qualified watch volume. Context is a fairness benchmark, not a behavioural score and not a platform target.

**What it supports:** that similar concentration can sit above different post-choice responses, and that several of those differences keep their direction against both activity controls. The candidate states drawn from it are described in the [analysis journal](../../docs/analysis_journal.md#14-when-concentration-stops-meaning-the-same-thing).

**What it does not prove:** final segments, durable viewer identities, causes, recommendation effects, headroom, or that replay occurred on the dominant title. It says nothing about the choice set each profile actually faced; entitlement, catalogue and language opportunity are conditioned separately.
