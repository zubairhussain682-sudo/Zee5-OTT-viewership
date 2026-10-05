# Evidence

Compact result tables that support what the documentation claims. No raw data, no mart extracts and nothing at profile grain — full-resolution tables stay in the analysis environment ([why](../data/README.md)).

The folder is split by what a file is for, not by when it was produced:

- **[`mart_audit/`](mart_audit/README.md) — does a measure mean what it claims?** Contract checks and the human semantic audit of the marts: grain, coverage, activity, breadth, concentration and the post-choice measurement decisions.
- **[`viewer_diagnosis/`](viewer_diagnosis/README.md) — what does the behaviour look like once the measures are trusted?** Behavioural mechanism results built on those measures.

A Test 4 file therefore sits in `mart_audit/` when it settles how something is measured (what counts as resume, which replay horizon is fair) and in `viewer_diagnosis/` when it reports behaviour (how post-choice response differs across breadth and concentration).

## Measurement evidence — `mart_audit/`

| File | What it holds | From |
| --- | --- | --- |
| [`measurement_checks.json`](mart_audit/measurement_checks.json) | 70 automated contract checks across both windows, with the human-review status of each audit block | Tests 1–4 |
| [`profile_viewership_hhi_by_breadth_final_90.csv`](mart_audit/profile_viewership_hhi_by_breadth_final_90.csv) | Median and 90th-percentile concentration at each exact breadth, with the `1/n` floor — the source for Figures 04 and 05 | Test 3 |
| [`post_choice_measurement_summary.csv`](mart_audit/post_choice_measurement_summary.csv) | Coverage and core post-choice rates per window, with each column's denominator stated | Test 4B–4C |
| [`completion_abandonment_axis.csv`](mart_audit/completion_abandonment_axis.csv) | The common-denominator test showing completion and abandonment are one outcome axis | Test 4C |
| [`return_decomposition.csv`](mart_audit/return_decomposition.csv) | Cross-session returns split into pre-completion resume, post-completion return and strict rewatch | Test 4C |
| [`resume_playback_continuity.csv`](mart_audit/resume_playback_continuity.csv) | Where a later session restarted relative to the previous endpoint — the evidence that resume is genuine | Test 4C |
| [`return_semantic_closure.csv`](mart_audit/return_semantic_closure.csv) | Eventual outcome of resumed assets — the source for Figure 09 | Test 4C |
| [`rewatch_latency_observability.csv`](mart_audit/rewatch_latency_observability.csv) | First-rewatch latency and available follow-up — the source for Figures 10A and 10B | Test 4C |
| [`rewatch_horizon_summary.csv`](mart_audit/rewatch_horizon_summary.csv) | Replay outcomes and censoring at horizons from 1 to 60 days | Test 4C |
| [`rewatch_profile_coverage.csv`](mart_audit/rewatch_profile_coverage.csv) | Profile-level evidence coverage behind the "at least three known outcomes" replay rule | Test 4C |
| [`opportunity_regime_summary.csv`](mart_audit/opportunity_regime_summary.csv) | Reachable catalogue, breadth, concentration and activity by window × entitlement timing × opportunity regime | Test 5B |
| [`catalogue_multilinguality_by_program_type.csv`](mart_audit/catalogue_multilinguality_by_program_type.csv) | How many audio languages parent titles carry, overall and by programme type | Test 6A |
| [`title_origin_vs_available_audio.csv`](mart_audit/title_origin_vs_available_audio.csv) | Titles originating in each language against titles offering it as audio | Test 6A |
| [`language_opportunity_by_access_regime.csv`](mart_audit/language_opportunity_by_access_regime.csv) | Reachable catalogue and its multilingual share by window and access regime | Test 6A |

[`mart_audit/README.md`](mart_audit/README.md) is the audit record itself: what each block asked, what passed, and the caveats attached.

## Behavioural evidence — `viewer_diagnosis/`

