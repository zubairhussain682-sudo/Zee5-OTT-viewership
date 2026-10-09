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

## Language and title origin (Test 6)

**Question:** does language behaviour add anything once the multilingual supply behind it is known — and if consumed-language breadth is not enough, does movement across catalogue-origin ecosystems survive the opportunity that made it possible?

Two rules travel with both tables. Native language is **not observed**: `home_region`, regional plan language and title origin are contextual fields, so nothing here is described as native, mother-tongue or non-native viewing. And the three language observations stay separate — a title's origin, the audio offered on it, and the track actually consumed answer different questions, so a dubbed title keeps its origin however it was watched.

### `consumed_vs_opportunity_language.csv`

**Produced by:** the Test 6B language-behaviour analysis, which joins qualified viewing to the historically valid language opportunity behind it. The profile-level language distributions it was aggregated from are not published.

**Population and window:** analytically eligible profiles — 8,761 in `BASELINE_90` and 9,762 in `FINAL_90`, each window analysed separately.

**Grain:** one row per window × opportunity regime, plus an `ALL_REGIMES` row per window. The regime rows are the analysis output; the `ALL_REGIMES` rows are profile-weighted aggregations of them, exact because the regimes partition the eligible population (counts are summed, means are weighted by `profiles`).

| Column | Meaning |
| --- | --- |
| `avg_distinct_reachable_audio_languages` | Audio languages reachable at least once — a breadth measure that saturates near nine or ten |
| `avg_distinct_consumed_audio_languages` | Audio languages actually used by qualified viewing |
| `avg_top_consumed_language_watch_share`, `avg_consumed_language_hhi` | Concentration of playback across languages |
| `avg_opportunity_top_language_day_share`, `avg_opportunity_language_hhi_days` | The same concentration measures computed on title-day language opportunity |
| `avg_consumed_minus_opportunity_top_day_share_pp`, `avg_consumed_minus_opportunity_hhi_days` | The gap between the two, in percentage points and HHI units |
| `hhi_valid_profiles`, `profiles_consumption_more_concentrated_days` | The denominator and numerator behind "consumed is more concentrated than opportunity" |

**What it supports:** the aggregate window × opportunity-regime comparison. Playback is far more concentrated than the audio environment it happens in — consumed HHI exceeds opportunity HHI for 8,711 of 8,761 baseline profiles (99.43%) and 9,710 of 9,762 final profiles (99.47%) — and at regime level, broad-access profiles consume more languages, and less concentrated ones, than every regional family. It also shows why reachable-language *count* cannot be the denominator: it is nearly saturated, so the opportunity shares and HHI carry the comparison.

