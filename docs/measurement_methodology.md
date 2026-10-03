# Measurement methodology

The marts are only useful if each measure means one thing and uses a denominator that fits it. This document defines the rules the current marts rely on, why each exists, and where it is implemented.

## Qualified start: when does playback count as engagement?

**Question:** a viewer pressed play. Did they engage?

**Why it matters:** autoplay can start an episode nobody chose, and a manual start stopped after a few seconds is insufficient evidence of meaningful engagement. Counting both as engagement inflates breadth and distorts every rate built on starts.

**Rule:** a start qualifies when watch time reaches

| Playback | Threshold |
| --- | --- |
| Manual | `min(5 minutes, 10% of runtime)` |
| Autoplay | `min(8 minutes, 20% of runtime)` |

Autoplay carries the stricter bar because it requires no choice at all.

**What this changed:** qualification is a property of an event, not a new event type. Start-based outcome measures use qualified starts as their analytical starting population.

**Implemented in:** [`qualification.py`](../src/analytical_transforms/qualification.py).

## Meaningful title: what counts toward breadth?

A parent title counts toward a viewer's breadth only when it has **at least one qualified start**. A title that was merely available — or appears only because a continuation opportunity opened on it — is not meaningful, however many days it was reachable.

**Checked by:** [`meaningful_title_validation.sql`](../sql/mart_audit/meaningful_title_validation.sql).

## Concentration: top-title share and HHI

**Definition:** a viewer's qualified watch minutes are divided across their meaningful titles into shares s₁, …, sₙ that sum to 1. Top-title share is the largest share. The Herfindahl-Hirschman Index is:

```text
HHI = Σ sᵢ²
```

**Why both:** top-title share only sees the largest title, so two viewers with the same top share can spread the rest of their viewing very differently. HHI uses the whole distribution, and squaring gives progressively more weight to large allocations. Title HHI is valid only for profiles with at least three meaningful titles; genre HHI is built the same way across meaningful genres.

**What kind of measure it is:** a descriptive concentration index. It summarises how concentrated an allocation is. It is not an inferential test, does not estimate causality, and does not say whether concentration is healthy, constrained or recoverable — HHI measures concentration, not mechanism or headroom.

**The breadth-dependent floor:** equal shares across `n` titles give the lowest possible HHI, `1/n`. Raw HHI therefore falls with breadth partly for arithmetic reasons, and is not a breadth-independent viewer trait.

![Line chart of median raw title HHI against the equal-share floor 1/n by exact meaningful-title count in the final 90-day window, showing that much of the decline in raw HHI with breadth follows the floor](../figures/figure_04_hhi_breadth_constraint.png)

**Exploratory adjustment:** the breadth audit rescaled HHI to remove that floor:

```text
adjusted HHI = (HHI − 1/n) / (1 − 1/n)
```

0 means equal shares across the viewer's meaningful titles; values approach 1 as allocation concentrates. This adjustment is a diagnostic used in the audit. It is not yet an approved measure in the behavioural measurement layer.

**Caveat:** `genre_hhi` is populated for a small number of profiles with no meaningful genre, where genre concentration is undefined; those rows are excluded from genre-concentration interpretation.

**Checked by:** [`profile_viewership_title_concentration.sql`](../sql/mart_audit/profile_viewership_title_concentration.sql) and [`profile_viewership_genre_concentration.sql`](../sql/mart_audit/profile_viewership_genre_concentration.sql).

## Completion

An asset is complete when furthest progress reaches **90%** of runtime. Only qualified starts can become completions or non-completions, so an accidental autoplay start cannot count as an incomplete viewing.

The mart stores `completion_rate` over all qualified starts. For behavioural comparison, completion uses the same known-outcome denominator as abandonment (below). On that denominator every known start either completes or is abandoned, so the two are exact complements and form **one outcome axis**: completion is the primary general-retention measure, and abandonment is its diagnostic inverse rather than a second fingerprint dimension.

## Abandonment: an observable no-resume horizon is required

**Question:** a viewer stopped halfway. Did they abandon it?

**Why it matters:** if they stopped two days before the data ends, nobody knows yet. Counting that as abandonment would make the most recent viewing look worst simply because less time had passed.

**Rule:** an unfinished qualified start is abandoned only after 14 days with no resume. Where fewer than 14 days of follow-up exist, the outcome is **unknown** and is never counted as abandonment.

**Behavioural denominator:** the stored `abandonment_rate` divides abandoned starts by all qualified starts, so unknown outcomes sit in its denominator and late-window viewing looks less abandoned than it is. Behavioural abandonment uses known outcomes only:

```text
abandonment_known_denominator = qualified_asset_starts − censored_abandonment_starts
```

The stored rate stays documented but is not the downstream behavioural measure. No mart rebuild is needed: the mart carries every component.

## Continuation

**Question:** after finishing an episode, did the viewer go on to the next?

**Rule:** see the full definition in [mart architecture](mart_architecture.md#continuation-did-the-viewer-go-on-to-the-next-episode). In short, an opportunity exists only when the next episode was released, available, and within the profile's plan and audio entitlement. Each opportunity has exactly one outcome — known positive, known negative or unknown — and a viewer's rate pools known positives over known outcomes only.

**Why the precision matters:** a next episode that had not yet been released is not a missed opportunity, and a follow-up period cut short by a lapse in access is not a refusal.

**Scope:** continuation is an episodic-specific persistence measure. A profile with no legitimate next-episode opportunity has no continuation value, not a low one, and only known outcomes enter the rate.

![100% stacked bar chart showing continued, observed non-continuation and censored or unknown outcomes as shares of episodic continuation opportunities in the baseline and final 90-day windows](../figures/figure_03_continuation_outcomes_by_window.png)

**What the marts show:** unknown outcomes are 0.8% of continuation opportunities in the baseline window and 3.3% in the final window, which runs up to the end of the observable period. Keeping them as a separate state is a measurement control, not a cosmetic detail. Counted as non-continuation, they would push the measured rate down wherever follow-up is shortest — for reasons of observation, not behaviour.

**Implemented in:** [`continuation.py`](../src/analytical_transforms/continuation.py) · **Checked by:** [`continuation_state_integrity.sql`](../sql/mart_audit/continuation_state_integrity.sql) and [`continuation_checks.py`](../src/validation/continuation_checks.py), which tests each opportunity against the source tables and confirms both marts reproduce them.

## Resume: a pathway, not an outcome

The mart field `resumed_assets` counts qualified assets seen in more than one session. That mixes two behaviours: returning to an asset **before** completion, and returning **after** completion, which is replay.

**Rule:** resume means a pre-completion cross-session return. These returns were validated against playback position — later sessions typically restart just before the previous endpoint, with modest backtracking and almost never from the beginning — so they represent genuine unfinished-content persistence.

**Downstream treatment:** a resumed asset may still go on to complete, be abandoned or remain censored, so resume is an intermediate viewing pathway, not a terminal outcome, and it is never paired with abandonment as an alternative result. Validated resume is supporting evidence of unfinished-content persistence. The broad `resumed_assets` field is not a canonical fingerprint measure.

## Replay: completed-content repeat value over a fixed horizon

A rewatch is a qualified start at least 12 hours after the asset's first completion. Raw rewatch cannot be compared across windows, because earlier completions have more of the observation period left to produce one.

**Rule:** replay is measured over a fixed 14-day horizon after first completion. A rewatch inside the horizon is a known positive at once; a non-rewatch is known only when all 14 days were observable; otherwise the outcome is censored.

```text
14-day replay rate = completed assets rewatched within 14 days ÷ known 14-day outcomes
```

**Evidence threshold:** at profile grain the rate is used for behavioural comparison only when there are at least three known outcomes, and the known denominator is carried beside the rate so that three outcomes are never read as precisely as thirty.

## Post-choice response: four constructs, not one engagement score

| Construct | Measure | Condition |
| --- | --- | --- |
| General retention | Completion | Known outcomes only |
| Episodic persistence | Continuation | A legitimate, observable next-episode opportunity |
| Unfinished-content persistence | Validated pre-completion resume | Supporting pathway evidence |
| Completed-content repeat value | 14-day replay | At least three known outcomes, denominator retained |

These answer different questions and are not collapsed into a single score. A profile-average rate weights every viewer equally; a pooled rate weights outcomes. Neither is automatically more reliable, and later analysis keeps the evidence denominator alongside the rate. None of these measures establishes viewing opportunity or headroom: they describe what happened after content was chosen.

**Reproduced by:** [`post_choice_outcome_semantics.sql`](../sql/diagnostics/post_choice_outcome_semantics.sql) (censoring and the completion–abandonment axis), [`return_behavior_semantics.py`](../scripts/diagnostics/return_behavior_semantics.py) (resume versus replay) and [`rewatch_observability.py`](../scripts/diagnostics/rewatch_observability.py) (the replay horizon and profile coverage). The scripts need full-resolution exports of the playback tables and write compact evidence files.

## Opportunity

**Question:** what could this profile have watched?

**Rule:**

```text
Profile opportunity        = profile exists  AND  account holds valid access           (per day)
Profile-title opportunity  = profile opportunity  AND  title released, available, eligible   (per day)
```

Opportunity is evaluated from the access and catalogue state that actually existed at the time. It is not reconstructed from the plan an account happened to hold at the end of the window.

| Rule | Effect |
| --- | --- |
| Days before profile creation | Do not belong to that profile's opportunity |
| Subscription gaps | Contribute no entitlement |
| Before release or catalogue entry, after catalogue exit | Title contributes no opportunity |
| A later upgrade | Cannot enlarge an earlier choice set |

**Regional entitlement is title-level.** For a regional plan, a parent title is reachable when the plan's language group appears among that title's available audio languages:

```text
regional_title_eligibility = plan_language_group ∈ available audio languages for the parent title
```

The test is therefore based on offered audio availability, not solely on `original_language`, and it determines only whether the title enters the reachable catalogue — never which audio language was later consumed during playback. **Offered language describes opportunity; consumed language describes behaviour.** `ALL_ACCESS` and `ALL_ACCESS_SPORTS` are treated as the same broad VOD opportunity family because their VOD catalogue reach is the same here; that does not imply the two products are commercially identical outside this calculation.

**Why it matters:** this is the denominator that separates *chose not to watch* from *could not watch*.

![100% stacked bar chart showing profile-title rows by days of title availability — under 30, 30 to 59, 60 to 89, and the full 90 — in the baseline and final 90-day windows](../figures/figure_02_title_opportunity_by_band.png)

**What the marts show:** within the same 90-day window, roughly a quarter of profile-title rows had fewer than the full 90 days of opportunity, and around 6% had fewer than 30. These rows cover titles a profile watched or had a continuation opportunity on, not the whole catalogue. Opportunity is a measurement control, not a cosmetic detail: without it, a title's shorter reach would be read as a viewer's lower interest.

**Implemented in:** [`access.py`](../src/analytical_transforms/access.py) and [`opportunity.py`](../src/analytical_transforms/opportunity.py) · **Checked by:** [`opportunity_integrity.sql`](../sql/mart_audit/opportunity_integrity.sql) and, independently, [`opportunity_checks.py`](../src/validation/opportunity_checks.py), which rebuilds the same quantities day by day from the source tables without reusing the implementation's own logic.

## Profile-level opportunity quantities

Three related but **non-interchangeable** measures describe opportunity at profile grain.

| Measure | What it describes |
| --- | --- |
| `entitled_days_in_window` | Days within the declared window on which the profile existed and its account held valid VOD entitlement — an opportunity-duration measure |
| `eligible_parent_title_days` | Σ reachable parent titles on each entitled day: duration combined with daily catalogue reach, not a count of distinct titles |
| `mean_daily_eligible_parent_titles` | `eligible_parent_title_days ÷ entitled_days_in_window` (where entitled days > 0) — the average size of the reachable catalogue on an entitled day |

For zero-entitlement profile-windows the mean opportunity stays zero rather than producing an undefined behavioural quantity.

**Reconciled before use:** these fields were checked before being used as conditioning variables — entitlement never exceeded observable profile tenure, catalogue opportunity never appeared without entitlement, and mean daily opportunity reconciled to title-days divided by entitled days.

## Window-level reachable catalogue: the same-grain breadth denominator

The daily measures are not sufficient for every question. `distinct_meaningful_titles` is a count over the whole 90-day window, so dividing it by `mean_daily_eligible_parent_titles` — a daily average — mixes grains. The window-level measure is therefore:

```text
reachable_parent_titles_in_window
  = count of distinct parent titles with at least one valid
    profile-title opportunity day during that profile-window
```

Operationally, where the profile × parent-title exposure matrix stores the number of valid reachable days, this is `count(exposure_days > 0)` — the matrix [`profile_opportunity`](../src/analytical_transforms/opportunity.py) already returns, so the same canonical historical logic produces both.

| Measure | What it describes |
| --- | --- |
| `mean_daily_eligible_parent_titles` | Typical reachable catalogue size on an entitled day |
| `eligible_parent_title_days` | Total title × day opportunity accumulated through the window |
| `reachable_parent_titles_in_window` | Distinct parent titles reachable at least once during the window |

The distinctions are deliberate. A catalogue changes during a 90-day window, so the number of titles reachable at least once can exceed the average number reachable on any one day. The window-level measure was reconciled back to the existing entitlement and title-day fields before behavioural interpretation, specifically so that a window-level behavioural count is compared with a window-level reachable choice set rather than dividing quantities that merely happen to have convenient units.

## Breadth relative to reach is diagnostic, not a utilisation target

For exploratory comparison:

```text
meaningful_titles_per_100_reachable
  = 100 × distinct_meaningful_titles ÷ reachable_parent_titles_in_window
    (defined only where the reachable denominator is positive)
```

Without a positive denominator the ratio is undefined rather than zero, and the public helper returns `NaN`. A zero ratio says a profile watched nothing meaningful out of a real reachable pool; no pool at all is a different statement, and collapsing the two would understate breadth relative to reach. This is not the same case as `mean_daily_eligible_parent_titles`, which is legitimately zero when a profile had no entitled days.

This ratio is diagnostic only. It must not be read as the percentage of catalogue a viewer was expected to consume, a platform utilisation target, recommendation exposure, evidence that all reachable titles were noticed or considered, or direct viewing headroom. A reachable title is technically available under the historically valid access state; the dataset does not establish that it was surfaced to the viewer.

**Downstream treatment:** absolute breadth stays beside any opportunity-relative diagnostic rather than meaningful-title breadth being replaced by one normalised score.

## Opportunity regimes: use the structure in access, not arbitrary quintiles

Quantile bands were examined first and rejected for final conditioning. Eligible entitlement was heavily concentrated at 90 days, producing large ties, and reachable catalogue size formed repeated discrete pools rather than a smooth continuum. Those pools mapped directly back to historical plan structure, so the classification follows the access mechanics that generated the choice set.

**Entitlement timing**

| Timing | Definition |
| --- | --- |
| `FULL_90` | Valid entitlement across all 90 days of the analytical window |
| `PARTIAL` | Fewer than 90 entitled days while still satisfying analytical eligibility |

Timing is kept separate from catalogue regime: a partial-window broad-access profile is not treated as though it belonged to a narrower access family merely because it accumulated fewer entitled days. Catalogue composition also changes through time, so a partial profile may observe a slightly different daily catalogue mix while remaining under the same access regime. Duration and access family cannot safely be collapsed into one opportunity score.

**Opportunity regime**, reconstructed from the subscription intervals that overlap the period in which the profile actually exists:

```text
effective_start = max(subscription_start, window_start, profile_created_date)
effective_end   = min(subscription_end, window_end)
```

| Regime | Assigned when |
| --- | --- |
| `STABLE_BROAD` | Effective VOD opportunity remains within the broad-access family |
| `STABLE_REGIONAL_<language>` | Effective access remains within one regional language pack |
| `MIXED_ACCESS` | More than one materially different VOD opportunity regime applies during the profile-window |

The major reachable-catalogue modes were checked against these reconstructed historical access states rather than labelled from catalogue size alone; the correspondence between the repeated opportunity pools and the underlying plan regimes is what justified the classification.

The resulting structure is published, one row per window × entitlement timing × regime, in [`opportunity_regime_summary.csv`](../evidence/mart_audit/opportunity_regime_summary.csv). `access_context_days` and `opportunity_regimes` in [`opportunity.py`](../src/analytical_transforms/opportunity.py) implement the effective-overlap day weighting and the classification above.

## Access and consumption opportunity remain separate controls

A large reachable catalogue does not guarantee enough actual viewing activity to encounter much of it.

| Control | Definition |
| --- | --- |
| Access opportunity | Reachable catalogue under historical entitlement |
| Consumption opportunity | The amount of observed activity through which choices could occur |

Qualified watch hours and active days remain the two primary consumption-opportunity controls, and they are used **separately**. A profile can accumulate substantial hours through relatively few long viewing occasions while another accumulates similar hours over many active days; combining them into a single activity score would remove a distinction the analysis has already shown to matter. [Activity context](analytical_framework.md#activity-context) is a fairness comparison, not a new behavioural score.

## Opportunity-conditioned mechanism comparisons

When behavioural states are tested against realistic opportunity, the comparison follows this order:

```text
same analytical window
  + comparable opportunity family
  + comparable consumption opportunity
        ↓
compare behavioural state / post-choice response
```

Qualified watch hours and active days are used in separate versions of the comparison rather than crossed into one joint benchmark unless support is demonstrably sufficient. This prevents three sources of variation from being mistaken for one another: different catalogues being reachable, different amounts of viewing being generated, and genuinely different allocation or post-choice behaviour.

**Downstream treatment:** opportunity conditioning does not redefine the behavioural state itself. Breadth and concentration states remain `state(profile, window)` derived from observed behaviour; access regime is attached as context.

The comparisons themselves, with the population restriction and the support columns they have to be read against, are published under [opportunity conditioning](../evidence/viewer_diagnosis/README.md#opportunity-conditioning-test-5). One practical consequence of the rule above is recorded there: the candidate-mechanism table keeps the original Test 4 full-population activity quintiles, while the opportunity contrasts bucket activity within the stable population, so the two sets of quintile boundaries are not interchangeable.

## Genre structure is supporting context, not an opportunity denominator

Genre structure can help explain whether title breadth occurred across many genres or across many titles inside a narrower genre space. It is not treated as a complete opportunity denominator: the current data establish title-level reachability historically, but provide no equivalent canonical profile × genre opportunity measure strong enough to turn genre breadth into an exposure-normalised behavioural score.

**Downstream treatment:** genre measures are retained as supporting structure beside title breadth and concentration rather than substituted for the title-level opportunity framework.

## What opportunity conditioning licenses

The opportunity measures may be used to ask whether an observed mechanism survives under comparable realistic choice. They do not license this inference:

```text
reachable but unwatched titles = viewing headroom      ✗ not licensed
```

Reachability establishes possibility, not inclination or conversion. A title can be reachable without having been surfaced, considered or compatible with the viewer's observed behaviour, and genuine headroom requires later evidence beyond unused access.

## Analytical eligibility

A profile is eligible for the main comparison when it has **at least 30 entitled days, 3 active days and 120 qualified watch minutes** in the window. All three components stay visible beside the flag. No row is removed and no minimum breadth is imposed.

Eligibility answers *is there enough evidence and access to compare this profile fairly?* It is not a business outcome and not a segment.

**Implemented in:** [`eligibility.py`](../src/analytical_transforms/eligibility.py).

## Account-level aggregation

Account-level marts sum additive volumes across an account's profiles, rebuild distinct titles, genres and languages as unions from events, and reconstruct pooled rates from their underlying numerators and denominators. They never add up per-profile distinct counts or average per-profile rates.

The full account aggregation builder remains outside the current public code checkpoint.

## Code contracts

| Module | Logic | Inputs |
| --- | --- | --- |
| `access.py` | Account-day access; profile existence; plan and audio membership | `cycles` with inclusive `date` start/end; `profiles` with unique IDs, account IDs and creation dates |
| `opportunity.py` | Released, available parent titles; historical plan eligibility; account and profile exposure; window-level reachable catalogue, entitlement timing and access regimes | Catalogue release/entry/exit as pandas timestamps (`NaT` for no exit); audio with `parent_title_id` and `language`; inclusive window bounds |
| `qualification.py` | Qualified start and the 90% progression threshold | Events with `watch_seconds`, `is_autoplay`; runtime in seconds |
| `continuation.py` | Episode ordering, continuation opportunity, outcome state and attribution | Prepared episode events plus `profiles`, `accounts`, `catalogue`, `cycles` and `audio` frames |
| `eligibility.py` | The eligibility rule | A frame that already carries entitled days, active days and qualified minutes |

Opportunity and continuation functions take a calendar object exposing `n_days` and `day_index(date)`; continuation additionally needs `start`, `end` and `analytical_start`. The fixture tests show a minimal example. `profile_opportunity` returns `(profile_ids, parent_ids, exposure_matrix)` indexed by profile, alongside a profile-level opportunity frame. `reachable_parent_titles` reduces that exposure matrix to the window-level count defined above, `entitlement_timing` labels full against partial entitlement, `meaningful_titles_per_100_reachable` forms the diagnostic ratio and returns `NaN` where nothing was reachable, and `access_context_days` and `opportunity_regimes` classify the access history. All five are pure functions over frames and arrays, and the fixtures cover their boundaries: a title reachable for one day counts once, a profile with no access has no context row, a move between `ALL_ACCESS` and `ALL_ACCESS_SPORTS` stays `STABLE_BROAD` because VOD reach is unchanged, and a move between regional languages or between regional and broad access is `MIXED_ACCESS`.

The published code exposes these transformations and their checks. It does not include a single command that rebuilds every mart from full-resolution tables.

## Running the checks

```bash
python -m pip install -r requirements.txt
python -B -m unittest discover -s src/validation -p "test_*.py" -v
```

The fixtures need no database and no full tables. They exercise the rules at their boundaries: profiles created mid-window, access gaps, regional entitlement, historical upgrades, catalogue release and exit, episode ordering across seasons, interrupted and resumed access, and the exact seven-day continuation horizon.

The SQL in [`sql/`](../sql) is SELECT-only apart from the reference schema file [`raw_schema.sql`](../sql/schema_understanding/raw_schema.sql), which is DDL for an empty schema and should not be run against existing tables. Select the intended database before running any of it.
