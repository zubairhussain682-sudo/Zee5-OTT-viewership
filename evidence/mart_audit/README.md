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
| Next | Breadth and concentration | Not yet reviewed |

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