**Scope limit:** this table is aggregated to the regime level, so it does not itself demonstrate that the broad/regional difference survives activity conditioning. That check was run inside Test 6B against watch-hours and active-days quintiles separately and is reported in [journal entry 16](../../docs/analysis_journal.md#16-a-multilingual-catalogue-is-not-the-same-thing-as-multilingual-behaviour); the quintile-level output behind it is not published here.

**What it does not prove:** that plan family causes language concentration, or that any profile was expected to consume languages in proportion to supply. Access, catalogue composition, programme mix and behavioural selection are entangled observationally, and nothing here is a language-openness score.

### `cross_origin_anchor_and_opportunity.csv`

**Produced by:** the Test 6C analysis. Behaviour comes from [`test6c2_baseline_anchor_cross_origin_behaviour.sql`](../../sql/diagnostics/test6c2_baseline_anchor_cross_origin_behaviour.sql); the anchor-relative opportunity is reconstructed in Python from the same day-by-day exposure the marts use, with the public logic in [`origin.py`](../../src/analytical_transforms/origin.py). Profile-level anchors, behaviour and opportunity sidecars are not published.

**Population:** the paired population of 8,199 profiles eligible in *both* windows — about 93.6% of baseline and 84.0% of final eligible profiles.

**Grain:** one row per profile group, with `group_type` saying which kind of group:

| `group_type` | `group` | What it is |
| --- | --- | --- |
| `POPULATION` | `ALL_PAIRED`, `ANCHOR_70_PLUS`, `ANCHOR_70_95`, `ANCHOR_95_100` | Diagnostic sensitivity populations, aggregated from the bands below |
| `ANCHOR_SHARE_BAND` | `0.15-0.20` … `0.95-1.00` | 5-percentage-point bands of Baseline anchor share, as the analysis produced them |
| `ANCHOR_ORIGIN_LANGUAGE` | `Hindi`, `Bengali`, `Telugu`, … | Profiles grouped by their Baseline anchor origin |

The `POPULATION` rows are profile-weighted aggregations of the band rows, exact because the bands partition the paired population. They are **diagnostic slices, not segment thresholds**: the anchor-share distribution declines smoothly with no natural breakpoint, so ≥70% and 95–100% exist only because movement is easier to read from a clear starting centre.

**Columns.** `avg_baseline_cross_origin_title_day_share` and its final counterpart are historically valid *opportunity* — reachable title-days outside the fixed anchor over all reachable title-days. `avg_baseline_cross_origin_minute_share` and its final counterpart are *behaviour* — qualified minutes on titles originating outside the anchor. Opportunity and behaviour are deliberately adjacent, because the comparison between them is the finding. `pct_entered_new_origin_language`, `pct_cross_origin_share_increased` and `pct_stayed_only_in_baseline_anchor` are percentages; the shares are fractions.

**What it supports:** that cross-origin viewing moved much further than the opportunity behind it. Across all paired profiles, opportunity went from 63.7% to 64.7% while viewing went from 36.6% to 48.5%; for anchors at or above 70%, from 52.3% to 53.7% against 12.8% to 28.0%; and in the 95–100% band, from 26.2% to 28.5% against 0.5% to 10.5%, with 55.7% of that band still consuming nothing outside the anchor. Without cross-origin opportunity the behaviour cannot occur at all — so the point is not that opportunity is irrelevant, but that it does not mechanically determine the direction or size of the movement.

**What it does not prove:** causality in either direction, language openness, native-language preference, a stable tendency, a segment or headroom. Cross-origin viewing divided by cross-origin opportunity is not a conversion rate. One caveat belongs beside every reading of the strong-anchor rows: the Baseline anchor is by construction the largest Baseline origin share, so profiles selected for extreme Baseline concentration have more room to move away from it afterwards, and some regression toward a less extreme final distribution is expected.

### `cross_origin_direction_cross_tab.csv`

**Question:** when a profile's cross-origin viewing changed between the windows, had its cross-origin *opportunity* moved in the same direction?

**Why it matters:** the headline comparison shows that viewing moved much further than opportunity on average, but an average can hide a mechanical story in which almost everyone simply follows their own opportunity. This table opens the average up and asks whether the direction of opportunity change predicts the direction of behavioural change at all.

**Produced by:** the Test 6C.3 analysis, from the same reconstruction behind [`cross_origin_anchor_and_opportunity.csv`](cross_origin_anchor_and_opportunity.csv). Profile-level sidecars are not published.

**Population and grain:** the 8,199 paired profiles, each falling into exactly one of nine cells — behaviour direction (increased, decreased, effectively unchanged) × opportunity direction (the same three). All nine cells are published, including the three that are empty, so the partition is visible rather than implied. Profiles sum to 8,199.

| Column | Meaning |
| --- | --- |
| `share_of_paired_profiles` | The cell as a share of all 8,199 |
| `share_within_behavior_direction`, `share_within_opportunity_direction` | The same cell read down each margin |
| `avg_baseline_/avg_final_cross_origin_title_day_share`, `avg_cross_origin_title_day_share_change` | Opportunity before, after and the change |
| `avg_baseline_/avg_final_cross_origin_minute_share`, `avg_cross_origin_share_change` | Behaviour before, after and the change |
| `avg_baseline_/avg_final_cross_origin_reachable_titles` | Distinct cross-origin titles reachable, as a size check on the opportunity pool |
| `pct_entered_new_origin_language`, `avg_final_qualified_watch_hours`, `avg_final_active_days` | Movement and activity context for the cell |

**What it supports:** that opportunity direction barely predicts behavioural direction. Among the 7,275 profiles whose opportunity share rose, 64.1% increased their cross-origin viewing; among the 924 whose opportunity share fell, 66.5% did — a difference of about two points in the wrong direction for a mechanical account. The magnitudes make the same point: the largest cell combines a +1.5-point opportunity change with a +24.8-point viewing change, and the 614 profiles whose opportunity share *fell* still raised viewing by 24.6 points. It is the source for the group counts behind Figures 18 and 18B.

**What it does not prove:** causality in either direction, or that opportunity is irrelevant — cross-origin viewing cannot occur without cross-origin opportunity at all. Directions here are numerical signs with no materiality threshold, so many "rose" and "fell" changes are near zero; a falling *share* is also not the same as falling absolute opportunity, since the cross-origin pool grew in most of these cells.

### `test6c4b_programme_multilingual_sensitivity.csv`

**Question:** does programme composition or multilingual-title viewing intensity materially explain cross-origin behaviour, once profiles are compared against peers with comparable historical cross-origin opportunity and activity?

**Why it matters:** Test 6A had already shown that multilingual supply is heavily structured by programme type, so programme mix was the most plausible alternative explanation for the cross-origin heterogeneity. If it accounted for the pattern, there would be no behavioural tendency left to carry forward.

**Produced by:** the Test 6C.4B peer-matching analysis. Peer cells match exact Baseline dominant origin, 5-percentage-point Baseline anchor-share band, 5-percentage-point Final cross-origin title-day opportunity band, and activity quintile — with `ACTIVE_DAYS` and `WATCH_HOURS` run as separate versions rather than crossed. Profile-level peer expectations are not published.

**Population:** the paired Test 6C population of 8,199 profiles. `support_population` separates `ALL` from `PEER_N_GE_20`; **the primary interpretation is `PEER_N_GE_20`**, and that threshold is a support rule, not a behavioural one.

**Grain:** 40 rows — one per analysis dimension × level × control basis × support population, split evenly between 20 `PROGRAMME_TYPE` rows and 20 `MULTILINGUAL_INTENSITY_QUINTILE` rows.

**Reading a deviation:** `avg_cross_origin_deviation_pp` is the profile's Final cross-origin minute share minus its peer-cell expectation, in percentage points, averaged over the group. Positive means more cross-origin viewing than comparable peers. On the `PROGRAMME_TYPE` rows the peer-group columns (`avg_`, `median_`, `min_peer_group_size` and the `pct_profiles_peer_n_*` columns) carry the detailed peer-cell support diagnostics; on the `MULTILINGUAL_INTENSITY_QUINTILE` rows those columns are deliberately blank and support is carried by `support_population` and `profiles`. The completed 6C.4B analysis reconciled with zero failures, and the row-level `reconciliation_failures` field is populated only where the source programme-support table carried it.

**What it supports — programme:** the remaining associations are modest in the supported population, and consistent in direction across both activity controls.

| Dominant programme | vs active-days peers | vs watch-hours peers | Support |
| --- | ---: | ---: | --- |
| MOVIE | −1.75 pp | −1.68 pp | Well supported |
| WEB_SERIES | +2.35 pp | +2.10 pp | Well supported |
| TV_CATCHUP | +1.32 pp | +1.23 pp | Well supported |
| REALITY | +2.89 pp | +2.82 pp | Support-sensitive — 41 and 42 supported profiles |
| DOCUMENTARY_SPECIAL | +3.79 pp | +4.26 pp | Too thin — one supported profile |

The two thin rows are published rather than deleted, and they do not carry the conclusion.

**What it supports — multilingual-title intensity:** the peer-adjusted pattern is non-monotonic. In the supported population Q1 sits below peer expectation under both controls (−0.95 and −1.01 pp), Q2 marginally below (−0.17 and −0.39 pp), Q3 and Q4 above it (+1.19/+1.23 and +1.21/+1.13 pp), and Q5 falls back below (−1.32 and −0.94 pp). Q5 consists entirely of profiles at 100% multilingual-title minutes, and tied values at 100% also appear in Q4, so the Q4/Q5 boundary is a ranking artefact rather than a behavioural threshold. More multilingual-title viewing therefore does not mean progressively more cross-origin behaviour.

`multilingual_title_minute_share` is consumed minutes on titles that happen to offer several audio tracks. It is a consumption-composition measure and is never multilingual supply.

**What it does not establish:** a causal programme effect, psychological language openness, a stable identity, segment membership, persistence or headroom. Differences between the `ALL` and `PEER_N_GE_20` populations also carry population-selection effects and must not be attributed to opportunity matching alone.

## Test 6D — does cross-origin behaviour add information inside the mechanisms?

**Question:** cross-origin movement survived Test 6C's structural explanations, but that did not show it told us anything the candidate mechanisms had not already said. Test 6D asks whether it is **non-redundant**: after holding the mechanism fixed and conditioning on anchor structure, historical opportunity and activity, do profiles inside the same mechanism still differ in how far their viewing extends beyond their Baseline origin centre?

**Why it matters:** a second measure of the same underlying behaviour is not a second piece of evidence. If cross-origin behaviour were implicit in the mechanisms, carrying it forward would complicate the eventual headroom diagnosis without strengthening it.

**Decision recorded by these tables:** pass for provisional carry-forward as a non-redundant, cross-cutting behavioural dimension. Nothing here establishes incremental viewing, a causal effect, longitudinal persistence, a final segment or realisable headroom.

**Four populations run through this set, and they are not interchangeable:**

| Population | Profiles | Used for |
| --- | ---: | --- |
| Full Final-eligible | 9,762 | Ranking the original Test 4 breadth × concentration states, before pairing |
| Paired | 8,199 | Eligible in both windows; the Test 6D analysis population, and the ranking population for peer-matching activity quintiles |
| Common opportunity-band | 7,092 | The four shared opportunity bands used for standardised comparison (86.5% of paired) |
| Common-supported | 5,510 | Peer cells of at least 20 profiles under **both** activity controls (67.2% of paired) |

Findings from a smaller population do not generalise to a larger one, and the tables carry their own counts so a reader can see which applies.

### Population and opportunity structure

[`test6d1_candidate_population_integration.csv`](test6d1_candidate_population_integration.csv) — one row per candidate family: its original Test 4 states, profile count and share of the paired population, with both ranking populations stated. Membership comes from the Final-window state construction ranked over 9,762 profiles and joined without reranking, so no candidate is redefined by anything Test 6D measures. The six families sum to 8,199.

[`test6d2_candidate_opportunity_structure.csv`](test6d2_candidate_opportunity_structure.csv) — the Final cross-origin title-day opportunity distribution for each family: mean, median, p10/p25/p75/p90, the Baseline comparison and anchor-strength context. The distributions are kept rather than reduced to means because they are lumpy: large parts of the population sit at opportunity shares near 57.6%, 89.4% and 92.3%. Those are structural mass points produced by catalogue composition and historical access, **not** discovered behavioural thresholds. Mean opportunity runs from 57.5% (Broad Distributed) to 73.3% (Access-Sensitive Neighbour).

[`test6d2_candidate_anchor_origin_composition.csv`](test6d2_candidate_anchor_origin_composition.csv) — which Baseline anchor origins make up each family. This is where the arithmetic behind the opportunity differences becomes visible: Broad Distributed is about 80% Hindi-anchored, and Hindi is the largest origin ecosystem in the catalogue, so a Hindi anchor leaves proportionally less reachable catalogue outside it. The opportunity measure describes the share of accessible catalogue outside the reference ecosystem — it is not a measure of who is adventurous.

### Raw behaviour, bands and standardisation

[`test6d3a_raw_cross_origin_distribution.csv`](test6d3a_raw_cross_origin_distribution.csv) — actual, unstandardised Final cross-origin minute share per family: mean, median, quartiles and the share of profiles that watched **nothing** outside their anchor. It is the table behind the central observation that Focused Successful and the Access-Sensitive Neighbour average 41.3% and 41.9% while 26.9% and 9.8% of them respectively are anchor-only. Percentiles use linear interpolation, stated in the file.

[`test6d3b_opportunity_band_behaviour.csv`](test6d3b_opportunity_band_behaviour.csv) — behaviour inside five-percentage-point bands of Final cross-origin opportunity, one row per family × band, with the band's support flags and its common weight. **A band describes the available choice environment, not the viewing outcome:** a profile in the 55–60% band had roughly that share of its reachable parent-title-days outside its anchor language, which says nothing about what it watched, nor about what was surfaced or considered.

[`test6d3b_opportunity_standardised_summary.csv`](test6d3b_opportunity_standardised_summary.csv) — each family's raw mean beside its common-weight standardised mean, with support coverage. Standardisation applies one shared set of band weights to every family, so the comparison runs through the same mix of opportunity bands; it changes no profile's viewing or opportunity and estimates no causal effect. Raw and standardised answer different questions and neither replaces the other. Standardised to the common distribution, Focused Successful and the neighbour land at 35.7% and 35.8% — and still differ underneath.

**Banding is not matching.** Sharing a band does not equalise anchor origin, anchor strength, activity or programme composition, which is precisely why the peer adjustment follows.

### Peer-adjusted residuals

[`test6d4_peer_adjusted_candidate_residuals.csv`](test6d4_peer_adjusted_candidate_residuals.csv) — one row per family × activity control × support population (`ALL` and `PEER_N_GE_20`), with actual share, peer expectation, mean and median residual, quartiles, the share above and below peers, peer-group sizes and retention. Peer cells match exact Baseline anchor origin, 5-point anchor-strength band, 5-point Final opportunity band and Final activity quintile; **candidate family is deliberately not in the key**, since a candidate-specific benchmark would be built from the distinction under evaluation. Activity quintiles are ranked over the 8,199 paired profiles — recorded in the file as `activity_quintile_population` — and the expectation is the inclusive peer-cell mean, recorded as `peer_expectation_convention`.

Supported candidate means sit within about ±6 pp of peer expectation: Focused Successful −1.91/−1.76 pp, Selective Core +2.62/+2.25, Access-Sensitive Neighbour −6.06/−4.26, Successful First-Pass +4.31/+5.01, Broad Distributed −1.27/−1.01 and residual states +0.90/+0.54, under the active-days and watch-hours controls respectively. Broad Distributed looked naturally cross-origin in the raw data yet sits close to expectation once context is accounted for.

[`test6d4_programme_sensitivity.csv`](test6d4_programme_sensitivity.csv) — the same comparison with dominant Final programme type added to the peer key, carrying the core result on the same profiles for comparison. It narrows the Access-Sensitive Neighbour's gap without reversing it, and it materially reduces support, so it is sensitivity evidence rather than a replacement for the core residual.

### Dispersion inside the mechanism

[`test6d5_within_candidate_residual_dispersion.csv`](test6d5_within_candidate_residual_dispersion.csv) — residual distribution per family × control on the common-supported population: mean, median, p10/p25/p75/p90, interquartile range and median absolute deviation. The IQR matters more than the mean here, because large positive and negative residuals offset one another: Focused Successful's middle half spans roughly 46 pp around a mean of about −1.6.

[`test6d5_cross_control_robustness.csv`](test6d5_cross_control_robustness.csv) — Spearman and Pearson correlation between the two specifications, sign agreement and reversal, mean absolute difference, and the quartile-overlap counts including `stable_low` and `stable_high`. For Focused Successful: ρ = 0.985, 97.8% keeping the same sign, 91.1% and 94.4% quartile overlap. **This is robustness, not replication** — both specifications benchmark the same Final outcome and share most matching variables, so agreement says the reading is not an artefact of one activity benchmark. It says nothing about persistence over time.

[`test6d5_diagnostic_tail_context.csv`](test6d5_diagnostic_tail_context.csv) — what the tails actually look like: for each family's `STABLE_LOW` and `STABLE_HIGH` groups, actual cross-origin viewing, opportunity, Baseline anchor share and residuals. Inside Focused Successful, 195 low-tail profiles averaged 11.7% actual cross-origin viewing against 92.7% for 202 high-tail profiles — about 81 points apart — while their outside-anchor opportunity (77.0% against 76.8%) and anchor strength (67.4% against 66.4%) were nearly identical. These are group-level comparisons, not matched pairs, and the quartiles are positional diagnostics rather than propensity categories.

[`test6d5_focused_constituent_state_sensitivity.csv`](test6d5_focused_constituent_state_sensitivity.csv) — the same checks inside C5_B1 and C4_B1 separately, showing the dispersion exists within the constituent states rather than arising from pooling them into one family.

[`test6d5_programme_tail_sensitivity.csv`](test6d5_programme_tail_sensitivity.csv) — whether tail profiles keep their direction once programme type joins the peer key, with the surviving support for each tail. High directional agreement on low coverage establishes consistency within the comparable subset only.

**What this set does not prove:** that cross-origin movement produces additional viewing time, that any difference is caused by access, programme or recommendation, that these behaviours persist beyond the Final window, or that any tail group is a segment. The `stable_low` and `stable_high` labels mean the same profiles occupied the same residual quartile under both Final-window activity controls — nothing more.
