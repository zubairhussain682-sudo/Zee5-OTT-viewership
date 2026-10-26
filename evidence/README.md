# Evidence

Compact result tables that support what the documentation claims. No raw data, no mart extracts and nothing at profile grain — full-resolution tables stay in the analysis environment ([why](../data/README.md)).

The folder is split by what a file is for, not by when it was produced:

- **[`mart_audit/`](mart_audit/README.md) — does a measure mean what it claims?** Contract checks and the human semantic audit of the marts: grain, coverage, activity, breadth, concentration and the post-choice measurement decisions.
- **[`viewer_diagnosis/`](viewer_diagnosis/README.md) — what does the behaviour look like once the measures are trusted?** Behavioural mechanism results built on those measures.
- **[`segmentation/`](segmentation/README.md) — who was segmented, and what is each segment made of?** The verified investigated population, route-to-segment membership and each route's mechanism signature.

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
| [`test7_relational_validation_summary.csv`](mart_audit/test7_relational_validation_summary.csv) | Hours × active days and titles × hours partitions, with session and title-allocation evidence | Test 7 (relational) |

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
| [`test6d1_candidate_population_integration.csv`](viewer_diagnosis/test6d1_candidate_population_integration.csv) | The Test 4 candidate families carried into the paired population, with both ranking populations stated | Test 6D.1 |
| [`test6d2_candidate_opportunity_structure.csv`](viewer_diagnosis/test6d2_candidate_opportunity_structure.csv) | Final cross-origin opportunity distribution per candidate family, including its structural mass points | Test 6D.2 |
| [`test6d2_candidate_anchor_origin_composition.csv`](viewer_diagnosis/test6d2_candidate_anchor_origin_composition.csv) | Which Baseline anchor origins make up each candidate family | Test 6D.2 |
| [`test6d3a_raw_cross_origin_distribution.csv`](viewer_diagnosis/test6d3a_raw_cross_origin_distribution.csv) | Unstandardised Final cross-origin viewing per family, with the anchor-only share | Test 6D.3A |
| [`test6d3b_opportunity_band_behaviour.csv`](viewer_diagnosis/test6d3b_opportunity_band_behaviour.csv) | Behaviour inside five-point opportunity bands, with band support and common weights | Test 6D.3B |
| [`test6d3b_opportunity_standardised_summary.csv`](viewer_diagnosis/test6d3b_opportunity_standardised_summary.csv) | Raw against common-weight standardised candidate means | Test 6D.3B |
| [`test6d4_peer_adjusted_candidate_residuals.csv`](viewer_diagnosis/test6d4_peer_adjusted_candidate_residuals.csv) | Candidate-blind peer residuals by family, activity control and support population | Test 6D.4 |
| [`test6d4_programme_sensitivity.csv`](viewer_diagnosis/test6d4_programme_sensitivity.csv) | The same residuals with dominant programme type added to the peer key | Test 6D.4 |
| [`test6d5_within_candidate_residual_dispersion.csv`](viewer_diagnosis/test6d5_within_candidate_residual_dispersion.csv) | Residual spread inside each candidate family on the common-supported population | Test 6D.5 |
| [`test6d5_cross_control_robustness.csv`](viewer_diagnosis/test6d5_cross_control_robustness.csv) | Agreement between the two activity specifications, with quartile overlap | Test 6D.5 |
| [`test6d5_diagnostic_tail_context.csv`](viewer_diagnosis/test6d5_diagnostic_tail_context.csv) | What the stable residual tails actually watched, and the opportunity around them | Test 6D.5 |
| [`test6d5_focused_constituent_state_sensitivity.csv`](viewer_diagnosis/test6d5_focused_constituent_state_sensitivity.csv) | The same dispersion checks inside C5_B1 and C4_B1 separately | Test 6D.5 |
| [`test6d5_programme_tail_sensitivity.csv`](viewer_diagnosis/test6d5_programme_tail_sensitivity.csv) | Whether tail direction survives programme-matched peers, with surviving support | Test 6D.5 |
| [`test7_population_and_family_coverage.csv`](viewer_diagnosis/test7_population_and_family_coverage.csv) | Eligible, paired and window-only populations, and every family's size on each basis | Test 7.1–7.2 |
| [`test7_family_transition_matrix.csv`](viewer_diagnosis/test7_family_transition_matrix.csv) | Complete 6 × 6 Baseline-to-Final family matrix with within-family shares | Test 7.2 |
| [`test7_exact_state_transitions.csv`](viewer_diagnosis/test7_exact_state_transitions.csv) | The 233 observed exact concentration × breadth routes | Test 7.2 |
| [`test7_consumption_change_by_trajectory.csv`](viewer_diagnosis/test7_consumption_change_by_trajectory.csv) | Individual change in titles, hours, active days, top-title share and reach, by trajectory | Test 7.3 |
| [`test7_breadth_hours_joint_movement.csv`](viewer_diagnosis/test7_breadth_hours_joint_movement.csv) | Titles × hours direction groups, overall, for persistent families and by route | Test 7.3 / relational |
| [`test7_post_choice_outcomes.csv`](viewer_diagnosis/test7_post_choice_outcomes.csv) | Dual-supported completion, continuation and replay, by trajectory | Test 7.4 |
| [`test7_cross_origin_recurrence.csv`](viewer_diagnosis/test7_cross_origin_recurrence.csv) | Outside-anchor presence, recurrence and level against the fixed Baseline anchor | Test 7.6 |
| [`test7_integrated_family_pathways.csv`](viewer_diagnosis/test7_integrated_family_pathways.csv) | The cohort-level evidence behind the six family interpretations | Test 7.7 |

