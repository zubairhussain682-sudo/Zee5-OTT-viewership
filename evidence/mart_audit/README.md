# Mart audit evidence

**Question:** before any viewer-level measure is trusted, do the analytical marts actually hold what they claim to?

**Why it matters:** a fingerprint or segment built on a mart that silently duplicates rows, inherits access a profile never had, or treats unobserved follow-up as a negative outcome would look numerically plausible and still be wrong.

[`measurement_checks.json`](measurement_checks.json) records 70 automated contract checks across both viewership windows. Every check passes. The file holds check outcomes only — it contains no population measures, distributions or findings.

| Check family | What it establishes |
| --- | --- |
| `K01`–`K12` | Each mart is unique at its declared grain; no orphan profiles, accounts or parent titles; window boundaries are ordered and complete |
| `P01`–`P09` | Profile opportunity never exceeds the days a profile existed, title exposure equals an independent day-by-day reconstruction, eligibility follows its stated rule, and account eligible-profile counts add up from profiles |
| `C*` | Continuation opportunities are unique, follow episode order within a parent title, open only when the next episode is reachable, carry exactly one outcome state, and reconcile from title rows to profile rows |

**Interpretation:** passing these checks establishes that the mart grain, opportunity and continuation contracts hold. Automated checks do not by themselves prove that every mart field is suitable for downstream behavioural measurement — that judgment belongs to human semantic review. `profile_title_window` has completed that review; `profile_viewership_window` is being reviewed in blocks, [recorded below](#human-semantic-audit-profile_viewership_window). Nor does a suitable field automatically become a fingerprint input: each candidate measure still needs its own review of distribution, stability and redundancy.

The validation logic is published and inspectable. Re-running the full contract suite requires the full-resolution source and mart tables, which are intentionally not stored in this repository.

- `P01`–`P09` come from [`opportunity_checks.py`](../../src/validation/opportunity_checks.py), which rebuilds historical access and title availability day by day from the source tables, sharing neither the access matrix nor the catalogue logic used to build the marts — so agreement is evidence, not a restatement.
- The `C*`, `CT_*` and `CV_*` continuation checks come from [`continuation_checks.py`](../../src/validation/continuation_checks.py), which tests each opportunity against the source tables and then confirms both marts reproduce those opportunities exactly.

Small deterministic fixtures in [`src/validation`](../../src/validation) exercise the same rules at their boundaries — profile creation mid-window, access gaps, regional entitlement, catalogue release and exit, and the seven-day continuation horizon — without needing the full tables.

## Human semantic audit: `profile_viewership_window`

The viewer-level base is reviewed in blocks, each asking whether a family of fields means what downstream measurement needs it to mean. Results below were recorded from the audit run; the queries are published, the full tables are not.

| Block | Scope | Status |
| --- | --- | --- |
| Test 1 | Grain, coverage and row semantics | PASS |
| Test 2 | Activity, volume and session measures | PASS |
| Test 3 | Breadth and concentration | PASS WITH CAVEAT |
| Test 4 | Post-choice response and its link to breadth and concentration | PASS WITH MEASUREMENT DECISIONS |
| Test 5 | Opportunity measures used for realistic-choice conditioning | PASS |
| Test 6A | Multilingual catalogue supply and language opportunity | PASS WITH CAVEAT |
| Next | Reintegration of cross-origin behaviour into the mechanism candidates | Not yet reviewed |

**PASS WITH CAVEAT** records a bounded semantic imperfection that does not threaten the project objective, downstream denominators, analytical eligibility or the interpretation of the populations actually used. The imperfection is documented and the affected rows are excluded from the relevant interpretation; the mart is not rebuilt for it.

**PASS WITH MEASUREMENT DECISIONS** records that the stored fields reconcile, but that behavioural use requires explicit decisions about denominators, observability or scope. The decisions are made from components the mart already carries; the mart is not rebuilt.

### Test 1 — grain, coverage and row semantics

Queries: [`profile_viewership_grain_coverage.sql`](../../sql/mart_audit/profile_viewership_grain_coverage.sql).

| | BASELINE_90 | FINAL_90 |
| --- | ---: | ---: |
| Window | 2025-09-01 to 2025-11-29 | 2025-11-30 to 2026-02-27 |
| Rows / distinct profiles | 13,037 / 13,037 | 13,037 / 13,037 |
| No playback | 1,841 | 976 |
| Playback but no qualified start | 30 | 34 |
| At least one qualified start | 11,166 | 12,027 |
| No meaningful title | 1,871 | 1,010 |
| Main-analysis eligible | 8,761 | 9,762 |

Every profile appears in both windows at profile × window grain. Semantic contradiction checks returned zero rows: qualified minutes above total minutes, qualified active days above active days, meaningful titles above titles touched, disagreement between the meaningful-title fields, no-playback rows carrying viewing, activity or session values, and meaningful titles on rows without a qualified start. Representative inactive, unqualified, qualified-but-ineligible and eligible profiles were also inspected by hand.

**Meaning of the pass:** the mart is coherent at its grain, keeps profiles that watched nothing, separates raw activity from qualified engagement, carries opportunity independently of realised viewing, and treats eligibility as evidence sufficiency rather than behavioural identity.

### Test 2 — activity, volume and session measures

Queries: [`profile_viewership_activity_invariants.sql`](../../sql/mart_audit/profile_viewership_activity_invariants.sql) (descriptive shape and internal invariants) and [`profile_viewership_raw_reconciliation.sql`](../../sql/mart_audit/profile_viewership_raw_reconciliation.sql) (rebuilt from `viewing_sessions` and `view_events`).

**Internal invariants — zero violations** in both windows: autoplay events, qualified starts and sessions never exceed events; active days never exceed the window and qualified active days never exceed active days; watch-hour, qualified-watch-hour and sessions-per-active-day derivations hold; session summaries appear exactly when sessions exist and are mutually consistent; timestamps are ordered, absent on rows without playback and present on rows with it.

**Reconciliation with raw playback:**

| Measure | Result |
| --- | --- |
| Event count, autoplay count, active days | Exact — 0 mismatches in both windows |
| `first_event_ts`, `last_event_ts` | Exact — 0 mismatches against the earliest and latest event **start** timestamps |
| Session count | Exact — 0 mismatches in both windows |
| Watch minutes | Within numerical precision — no profile differs by more than 0.001 minute |
| Session minutes, mean, median and longest session | Within numerical precision — no profile differs by more than 0.001 minute |

Minutes are not literally identical to their rebuilt values, and are not presented as such. Under a deliberately strict 0.000001-minute tolerance, thousands of profiles show a difference; none survives a 0.001-minute tolerance, and there is no systematic direction.

| Watch-minute difference | BASELINE_90 | FINAL_90 |
| --- | ---: | ---: |
| Profiles above 0.000001 min | 7,490 | 7,971 |
| Profiles above 0.001 min | 0 | 0 |
| Largest absolute difference (min) | 0.000033 | 0.000033 |
| Mean absolute difference (min) | 0.000019 | 0.000020 |
| Net signed difference, all profiles (min) | 0.002533 | 0.000233 |

| Session-duration difference | BASELINE_90 | FINAL_90 |
| --- | ---: | ---: |
| Profiles above 0.000001 min — total / mean / median / longest | 11,123 / 9,837 / 10,875 / 10,987 | 11,970 / 10,660 / 11,692 / 11,834 |
| Largest difference — total session minutes | 0.000954 | 0.000996 |
| Largest difference — mean / median / longest | ≤ 0.00005 | ≤ 0.00005 |

The largest watch-minute gap is about 0.002 seconds. The magnitudes are consistent with harmless numerical representation and rounding differences across the reconstruction and stored mart values. Watch minutes (playback summed over events) and session minutes (elapsed session time) are distinct constructs and are not reconciled against each other.

**Meaning of the pass:** activity, volume and session measures are semantically coherent and reproducible from the raw playback and session layer. Counts and timestamps reconcile exactly; watch-time and session-duration differences are confined to analytically negligible numerical precision.

### Test 3 — breadth and concentration

Queries: [`profile_viewership_breadth_reconciliation.sql`](../../sql/mart_audit/profile_viewership_breadth_reconciliation.sql) (3A–3B), [`profile_viewership_title_concentration.sql`](../../sql/mart_audit/profile_viewership_title_concentration.sql) (3C) and [`profile_viewership_genre_concentration.sql`](../../sql/mart_audit/profile_viewership_genre_concentration.sql) (3D).

| Block | Scope | Result |
| --- | --- | --- |
| 3A | Breadth against raw playback, `profile_title_window` and `profile_genre_window` | PASS — distinct assets, parent titles, genres, consumed audio languages, meaningful titles and meaningful genres: 0 mismatches in both windows |
| 3B | Effect of qualification on breadth | Descriptive — see below |
| 3C.1 | Title concentration against `profile_title_window` | PASS — qualified minutes, minutes outside meaningful titles (0), meaningful-title counts, top-title minutes and share, title HHI, and HHI validity at ≥ 3 meaningful titles: 0 mismatches |
| 3C.2 | Breadth × concentration | Descriptive — see below |
| 3D.1 | Genre concentration against `profile_genre_window` | PASS WITH CAVEAT — meaningful-genre counts, top-genre share, genre HHI and their bounds: 0 mismatches; `genre_hhi` populated for 30 / 34 profiles with no meaningful genre |
| 3D.2 | Title versus genre concentration | Descriptive — see below |

**3B — qualification effect, profiles with any playback:**

| | BASELINE_90 | FINAL_90 |
| --- | ---: | ---: |
| Active profiles | 11,196 | 12,061 |
| Losing ≥ 1 title | 2,351 (21.00%) | 2,324 (19.27%) |
| Titles lost: 0 / 1 / 2 / 3+ | 8,845 / 1,710 / 414 / 227 | 9,737 / 1,685 / 415 / 224 |
| Average raw → meaningful titles | 13.10 → 12.80 | 16.40 → 16.12 |
| Average meaningful-title retention | 97.52% | 98.17% |
| Losing ≥ 1 genre | 681 (6.08%) | 581 (4.82%) |
| Average meaningful-genre retention | 98.23% | 98.67% |
| Eligible profiles losing ≥ 1 title | 2,183 of 8,761 | 2,223 of 9,762 |

Qualification removes shallow catalogue touches without materially rewriting breadth. Genre changes are descriptive only; genre opportunity is not normalised.

**3C.2 — breadth and concentration, eligible profiles with valid title HHI:**

| | BASELINE_90 | FINAL_90 |
| --- | ---: | ---: |
| Profiles | 7,897 | 8,698 |
| Meaningful titles, min / average / max | 3 / 17.31 / 319 | 3 / 21.67 / 387 |
| Average top-title share | 0.3727 | 0.3304 |
| Average adjusted top-title dominance | 0.2849 | 0.2519 |
| Average raw title HHI | 0.2649 | 0.2213 |
| Average adjusted title HHI | 0.1555 | 0.1241 |
| Average qualified watch hours | 41.32 | 43.66 |

Adjusted HHI = (HHI − 1/n) / (1 − 1/n), and adjusted top-title dominance applies the same rescaling to top-title share. Both are exploratory audit diagnostics, not approved measures. Window differences are descriptive: the eligible populations differ, so they are not within-viewer change.

At identical breadth, concentration still varies widely. [`profile_viewership_hhi_by_breadth_final_90.csv`](profile_viewership_hhi_by_breadth_final_90.csv) holds median and 90th-percentile top-title share and adjusted HHI, and the median raw HHI with its `1/n` floor, for every exact-breadth group in `FINAL_90` from n = 3 to n = 47. Every group in that range has at least 30 profiles; percentiles are nearest-rank. It is the source table for [Figure 04](../../figures/figure_04_hhi_breadth_constraint.png) and [Figure 05](../../figures/figure_05_adjusted_hhi_by_breadth.png). For example, at exactly 20 meaningful titles (129 profiles) median top-title share is 0.1933 against a 90th percentile of 0.3519, and median adjusted HHI is 0.0544 against 0.1160.

**3D.2 — title versus genre concentration, eligible profiles with valid title HHI:**

| | BASELINE_90 | FINAL_90 |
| --- | ---: | ---: |
| Paired profiles / with ≥ 2 meaningful genres | 7,897 / 7,468 | 8,698 / 8,318 |
| Average meaningful genres | 4.89 | 5.26 |
| Average top-title / top-genre share | 0.3727 / 0.6905 | 0.3304 / 0.6366 |
| Average title / genre HHI | 0.2649 / 0.5784 | 0.2213 / 0.5189 |
| Raw HHI correlation | 0.6308 | 0.5291 |
| Top-share correlation | 0.5466 | 0.4214 |
| Average adjusted title / genre HHI (≥ 2 genres) | 0.1511 / 0.4057 | 0.1194 / 0.3497 |
| Adjusted HHI correlation (≥ 2 genres) | 0.3876 | 0.2895 |

Genre concentration is related to title concentration but not redundant once the breadth-dependent floor is removed. It is supporting context, not the primary concentration signal and not evidence of narrow taste on its own.

**Caveat:** the 30 baseline and 34 final-window profiles with `genre_hhi` populated but no meaningful genre have no valid qualified genre distribution, so genre concentration is undefined for them. They are all profiles with playback but no qualified start, none is analytically eligible, and they are excluded from genre-concentration interpretation.

**Meaning of the pass:** breadth reconciles across grains and preserves parent-title breadth separately from asset depth; title concentration is correctly built from qualified viewing across meaningful titles; breadth and concentration are related but distinct signals; and genre concentration adds supporting context, subject to one bounded caveat.

### Test 4 — post-choice response and the bridge from concentration to mechanism

Test 4 asked whether the post-choice fields are semantically strong enough to help explain concentrated catalogue consumption. It was not a search for a generic engagement score: the purpose was to decide which outcomes carry distinct behavioural information, which need censoring-aware or opportunity-aware denominators, and which can safely support later fingerprints.

Code: [`post_choice_outcome_semantics.sql`](../../sql/diagnostics/post_choice_outcome_semantics.sql) (4B–4C), [`return_behavior_semantics.py`](../../scripts/diagnostics/return_behavior_semantics.py) and [`rewatch_observability.py`](../../scripts/diagnostics/rewatch_observability.py) (4C), and [`concentration_mechanism_controls.sql`](../../sql/diagnostics/concentration_mechanism_controls.sql) (4D). The Python scripts rebuild asset-level behaviour from raw playback for analytically eligible profile-windows, anchoring each asset at its first qualified start.

| Area | Resolution | Evidence |
| --- | --- | --- |
| 4A — post-choice field reconciliation | Profile-level completion, abandonment, continuation and return components reconcile to title-level evidence; what remains is semantics and denominators, not aggregation loss | — |
| 4B — abandonment censoring | An unfinished start without the full 14-day follow-up is unknown. Behavioural abandonment uses qualified starts − censored abandonment starts; `FINAL_90` holds 11,776 censored starts across 6,174 profiles | [`post_choice_measurement_summary.csv`](post_choice_measurement_summary.csv) |
| Evidence sufficiency | Each profile rate needs at least five units of evidence on its own basis — qualified starts for the stored completion summary, known outcomes for abandonment and for downstream completion, observed opportunities for continuation — and at least three known outcomes for 14-day replay | [`post_choice_measurement_summary.csv`](post_choice_measurement_summary.csv), [`rewatch_profile_coverage.csv`](rewatch_profile_coverage.csv) |
| Completion / abandonment redundancy | On the same known denominator they are exact complements (correlation −1.0000, complement gap 0, no residual outcome): completion is primary, abandonment its diagnostic mirror | [`completion_abandonment_axis.csv`](completion_abandonment_axis.csv) |
| Continuation scope | Episodic-specific, known outcomes only; no opportunity is not a negative | [`post_choice_measurement_summary.csv`](post_choice_measurement_summary.csv) |
| Resume / rewatch separation | `resumed_assets` mixes pre-completion return with post-completion replay; pre-completion returns restart near the previous endpoint (median −43 s and −52 s) and behave as genuine resume; resume is a pathway, not a terminal outcome | [`return_decomposition.csv`](return_decomposition.csv), [`resume_playback_continuity.csv`](resume_playback_continuity.csv), [`return_semantic_closure.csv`](return_semantic_closure.csv) |
| 14-day replay | Median available follow-up after completion was 137 days in the baseline window and 44 in the final window, so replay uses a fixed 14-day horizon with known-outcome denominators | [`rewatch_latency_observability.csv`](rewatch_latency_observability.csv), [`rewatch_horizon_summary.csv`](rewatch_horizon_summary.csv) |
| Breadth × concentration mechanism connection | Similar concentration sits above different completion and replay responses | [`../viewer_diagnosis/concentration_mechanism_controls.csv`](../viewer_diagnosis/concentration_mechanism_controls.csv) |
| Separate activity-control robustness | Each profile is benchmarked separately against similar qualified watch hours and similar active days; a direction counts only when both agree. A crossed 25-stratum benchmark was rejected because it produced thin reference groups | [`../viewer_diagnosis/concentration_mechanism_controls.csv`](../viewer_diagnosis/concentration_mechanism_controls.csv) |

[`post_choice_measurement_summary.csv`](post_choice_measurement_summary.csv) keeps its historical completion summary alongside the corrected abandonment measure, so its columns sit on different bases:

- **Completion coverage and rates** (`completion_profiles_ge5`, `mean_completion_rate_ge5`, `pooled_completion_rate`) use the stored mart formulation: completed starts ÷ all qualified starts. The profile average covers profiles with at least five qualified starts; the pooled rate covers all eligible profiles.
- **Abandonment** (`known_abandonment_profiles_ge5`, `mean_known_abandonment_rate_ge5`, `pooled_known_abandonment_rate`) uses known outcomes after the censoring correction, for profiles with at least five known outcomes.
- **Continuation** averages profiles with at least five observed opportunities and pools across all eligible profiles.

Downstream, completion is measured on the same known-outcome denominator as abandonment — the common denominator on which [`completion_abandonment_axis.csv`](completion_abandonment_axis.csv) shows the two are exact complements. In `BASELINE_90` almost nothing is censored and the stored and known bases coincide. In `FINAL_90` they differ (average completion 0.7519 on the stored basis against 0.7935 on known outcomes), so the summary's completion and abandonment columns there should not be read as complements.

**Resulting post-choice vocabulary:** general retention → completion; episodic persistence → continuation under legitimate next-episode opportunity; unfinished-content persistence → validated pre-completion resume as supporting pathway evidence; completed-content repeat value → 14-day replay. Broad `resumed_assets` is excluded from downstream fingerprint use.

**What Test 4 licenses:** concentration alone is insufficient to identify a behavioural mechanism; completion is the primary post-choice retention axis; continuation is episodic-specific; resume is an intermediate pathway; 14-day replay is a distinct completed-content repeat measure; activity context is required before reading raw breadth × concentration differences; and several breadth × concentration states keep different post-choice signatures under both activity controls.

**What it does not license:** final viewer segments, permanent identities, causal explanations, recommendation-system claims, the assumption that replay occurred on the dominant title, or genuine unrealised viewing headroom. This is measurement and diagnostic evidence. The next block conditions behaviour on entitlement, catalogue reachability, tenure and other opportunity constraints.

### Test 5 — opportunity measures before conditioning

Before the opportunity fields could be used as conditioning variables, they had to hold as measures. Entitlement never exceeded observable profile tenure, catalogue opportunity never appeared without entitlement, and mean daily opportunity reconciled to eligible title-days divided by entitled days — the contracts already covered by `P01`–`P09` and [`opportunity_integrity.sql`](../../sql/mart_audit/opportunity_integrity.sql).

Test 5 then added a window-level measure, `reachable_parent_titles_in_window`: the distinct parent titles reachable at least once during the profile's entitled portion of a window. It was rebuilt with the same canonical day-by-day logic and reconciled back to the entitled-day and title-day fields before any behavioural comparison used it. The point was grain, not another green check: a window-level behavioural count needs a window-level choice set, which a daily average cannot provide. The [methodology](../../docs/measurement_methodology.md#window-level-reachable-catalogue-the-same-grain-breadth-denominator) defines the three quantities and why they are not interchangeable.

[`opportunity_regime_summary.csv`](opportunity_regime_summary.csv) publishes the resulting opportunity structure before any behavioural comparison uses it: one row per window × entitlement timing × opportunity regime, with profile counts, the reachable-catalogue distribution (average, minimum and maximum), average reachable titles per entitled day, meaningful titles, the diagnostic `meaningful_titles_per_100_reachable`, concentration and the activity averages. It is the table behind the statement that access, not behaviour, decides the size of the field: broad regimes average roughly 913 (baseline) and 976 (final) reachable parent titles against roughly 307 and 329 for regional regimes.

Three details matter when reading it. `hhi_valid_profiles` is the subset of each row's profiles whose title HHI is defined, so `avg_valid_title_hhi` has a smaller denominator than the other averages. Rows are reported however few profiles they contain — thin regimes are visible rather than merged away, and a row with a handful of profiles is a description, not a result. And `avg_meaningful_titles_per_100_reachable` is a profile-level average of a diagnostic ratio: it is not a utilisation target, because a reachable title was never owed a viewing.

The conditioning results built on this structure are reported in [journal entry 15](../../docs/analysis_journal.md#15-a-large-catalogue-is-not-the-same-thing-as-a-large-choice-set), with their own tables in [`../viewer_diagnosis`](../viewer_diagnosis/README.md#opportunity-conditioning-test-5).

### Test 6A — multilingual supply before any behaviour

Language could not be added as another breadth measure until the supply behind it was audited, because three different fields describe it: the language a title originates in, the languages offered as audio on it, and the language actually played. This block contains no viewer behaviour at all — it asks what multilingual choice existed before asking what anyone did with it.

It closed as **pass with caveat**. The structure holds, but `content_audio_languages` carries no independent entry or exit date per audio track, so listed tracks inherit the parent title's availability dates. That supports title-level multilingual opportunity and prevents any claim about the day a particular dub appeared if its real timing differed from the title's.

[`catalogue_multilinguality_by_program_type.csv`](catalogue_multilinguality_by_program_type.csv) — one row per programme type plus an `ALL_TITLES` row, at parent-title grain across the whole catalogue. The 1,000 parent titles carry 1,904 title × audio-language rows: 445 are monolingual, 555 multilingual, and the mean is 1.904 audio languages. The `titles_with_N_audio_languages` columns let a reviewer rebuild that distribution and check the concentration of supply — the 244 titles with three or more tracks hold 65.6% of all additional-language tracks. Multilinguality then differs sharply by programme: 78.17% of movies against 9.83% of catch-up. `DOCUMENTARY_SPECIAL` covers nine titles and is reported as it stands rather than merged away; its percentage is arithmetically correct and analytically tiny.

[`title_origin_vs_available_audio.csv`](title_origin_vs_available_audio.csv) — one row per language. `titles_of_this_origin` counts parent titles originating in that language; `titles_offering_this_audio` counts parent titles carrying it as an audio track. The two are not interchangeable, which is the point: Kannada originates 44 titles but is offered as audio on 216, so counting origins as audio opportunity would understate dubbing, and counting offered tracks as consumption would overstate behaviour.

[`language_opportunity_by_access_regime.csv`](language_opportunity_by_access_regime.csv) — one row per window × access regime, built on the same historically valid day-by-day availability used for catalogue opportunity. It gives reachable parent titles, their multilingual count and share, mean accessible audio languages per reachable title, and the day-weighted versions of those. Read the percentages beside the absolute counts: a regional pack's catalogue is more multilingual in percentage terms precisely because a dub is one route by which a title becomes eligible for the pack, but 186 reachable titles under a Bengali pack is a much smaller choice set than 913 under broad access.

**What these do not prove:** nothing about viewers. They establish supply and reachability, not multilingual viewing, preference, propensity, a segment or headroom. Reachable means technically available under historically valid entitlement — not surfaced, recommended, noticed or considered.
