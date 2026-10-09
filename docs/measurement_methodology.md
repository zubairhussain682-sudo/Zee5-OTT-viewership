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

## Language fields: origin, offered audio and consumed audio

Three fields describe language and none substitutes for another.

| Quantity | Source | Meaning |
| --- | --- | --- |
| `original_language` | Parent-title catalogue metadata | The language ecosystem the title originates in |
| Available audio language | `content_audio_languages` | Audio tracks offered on the parent title |
| Consumed audio language | `view_events.audio_language` | The track actually played during an observed event |

A viewer consuming Tamil audio on a Hindi-origin title has consumed Tamil audio *and* viewed inside a Hindi-origin ecosystem. Both statements are true and they answer different questions.

`home_region` and regional-plan language are contextual metadata, not native-language fields. Terms such as "native-language share" or "non-native viewing" are not used anywhere in this project, because native language is unobserved.

### Parent-title audio bridge

`content_audio_languages` is read at the grain of one parent title × one available audio language. Audio rows are not weighted by the number of playable episode assets under the same parent title: catalogue-language structure stays at parent-title grain. A parent title may expose up to six audio languages in the observed catalogue.

Language opportunity is layered onto the historically valid title state defined under [opportunity](#opportunity): a track listed on a title that was unavailable on a given day contributes no opportunity that day.

### Regional entitlement is title-level, not a track restriction

```text
regional_title_eligible(t)
  = plan_language_group ∈ parent title's available audio-language set
```

If this holds, the parent title enters the reachable catalogue — and once it is entitled, every audio language listed on that title remains selectable. The pack language determines *title admission*; it is not an exclusive playback-language restriction. `ALL_ACCESS` and `ALL_ACCESS_SPORTS` share the same VOD title and audio opportunity, as elsewhere in the project.

**Caveat — audio-track timing.** `content_audio_languages` carries no independent entry or exit date per track, so listed tracks inherit the parent title's historically valid availability dates. This supports title-level multilingual opportunity analysis but does not establish the day a particular dub appeared if its real timing differed from the title's. It is carried as a bounded measurement caveat rather than repaired with invented dates.

## Language opportunity: breadth and allocation are different questions

```text
reachable_audio_language_count
  = distinct audio languages present among historically reachable parent titles
```

This is retained as a descriptive breadth measure only. It is not used as the sole language-opportunity control, because it saturates: most eligible profiles reach nearly the full observed language set. A profile reaching ten languages can still face a highly concentrated opportunity distribution, so language opportunity also needs shares across languages and the concentration of those shares.

| Opportunity question | Carried by |
| --- | --- |
| Which languages were reachable | Reachable-language count |
| How much title-day opportunity each language represented | Opportunity-language shares |
| How concentrated that opportunity was | Opportunity-language HHI |

As with reachable catalogue in Test 5, distinct-window reach and title-day opportunity answer different questions: reach asks what entered the choice set at least once, title-days ask how much historically valid opportunity accumulated through time. Title-day opportunity is the preferred denominator wherever timing and access duration differ.

### Consumed-language and opportunity-language metrics

Consumed-language measures use qualified viewing only, with `view_events.audio_language`. For profile *p*, window *w*, language *l*:

```text
consumed_language_share(p, w, l)
  = qualified minutes consumed in l ÷ all qualified minutes for (p, w)

consumed_language_hhi = Σ_l consumed_language_share_l²
```

No offered track counts as consumed unless a qualified event actually used it. Opportunity shares are built from historically valid language opportunity — profile existence → historical entitlement → parent-title availability → title audio bridge — and support `top_opportunity_language_share` and `opportunity_language_hhi`. They are opportunity descriptors, not expected consumption shares.

Comparing consumed-language HHI with opportunity-language HHI asks whether playback is more concentrated than the reachable audio environment. It does not imply that a profile was expected to consume languages in proportion to supply. Qualified watch hours and active days remain separate activity controls here, exactly as in Tests 4 and 5: more activity means more chances to accumulate languages, so raw language breadth is never read without activity context.

## Title origin and cross-origin movement

### Paired population

Cross-origin analysis uses profiles eligible in **both** `BASELINE_90` and `FINAL_90`: 8,199 profiles. The two windows are equal-length observational windows, not treatment and control periods — Baseline is the behavioural reference and Final the diagnostic window, and no causal before/after reading is licensed.

### Baseline title-origin anchor

```text
baseline_origin_minutes(o)
  = qualified Baseline minutes on parent titles whose original_language = o

baseline_anchor_origin = argmax_o baseline_origin_minutes(o)
baseline_anchor_share  = baseline_origin_minutes(anchor) ÷ all qualified Baseline minutes
```

Ties are broken by minutes descending then language ascending. The anchor stays fixed while Final behaviour and opportunity are evaluated; recomputing it from Final viewing would move the reference with the outcome. It is a behavioural reference only — not native language, home region, plan language or a permanent preference label.

**Anchor-strength bands are sensitivity slices, not identities.** No natural breakpoint appears in the anchor-share distribution, so thresholds such as ≥70%, 70–95% and 95–100% exist only to make subsequent movement easier to read where the starting centre is clear. They are not segment boundaries, high/low propensity thresholds or identity labels, and activity remains relevant because broader activity can itself create greater origin breadth.

### Cross-origin viewing and new-origin entry

```text
a = fixed Baseline anchor
cross_origin_event      = original_language(parent_title) ≠ a
cross_origin_minute_share = qualified minutes on cross-origin titles ÷ all qualified minutes
```

The audio track does not alter a title's origin classification: a dubbed title remains cross-origin when its `original_language` differs from the fixed anchor. An origin is **new** in Final when qualified Final viewing of it is positive while qualified Baseline viewing of it was zero. The derived descriptors — entered-new-origin, new-origin minute share, anchor-only — describe catalogue-origin movement and imply no permanent exploration tendency.

### Historical cross-origin opportunity

```text
EligibleSet(p, t) = AvailableCatalogue(t) ∩ PlanEntitlement(account(p), t) ∩ profile existence

cross_origin_title_day = reachable parent title-day whose original_language ≠ baseline_anchor_origin

cross_origin_title_day_opportunity_share
  = cross-origin reachable title-days ÷ all reachable title-days
```

This is the same day-by-day reconstruction used for catalogue opportunity in Test 5, partitioned by title origin relative to the fixed anchor. A later access change never rewrites earlier opportunity, and final-plan status is never projected backward.

Cross-origin opportunity is enabling context, not expected behaviour. A profile with no cross-origin opportunity cannot legitimately show cross-origin viewing; a profile with substantial cross-origin opportunity is not expected to consume a fixed share of it. Cross-origin viewing share divided by cross-origin opportunity share is therefore **not a conversion rate**, and no openness or utilisation score is constructed from the pair. Where strong-anchor slices are used, the comparison that carries the argument is the change in behaviour against the change in historically valid opportunity — which supports the claim that opportunity alone does not determine behaviour, and establishes no causality, intrinsic preference or stable propensity.

## Programme composition and peer matching

Programme composition is reconstructed from meaningful Final title viewing, and dominant programme type is descriptive context rather than behavioural identity. The five programme types — `MOVIE`, `WEB_SERIES`, `TV_CATCHUP`, `REALITY`, `DOCUMENTARY_SPECIAL` — are retained wherever support permits; sparse categories are not merged to make a result look cleaner. A broader library-like (`MOVIE` + `WEB_SERIES` + `DOCUMENTARY_SPECIAL`) against recurring (`TV_CATCHUP` + `REALITY`) split is supporting context only and does not replace the five types in the primary sensitivity analysis.

```text
multilingual_title_minute_share
  = qualified Final minutes on parent titles offering > 1 audio language
    ÷ all qualified Final minutes
```

This is a consumption-composition measure and must not be called multilingual supply. A profile can spend 100% of its minutes on multilingual titles while selecting one audio language and one title-origin ecosystem.

### Peer matching

Final cross-origin behaviour is compared inside peer cells defined by the same Baseline anchor origin, the same 5-percentage-point anchor-share band, the same 5-percentage-point Final cross-origin opportunity-share band, and the same Final activity quintile. Activity is matched in two separate versions, `ACTIVE_DAYS` and `WATCH_HOURS`; the controls are never crossed or averaged.

```text
peer_expected_cross_origin_share
  = mean Final cross-origin minute share in p's peer cell

cross_origin_deviation_pp
  = 100 × (profile Final cross-origin minute share − peer expected share)
```

Whether the focal profile is excluded from its own cell mean is **not established here** (the corrected Test 6D implementation, by contrast, uses the inclusive cell mean and records it in its published evidence). The 6C.4B implementation was never persisted to the analysis workbench, and the published aggregate cannot settle it: every one of the 8,199 profiles carries a deviation and the smallest reported peer-cell size is 1, which is consistent both with an inclusive cell mean and with a leave-one-out mean over cells of at least two profiles. The wording therefore states the cell mean without claiming a leave-one-out rule it cannot support. Either convention shifts an individual deviation by a factor of n/(n−1), which is negligible at the supported cell sizes and leaves the published directions unchanged.

The primary supported comparison uses `peer_n ≥ 20`. Smaller cells may be shown for support diagnostics but do not carry the interpretation — this is a support rule, not a behavioural threshold.

Programme-level deviations are descriptive averages of profile deviations after matching; they are not programme treatment effects. Differences between the full population and the `peer_n ≥ 20` subset also carry population-selection effects and must not be attributed to opportunity matching alone. Thin groups stay thin: `REALITY` is support-sensitive and `DOCUMENTARY_SPECIAL` is too small to carry a programme conclusion. Multilingual-title-minute quintiles are descriptive sensitivity bands, and where a boundary cuts through a mass of identical values — profiles at 100% multilingual-title minutes, for instance — that boundary is a ranking artefact, not a behavioural threshold.

## Test 6D: cross-origin behaviour inside candidate mechanisms

Test 6C established cross-origin movement relative to a fixed Baseline anchor and historically valid opportunity. Test 6D asks a different measurement question: does that behaviour contribute information beyond the breadth × concentration mechanisms already identified, or reproduce distinctions those mechanisms already capture?

| Quantity | Definition |
| --- | --- |
| **Outcome** — Final cross-origin minute share | Qualified Final viewing minutes on parent titles whose `original_language` differs from the fixed Baseline anchor origin, over all qualified Final minutes. A Hindi-anchored profile watching a Telugu-origin production through Hindi audio still contributes cross-origin viewing: audio selection never changes a title's original-language classification. |
| **Context** — Final cross-origin reachable title-day share | Reconstructed historically from profile existence, effective entitlement and parent-title availability, as defined under [cross-origin measurement](#title-origin-and-cross-origin-movement). It is the proportion of reachable parent-title-days outside the anchor ecosystem — not content presented, noticed, considered or expected to be watched. |

Viewing and opportunity remain separate quantities throughout. Neither is divided by the other to create a conversion or utilisation score.

### 6D.1 — population and candidate-state reconstruction

Test 6D uses the same 8,199 profiles eligible in both windows as Test 6C. Candidate mechanisms are assigned from the original Test 4 Final-window states *before* restricting to the paired population: concentration and breadth quintiles are `NTILE(5)` by top-title qualified share and distinct meaningful titles, with `profile_id` as tie-breaker, ranked over the **full 9,762 Final-eligible profiles**. The resulting state is joined to the paired population without reranking.

| Candidate family | Original Test 4 state |
| --- | --- |
| `FOCUSED_SUCCESSFUL` | C5_B1 and C4_B1 |
| `SELECTIVE_CORE` | C4_B3 |
| `ACCESS_SENSITIVE_NEIGHBOUR` | C5_B2 |
| `SUCCESSFUL_FIRST_PASS` | C3_B2 |
| `BROAD_DISTRIBUTED` | C1_B5 |
| `RESIDUAL` | All remaining breadth × concentration states |

The family names are interpretive labels for previously defined configurations. Membership is never recalculated using cross-origin viewing, opportunity, residuals or any Test 6D result — which is what preserves the non-redundancy test: a proposed dimension must be examined against the mechanisms as they already existed rather than allowed to redefine them in its own favour. The Final candidate state is the latest observed behavioural state in this dataset; Baseline-to-Final continuity is a separate longitudinal question, and Test 6D assigns no persistent or emerging identity.

### 6D.2 — opportunity distribution before behavioural comparison

For each candidate family, describe the Final cross-origin title-day opportunity distribution — count, mean, median, quartiles — together with Baseline anchor-origin composition and anchor strength. The purpose is to find out whether apparent behavioural differences might arise from differently structured reachable catalogues: a Hindi anchor and a Bengali anchor need not leave the same proportion of accessible catalogue outside the anchor, even under broad entitlement, so broad-access membership alone does not establish equal cross-origin opportunity.

Distributions are retained rather than reduced to means. Repeated opportunity-share values arise from common combinations of catalogue structure and historical access; they are **structural mass points, not discovered behavioural thresholds**. This step contains no behavioural ranking and establishes no propensity difference — it determines how cautiously the later comparisons may be read.

### 6D.3 — raw behaviour, opportunity bands and common-weight standardisation

**6D.3A.** For every candidate, describe the Final cross-origin minute share: mean, median, 25th and 75th percentiles, and the proportion of profiles with zero cross-origin Final viewing (anchor-only). The anchor-only proportion is retained because two families can have nearly identical means while containing very different numbers of profiles who never viewed outside their anchor. These are actual, unstandardised population descriptions and must stay available beside any conditional estimate.

**6D.3B.** Place profiles into five-percentage-point bands of Final cross-origin title-day opportunity share, and compare candidate behaviour within them. A profile in the 55–60% band had roughly 55–60% of its historically reachable parent-title-days outside its Baseline anchor language — the band classifies the *available choice environment*, not the viewing outcome.

The supported common-band comparison used four shared bands covering about 86.5% of the paired population:

| Final cross-origin opportunity band | Paired profiles | Common weight |
| --- | ---: | ---: |
| 10 – <15% | 883 | 0.125 |
| 55 – <60% | 3,743 | 0.528 |
| 85 – <90% | 1,049 | 0.148 |
| 90 – <95% | 1,417 | 0.200 |
| Common-band population | 7,092 | 1.000 |

Candidate families occupy those bands in different proportions, so comparing unadjusted means mixes behavioural differences with differences in the distribution of opportunity. The standardised comparison applies one common set of band weights, taken from the pooled paired population across the shared bands, to every family:

```text
band_mean(g, b)          = mean Final cross-origin minute share for candidate g in band b
common_band_weight(b)    = paired profiles in shared band b ÷ all paired profiles in the shared bands
standardised_mean(g)     = Σ_b [ common_band_weight(b) × band_mean(g, b) ]
```

The weights sum to one and are identical for every family. This is a descriptive standardisation of observed group means: it alters no profile's viewing or opportunity, creates no matched pairs and estimates no causal effect of access. A raw candidate mean describes the actual average in that candidate's observed population; a standardised mean answers the narrower question of behaviour under a common distribution of the selected bands. Neither replaces the other, and results from the common-band population do not automatically generalise beyond it.

**Banding is not matching.** Sharing a band does not establish equivalence on anchor origin, anchor strength, activity or programme composition, all of which remain possible explanations for within-band differences. That limitation motivates 6D.4 rather than being treated as though standardisation had completed the conditioning.

### 6D.4 — candidate-blind peer adjustment

Each profile's Final cross-origin viewing is compared against the mean observed among profiles with similar anchor structure, historical opportunity and activity. The peer-cell key is exact `baseline_anchor_origin` → 5-point band of `baseline_anchor_share` → 5-point band of Final opportunity share → Final activity quintile, with `ACTIVE_DAYS` and `WATCH_HOURS` as separate specifications. The two activity variables are never combined into a composite, crossed into a joint cell, or averaged into one benchmark.

**Population rule for activity quintiles.** Activity quintiles are `NTILE(5)` across the **full 8,199 paired profiles**, ordered by the Final activity measure with `profile_id` as deterministic tie-breaker; every paired profile receives a quintile and enters peer-cell construction before any support filtering. This differs from the candidate-state ranking population, and the two must not be interchanged:

| Construction | Ranking population |
| --- | --- |
| Test 4 breadth × concentration state used by 6D | Full Final-eligible, 9,762 |
| Test 6D activity quintile used for peer matching | Paired eligible, 8,199 |

An initial implementation reused full-population activity quintiles for peer matching and was rejected when it failed to reproduce the established Test 6C.4B programme results. After the quintiles were rebuilt over the 8,199 paired profiles, those historical deviations reproduced, and only the corrected results are carried forward.

```text
peer_expected_share(p, control) = mean Final cross-origin minute share in p's peer cell
cross_origin_residual_pp(p, control)
    = 100 × ( observed Final cross-origin minute share(p) − peer_expected_share(p, control) )
```

The corrected Test 6D implementation uses the **inclusive** peer-cell mean, recorded in the published evidence as `peer_expectation_convention`. Reproducing Test 6C.4B's published group results does not establish whether that earlier, unpersisted implementation included or excluded the focal profile, and this repository does not claim otherwise — see the [note on that convention](#programme-composition-and-peer-matching).

Candidate family is deliberately not part of the peer key: a candidate-specific benchmark would condition the comparison on the very classification whose additional value is under evaluation. The primary support rule is `peer_n ≥ 20`, counted before the restriction is applied; cells below it remain relevant to coverage diagnostics but carry no supported interpretation. This threshold concerns the reliability of the comparison population, not an intrinsic behavioural distinction.

A positive residual means more cross-origin Final viewing than the observable peer context, a negative residual less. It is not a conversion rate and not a causal programme, entitlement or mechanism effect. Candidate-level summaries report supported residuals separately for each control, always with support counts and coverage, because comparisons between a full candidate population and its supported subset are affected by support selection as well as conditioning.

**Programme sensitivity.** A stricter variant adds dominant Final programme type to the peer key while preserving the other conditions, interpreted only where the expanded cells satisfy `peer_n ≥ 20`. It does not replace the core residual, because an extra matching dimension materially reduces support, and its results cannot be presented as covering every profile in the original family.

### 6D.5 — within-candidate dispersion and robustness

Candidate-level means do not reveal whether cross-origin behaviour varies *inside* a mechanism. For the primary cross-control comparison, retain profiles whose peer cells hold at least 20 profiles under **both** specifications:

```text
common_supported(p) = peer_n_ACTIVE_DAYS(p) ≥ 20 AND peer_n_WATCH_HOURS(p) ≥ 20
```

That population is 5,510 of the 8,199 paired profiles (67.2%), and every distributional or cross-control claim refers to it rather than to the full paired population. For each candidate and specification, report count, mean and median residual, 25th and 75th percentiles and the interquartile range. The IQR is retained alongside the mean because substantial positive and negative residuals offset one another: a candidate with a near-zero mean residual can still contain profiles behaving very differently from their peers.

Cross-control robustness is assessed with the Spearman rank correlation, the share retaining the same residual sign, the share reversing sign, and the mean absolute difference in percentage points. **These are not replication.** Both specifications use the same Final cross-origin outcome and share most matching variables, so high correlation is evidence of robustness to the activity benchmark, not independent observation of behaviour and not a persistent viewer trait.

**Diagnostic quartile agreement.** Within each candidate's common-supported population, rank the residuals under each control into positional quartiles with `NTILE(4)` and `profile_id` as tie-breaker:

```text
stable_low  = bottom residual quartile under ACTIVE_DAYS AND under WATCH_HOURS
stable_high = top residual quartile under ACTIVE_DAYS AND under WATCH_HOURS
```

These labels mean only that the same profiles occupy the same tail under both Final-window activity controls. They are **not** behavioural thresholds, final segments, propensity categories or evidence of persistence across time. Where many profiles share identical residuals at a quartile boundary, `NTILE(4)` splits ties by `profile_id`: reproducible, but not a behavioural boundary.

For the two overlapping tail groups, inspect actual Final cross-origin minute share, Final cross-origin opportunity share, Baseline anchor share and the corresponding residuals. This translates residual dispersion back into observable viewing and checks whether the extremes merely reflect different starting anchors or opportunity. Similar group-level means do not establish individual matching; these are descriptive context layered onto the peer-conditioned result.

Because `FOCUSED_SUCCESSFUL` combines C5_B1 and C4_B1, the residual-spread and cross-control checks are repeated within the constituent states, testing whether heterogeneity exists inside them or merely arises from pooling. The constituent checks do not redefine the parent family or create new labels. A programme-adjusted tail sensitivity recomputes the benchmark with dominant Final programme type in the key, subject to the same minimum support, and reports both directional agreement and surviving support for each tail — a high agreement percentage with low programme-matched coverage establishes directional consistency within the comparable subset only.

### 6D.6 — decision and measurement boundaries

**Pass for provisional carry-forward as a non-redundant, cross-cutting behavioural dimension.** The supporting measurement evidence is the substantial within-candidate variation in Final cross-origin viewing after structural, opportunity and activity conditioning, together with robustness to alternative activity controls and programme-context sensitivity where support permits.

The decision introduces no new calculation, threshold, composite score or category, and it does not show how much incremental viewing a profile would generate if presented with more content. Cross-origin viewing can displace existing viewing rather than increase total qualified minutes; historically reachable titles are not necessarily titles shown, noticed or considered; and movement beyond an earlier original-language centre reveals neither native language nor psychological willingness to explore.

| ✓ May now say | ✗ May not yet say |
| --- | --- |
| A provisional, opportunity-conditioned descriptor of cross-origin allocation | Native-language or mother-tongue preference |
| Evidence beyond the breadth × concentration mechanisms | Psychological language openness or an intrinsic trait |
| Input to later behavioural fingerprints and mechanism-led interpretation | A calibrated cross-origin conversion or catalogue-utilisation rate |
| One component of a more discriminating unrealised-opportunity assessment | Causal effects of access, supply, programme composition or recommendations |
| | A permanent viewer identity, or a final segment derived from Test 6D residuals |
| | Longitudinal persistence inferred from two control specifications of the same Final outcome |
| | Incremental viewing headroom inferred from cross-origin movement or unused reachable titles alone |

The dimension is therefore available to inform later fingerprints and mechanism-led interpretation, but its role in any final segment must be earned through longitudinal evidence and relevance to the diagnosis rather than assumed from within-window robustness. Test 6D closes the non-redundancy question; it closes neither persistence nor realisable headroom.

## What the language and origin measures license

These rules support the term **cross-origin catalogue propensity under realistic opportunity** as an observed behavioural tendency after conditioning, and nothing more. They do not turn it into a native-language preference, language-openness psychology, a causal effect, a permanent identity, a segment or a headroom score.

Test 6D has since established that this tendency carries information the breadth × concentration mechanisms do not already capture, which is why it is carried forward provisionally. The progression the measurement layer licenses is therefore language supply → consumed-language behaviour → cross-origin viewing against a fixed anchor → non-redundant inside mechanisms. Raw language breadth remains descriptive throughout. Persistence across time and contribution to realisable headroom remain untested.

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
| `origin.py` | Baseline title-origin anchor, cross-origin classification and anchor-relative opportunity split | Qualified minutes by profile × `original_language`; an exposure matrix from `profile_opportunity` with each parent title's origin |

Opportunity and continuation functions take a calendar object exposing `n_days` and `day_index(date)`; continuation additionally needs `start`, `end` and `analytical_start`. The fixture tests show a minimal example. `profile_opportunity` returns `(profile_ids, parent_ids, exposure_matrix)` indexed by profile, alongside a profile-level opportunity frame. `reachable_parent_titles` reduces that exposure matrix to the window-level count defined above, `entitlement_timing` labels full against partial entitlement, `meaningful_titles_per_100_reachable` forms the diagnostic ratio and returns `NaN` where nothing was reachable, and `access_context_days` and `opportunity_regimes` classify the access history. All five are pure functions over frames and arrays, and the fixtures cover their boundaries: a title reachable for one day counts once, a profile with no access has no context row, a move between `ALL_ACCESS` and `ALL_ACCESS_SPORTS` stays `STABLE_BROAD` because VOD reach is unchanged, and a move between regional languages or between regional and broad access is `MIXED_ACCESS`.

`origin.py` reuses that same exposure matrix rather than rebuilding access: `baseline_origin_anchor` fixes the reference, `cross_origin_opportunity` partitions reach and title-days around it, and `cross_origin_minute_share` and `new_origin_entry` classify behaviour by title origin. Its fixtures cover the boundaries that matter: a regional pack admits a cross-origin title through its dub, a later broad plan does not enlarge the earlier window, the anchor stays fixed when Final behaviour moves, consumed audio never reclassifies a title's origin, and a share with no denominator is `NaN` rather than zero.

The published code exposes these transformations and their checks. It does not include a single command that rebuilds every mart from full-resolution tables.

## Running the checks

```bash
python -m pip install -r requirements.txt
python -B -m unittest discover -s src/validation -p "test_*.py" -v
```

The fixtures need no database and no full tables. They exercise the rules at their boundaries: profiles created mid-window, access gaps, regional entitlement, historical upgrades, catalogue release and exit, episode ordering across seasons, interrupted and resumed access, and the exact seven-day continuation horizon.

The SQL in [`sql/`](../sql) is SELECT-only apart from the reference schema file [`raw_schema.sql`](../sql/schema_understanding/raw_schema.sql), which is DDL for an empty schema and should not be run against existing tables. Select the intended database before running any of it.