[`viewer_diagnosis/README.md`](viewer_diagnosis/README.md) documents that file's grain, denominators and interpretation boundary.

## Segmentation evidence — `segmentation/`

| File | What it holds | From |
| --- | --- | --- |
| [`investigated_population_ledger.csv`](segmentation/investigated_population_ledger.csv) | Every paired route: viewers who grew titles and hours, or titles without hours, and how many of each were advanced | Final pass |
| [`investigated_population_evidence_record.csv`](segmentation/investigated_population_evidence_record.csv) | The viewer-level evidence record: population, QA, coverage, outcome support and heterogeneity counts | Final pass |
| [`segment_route_membership.csv`](segmentation/segment_route_membership.csv) | The 27 routes, the segment each belongs to and the basis for its placement | Final pass |
| [`segment_summary.csv`](segmentation/segment_summary.csv) | Each segment's routes and profiles by track, reconciling to 6,228 | Final pass |
| [`route_mechanism_signature.csv`](segmentation/route_mechanism_signature.csv) | Each paired route's attention spread, kept-title hours, hours by title fate, title turnover and time organisation | Final pass |
| [`route_outcomes_and_context.csv`](segmentation/route_outcomes_and_context.csv) | Dual-supported post-choice outcomes, with replay as context only, and changes in reach, outside-anchor share and episodic share | Final pass |
| [`route_vs_parent_hours.csv`](segmentation/route_vs_parent_hours.csv) | Each selected route against its full parent transition and the not-selected remainder | Final pass |
| [`final_only_placement.csv`](segmentation/final_only_placement.csv) | Viewers without an eligible Baseline: profile age, Final scale, completion support and placement | Final pass |

[`segmentation/README.md`](segmentation/README.md) documents each table's grain, columns and interpretation boundary.

Behavioural results stay deliberately thin: a table is published when a claim needs it, not because the analysis produced it. The four Test 5 tables are grouped under [opportunity conditioning](viewer_diagnosis/README.md#opportunity-conditioning-test-5), which states the population restriction they share — full-window entitlement in a single stable access context — and why the activity quintiles behind the candidate-mechanism table are not the same quintiles as the ones behind the contrasts.

The Test 6 tables sit under [language and title origin](viewer_diagnosis/README.md#language-and-title-origin-test-6) and [Test 6D](viewer_diagnosis/README.md#test-6d--does-cross-origin-behaviour-add-information-inside-the-mechanisms) in the behavioural index and alongside the structural audit in [`mart_audit/README.md`](mart_audit/README.md#test-6a--multilingual-supply-before-any-behaviour). The Test 6C.4B programme and multilingual-intensity sensitivity is published alongside them; its peer-matched deviations are the final screen behind the conclusion that programme composition does not explain cross-origin heterogeneity away.

Two things are deliberately absent. Nothing here is at profile, peer-stratum or mart grain, so the profile-level opportunity, peer and genre extracts behind these summaries stay in the analysis environment. And the Test 5A reachable-catalogue reconciliation is not published as a table: it is enforced in process, before any output is written. `P01`–`P09` in [`mart_audit/measurement_checks.json`](mart_audit/measurement_checks.json) are not a substitute for it — they validate the historical opportunity semantics the marts already carry (entitled days, title exposure, eligibility, account roll-up), while `reachable_parent_titles_in_window` is a newer window-level measure derived from the same exposure. What is public for the derived measure is its implementation and the boundary tests in [`src/validation/test_opportunity.py`](../src/validation/test_opportunity.py); the reconciliation that preceded its analytical use is described in the [methodology](../docs/measurement_methodology.md#window-level-reachable-catalogue-the-same-grain-breadth-denominator) and [journal entry 15](../docs/analysis_journal.md#15-a-large-catalogue-is-not-the-same-thing-as-a-large-choice-set), and it ran in the analysis environment. The within-profile comparison has since landed: the Test 7 tables are documented under [the same viewers across two windows](viewer_diagnosis/README.md#test-7--the-same-viewers-across-two-windows), with the relational validation in the [audit record](mart_audit/README.md#test-7--two-relationships-validated-as-context-not-as-new-dimensions). One Test 7.7 result is deliberately not tabulated: the 3,565 provisional candidates and 1,100 breadth-only review track stay in the journal until their profile-ID advancement ledger has been independently audited. *Later note (final pass, 2026-10-26): that audit has since been completed, and the advancement counts are now tabulated by route in [`segmentation/investigated_population_ledger.csv`](segmentation/investigated_population_ledger.csv).*
