# Viewer-diagnosis evidence

**Question:** does similar surface concentration conceal different responses after content is chosen?

**Why it matters:** concentration describes where attention accumulated, not whether the concentrated choices worked. If similar concentration sits above different post-choice behaviour, concentration cannot define a segment on its own.

This folder holds behavioural mechanism evidence, and — since Test 5 — the same mechanisms read against the catalogue each profile could realistically reach. The measurement decisions it depends on — known-outcome completion, the 14-day replay horizon and the separation of resume from replay — are recorded with their evidence in [`../mart_audit`](../mart_audit/README.md#test-4--post-choice-response-and-the-bridge-from-concentration-to-mechanism). Everything here is a compact result extract, not a profile-level or mart dataset.

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

## Opportunity conditioning (Test 5)

**Question:** do the candidate mechanisms still describe behaviour once profiles are compared under comparable realistic opportunity, or was some of that difference unequal access wearing a behavioural disguise?

The three tables below share one population restriction. Opportunity structure is taken from the regimes published in [`opportunity_regime_summary.csv`](../mart_audit/opportunity_regime_summary.csv), and the comparisons keep only profile-windows with `FULL_90` entitlement in a *stable* regime — one access context for the whole window, either broad (`ALL_ACCESS`, `ALL_ACCESS_SPORTS`) or regional. That is 7,531 profile-windows in `BASELINE_90` and 8,396 in `FINAL_90`. `MIXED_ACCESS` and partial entitlement are excluded from the contrasts rather than averaged into them: a profile whose access changed mid-window has no single choice set to compare.

`BROAD` and `REGIONAL` are opportunity families, not plans and not viewer types. Reachable means the title was released, in the catalogue and within the profile's plan and audio entitlement on at least one entitled day — not that it was surfaced, recommended, noticed or considered.

### `opportunity_family_activity_contrasts.csv`

**Grain:** one row per window × control type × control quintile — 20 rows. Each row puts broad and regional profiles side by side inside the same activity quintile. Quintiles are `NTILE(5)` within the stable population of that window, formed separately for qualified watch hours (`WATCH_HOURS`) and active days (`ACTIVE_DAYS`); the two controls are never combined into one score.

**Columns:** `broad_profiles` and `regional_profiles` are the row's denominators. Every other quantity appears three times — `broad_avg_*`, `regional_avg_*` and a difference — covering the control metric itself, the other activity metric (to show the control did not quietly equalise both), reachable parent titles, meaningful titles, top-title share, valid title HHI and the diagnostic per-100-reachable ratio. Each difference is regional minus broad, so a negative `reachable_title_difference` means the regional group had the smaller reachable catalogue. `top_title_share_difference_pp` is in percentage points; the rest are in their own units. Values are rounded to four decimal places.

**What it supports:** that access sets the size of the choice set far more than it sets how far viewing spreads inside it. Holding activity constant, regional profiles reach 32% to 35% of the broad group's catalogue, yet watch only 5% to 23% fewer meaningful titles, while the concentration differences stay small and inconsistent in sign (between -2.7 and +2.7 percentage points of top-title share).

**What it does not prove:** that regional viewers are more efficient catalogue users, that broad access is under-used, or that the gap is convertible viewing. A larger reachable catalogue is a wider boundary, not an unmet demand.

### `genre_structure_incremental_models.csv` and `genre_structure_support_summary.csv`

**Question:** does genre structure explain concentration beyond breadth, activity and opportunity regime — enough to replace the title-level story?

**Grain of the model table:** one row per window × control type × outcome — 8 rows. Each row fits two cross-validated linear models on the same profiles and reports both. The base model predicts the outcome from log meaningful titles, the log control metric, both squared, and opportunity-regime indicators. The expanded model adds two genre-structure measures: distinct meaningful genres, and the share of meaningful titles sitting in the dominant genre. Fit is five-fold out-of-sample with folds assigned deterministically per profile, so `base_cv_r2` and `expanded_cv_r2` are held-out values rather than in-sample fit.

| Column | Meaning |
| --- | --- |
| `outcome` | `top_title_qualified_share`, or `title_hhi` on the profiles whose HHI is defined |
| `n_profiles` | Profiles in the model — smaller for `title_hhi` because undefined-HHI rows are dropped |
| `base_cv_r2`, `expanded_cv_r2`, `delta_cv_r2` | Out-of-sample R² before and after adding genre structure, and the gain |
| `base_cv_rmse`, `expanded_cv_rmse`, `rmse_improvement` | The same comparison in error units |

**What it supports:** genre structure adds information and never subtracts it — every `delta_cv_r2` is positive — but the gain runs from 0.003 to 0.011 R² on a base that already explains 0.77 to 0.84. Genre composition therefore stays supporting context for how breadth is composed. It does not replace title breadth or title concentration, and it is not an opportunity denominator: the marts define no genre-level choice set.

**The support table** describes the matched peer-stratum comparison run beside these models, not the models themselves. Profiles were grouped into strata of comparable breadth, activity and opportunity, and only strata of at least 20 profiles were retained; the table reports how much of the stable population those strata covered — 76% to 82%, across 91 to 112 retained strata — so a reader can judge how representative that matched comparison was. The stratum-level and profile-level tables behind it stay in the analysis environment.

### `opportunity_conditioned_candidate_mechanisms.csv`

**Produced by:** the Test 4 breadth × concentration query, [`concentration_mechanism_controls.sql`](../../sql/diagnostics/concentration_mechanism_controls.sql), carried forward unchanged and then read inside opportunity families. The Test 4 activity quintiles are deliberately *not* re-bucketed within the stable population, so each state keeps the definition and the benchmarks it had in Test 4. That also means the quintile boundaries here come from the full eligible population, while the boundaries in the two tables above come from the stable population. The two are not interchangeable.

**Grain:** one row per window × state × opportunity family × control type — 48 rows. `state_scope` separates the two kinds of row:

| `state_scope` | `state` | What it is |
| --- | --- | --- |
| `TEST4_ANCHOR` | `FOCUSED_SUCCESSFUL` (C5_B1), `SELECTIVE_CORE_ATTACHMENT` (C4_B3), `SUCCESSFUL_FIRST_PASS` (C3_B2), `BROAD_DISTRIBUTED` (C1_B5) | The four candidate states earned in Test 4, named by concentration quintile × breadth quintile |
| `NEIGHBOURING_STATE` | `C4_B1`, `C5_B2` | The two adjacent cells examined because they might belong to the same families — carried as neighbours, never as established candidates |

**Denominators and support.** `profiles` counts the state's profiles in that family; `benchmark_profiles` counts the comparable-activity profiles they are measured against. `completion_measured_profiles` and `replay_measured_profiles` are the profiles that met each metric's evidence threshold (at least 5 known completion outcomes, at least 3 known 14-day replay outcomes), and benchmark rates are averaged over those same measured profiles rather than over every benchmark member. The three `min_occupied_cell_*` columns give the thinnest occupied activity-quintile cell contributing to the row. A row's own strength is read from its measured-profile counts; the minimum-cell columns say how evenly that evidence was spread, and a minimum under 30 is why a neighbouring state stays review-only even when its aggregate deviation looks clear. They are published because a single thin cell is exactly what an aggregate deviation hides. Deviations are percentage points, rates are fractions, and values are rounded to four decimal places. Continuation was computed internally but is not published here: it is episodic-specific, and no Test 5 conclusion rests on it.

**What it supports:** that the strongest Test 4 mechanisms survive opportunity conditioning — the selective-core and focused-successful patterns keep their direction against both activity controls under broad access — while the neighbouring states become access-sensitive or support-limited, as set out in [journal entry 15](../../docs/analysis_journal.md#15-a-large-catalogue-is-not-the-same-thing-as-a-large-choice-set).

**What it does not prove:** segments, durable identities, causes or headroom. Where regional support was too thin for a confident comparison — visible directly in the measured-profile and minimum-cell columns — the result stays inadequate instead of becoming a weaker claim in the same direction.
