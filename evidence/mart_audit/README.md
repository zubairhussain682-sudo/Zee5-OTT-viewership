# Mart audit evidence

**Question:** before any viewer-level measure is trusted, do the analytical marts actually hold what they claim to?

**Why it matters:** a fingerprint or segment built on a mart that silently duplicates rows, inherits access a profile never had, or treats unobserved follow-up as a negative outcome would look numerically plausible and still be wrong.

[`measurement_checks.json`](measurement_checks.json) records 70 automated contract checks across both viewership windows. Every check passes. The file holds check outcomes only — it contains no population measures, distributions or findings.

| Check family | What it establishes |
| --- | --- |
| `K01`–`K12` | Each mart is unique at its declared grain; no orphan profiles, accounts or parent titles; window boundaries are ordered and complete |
| `P01`–`P09` | Profile opportunity never exceeds the days a profile existed, title exposure equals an independent day-by-day reconstruction, eligibility follows its stated rule, and account eligible-profile counts add up from profiles |
| `C*` | Continuation opportunities are unique, follow episode order within a parent title, open only when the next episode is reachable, carry exactly one outcome state, and reconcile from title rows to profile rows |

**Interpretation:** passing these checks establishes that the mart grain, opportunity and continuation contracts hold. Automated checks do not by themselves prove that every mart field is suitable for downstream behavioural measurement — that judgment belongs to human semantic review. `profile_title_window` has completed that review; viewer-level measurement review remains ahead. Nor does a suitable field automatically become a fingerprint input: each candidate measure still needs its own review of distribution, stability and redundancy.

The validation logic is published and inspectable. Re-running the full contract suite requires the full-resolution source and mart tables, which are intentionally not stored in this repository.

- `P01`–`P09` come from [`opportunity_checks.py`](../../src/validation/opportunity_checks.py), which rebuilds historical access and title availability day by day from the source tables, sharing neither the access matrix nor the catalogue logic used to build the marts — so agreement is evidence, not a restatement.
- The `C*`, `CT_*` and `CV_*` continuation checks come from [`continuation_checks.py`](../../src/validation/continuation_checks.py), which tests each opportunity against the source tables and then confirms both marts reproduce those opportunities exactly.

Small deterministic fixtures in [`src/validation`](../../src/validation) exercise the same rules at their boundaries — profile creation mid-window, access gaps, regional entitlement, catalogue release and exit, and the seven-day continuation horizon — without needing the full tables.