| File | What it holds | From |
| --- | --- | --- |
| [`concentration_mechanism_controls.csv`](viewer_diagnosis/concentration_mechanism_controls.csv) | Completion and 14-day replay by breadth × concentration cell, with separate watch-hours and active-days controls — the source for Figures 11A and 11B | Test 4D |
| [`opportunity_family_activity_contrasts.csv`](viewer_diagnosis/opportunity_family_activity_contrasts.csv) | Broad against regional access inside the same activity quintile: reachable catalogue, breadth and concentration | Test 5C |
| [`genre_structure_incremental_models.csv`](viewer_diagnosis/genre_structure_incremental_models.csv) | How much genre structure adds to concentration models that already hold breadth, activity and opportunity | Test 5C |
| [`genre_structure_support_summary.csv`](viewer_diagnosis/genre_structure_support_summary.csv) | Coverage of the matched peer strata behind that genre comparison | Test 5C |
| [`opportunity_conditioned_candidate_mechanisms.csv`](viewer_diagnosis/opportunity_conditioned_candidate_mechanisms.csv) | The Test 4 candidate states, and two neighbouring states, re-read inside broad and regional opportunity | Test 5D |
| [`consumed_vs_opportunity_language.csv`](viewer_diagnosis/consumed_vs_opportunity_language.csv) | Consumed-language breadth and concentration against the reachable audio environment, by window and access regime | Test 6B |
| [`cross_origin_anchor_and_opportunity.csv`](viewer_diagnosis/cross_origin_anchor_and_opportunity.csv) | Baseline title-origin anchors, and cross-origin viewing against historically valid cross-origin opportunity | Test 6C |
| [`cross_origin_direction_cross_tab.csv`](viewer_diagnosis/cross_origin_direction_cross_tab.csv) | Every paired profile classified by the direction of its behavioural change against the direction of its opportunity change | Test 6C.3 |
| [`test6c4b_programme_multilingual_sensitivity.csv`](viewer_diagnosis/test6c4b_programme_multilingual_sensitivity.csv) | Cross-origin deviation from matched peers by dominant programme type and multilingual-title intensity | Test 6C.4B |

[`viewer_diagnosis/README.md`](viewer_diagnosis/README.md) documents that file's grain, denominators and interpretation boundary.

Behavioural results stay deliberately thin: a table is published when a claim needs it, not because the analysis produced it. The four Test 5 tables are grouped under [opportunity conditioning](viewer_diagnosis/README.md#opportunity-conditioning-test-5), which states the population restriction they share — full-window entitlement in a single stable access context — and why the activity quintiles behind the candidate-mechanism table are not the same quintiles as the ones behind the contrasts.

The Test 6 tables sit under [language and title origin](viewer_diagnosis/README.md#language-and-title-origin-test-6) in the behavioural index and alongside the structural audit in [`mart_audit/README.md`](mart_audit/README.md#test-6a--multilingual-supply-before-any-behaviour). The Test 6C.4B programme and multilingual-intensity sensitivity is published alongside them; its peer-matched deviations are the final screen behind the conclusion that programme composition does not explain cross-origin heterogeneity away.

Two things are deliberately absent. Nothing here is at profile, peer-stratum or mart grain, so the profile-level opportunity, peer and genre extracts behind these summaries stay in the analysis environment. And the Test 5A reachable-catalogue reconciliation is not published as a table: it is enforced in process, before any output is written. `P01`–`P09` in [`mart_audit/measurement_checks.json`](mart_audit/measurement_checks.json) are not a substitute for it — they validate the historical opportunity semantics the marts already carry (entitled days, title exposure, eligibility, account roll-up), while `reachable_parent_titles_in_window` is a newer window-level measure derived from the same exposure. What is public for the derived measure is its implementation and the boundary tests in [`src/validation/test_opportunity.py`](../src/validation/test_opportunity.py); the reconciliation that preceded its analytical use is described in the [methodology](../docs/measurement_methodology.md#window-level-reachable-catalogue-the-same-grain-breadth-denominator) and [journal entry 15](../docs/analysis_journal.md#15-a-large-catalogue-is-not-the-same-thing-as-a-large-choice-set), and it ran in the analysis environment. Later within-profile comparison will land here too.
