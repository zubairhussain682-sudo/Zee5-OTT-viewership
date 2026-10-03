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

[`mart_audit/README.md`](mart_audit/README.md) is the audit record itself: what each block asked, what passed, and the caveats attached.

## Behavioural evidence — `viewer_diagnosis/`

| File | What it holds | From |
| --- | --- | --- |
| [`concentration_mechanism_controls.csv`](viewer_diagnosis/concentration_mechanism_controls.csv) | Completion and 14-day replay by breadth × concentration cell, with separate watch-hours and active-days controls — the source for Figures 11A and 11B | Test 4D |

[`viewer_diagnosis/README.md`](viewer_diagnosis/README.md) documents that file's grain, denominators and interpretation boundary.

Behavioural results stay thin on purpose: only one table has so far earned publication, because measurement had to be settled first. Later tests add opportunity conditioning and within-profile comparison, and their results will land here.
