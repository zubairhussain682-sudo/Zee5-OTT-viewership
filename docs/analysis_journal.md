# Analysis journal

This journal records the reasoning behind consequential measurement decisions — the question that forced each one, what the evidence showed, and what it made us ask next. It is not a log of every query.

---

## 1. Ranking titles was the wrong question

**Question:** which titles are under-watched?

**Why it matters:** that is where catalogue-utilisation work usually starts, and it leads straight to a leaderboard.

**Evidence:** a low watch total is consistent with a title nobody could reach, a title reachable only by a small audience, a title people tried and dropped, and a title that simply suits few viewers. The number alone cannot separate them.

**Interpretation:** concentration is an outcome, not a diagnosis. Without knowing why it happens, any intervention is a guess.

**What this changed:** the question became *concentration → mechanism → opportunity* — explain the allocation of attention before asking whether more viewing is achievable. See [business problem](business_problem.md) and [analytical framework](analytical_framework.md).

**What it made us ask next:** what evidence could actually tell those explanations apart?

---

## 2. An account is not a viewer

**Question:** when an account shows broad viewing, is one person exploring widely?

**Why it matters:** a subscription can support several profiles with entirely different habits.

**Evidence:** accounts regularly hold more than one profile ([`account_profile_grain.sql`](../sql/schema_understanding/account_profile_grain.sql)). Summing each profile's distinct titles counts any title two of them watched twice.

**Interpretation:** an account's breadth describes combined viewing across its profiles, not one viewer's exploration.

**What this changed:** the profile became the behavioural unit and the account became context. Account-level breadth is rebuilt as a distinct union across events; pooled rates are rebuilt from numerators and denominators. A commercial plan change is never attributed to a single profile. See [account-level aggregation](measurement_methodology.md#account-level-aggregation).

**What it made us ask next:** if the profile is the unit, what exactly is it choosing between?

---

## 3. Ten episodes are not ten titles

**Question:** what counts as catalogue breadth?

**Why it matters:** the playable catalogue is made of assets, and an episodic series contributes many of them.

**Evidence:** parent-title identifiers repeat across assets, heavily for episodic programme types ([`asset_vs_parent_title.sql`](../sql/schema_understanding/asset_vs_parent_title.sql)). Counting assets would turn one binge-watched series into apparent exploration.

**Interpretation:** depth within a title and breadth across titles are two different behaviours. A viewer who watches ten episodes of one programme and a viewer who samples ten programmes should not score the same.

**What this changed:** attention is measured at parent-title grain, with asset and episode depth kept alongside it. See [mart architecture](mart_architecture.md).

**What it made us ask next:** when does touching a title count as engaging with it?

---

## 4. Offered is not watched

**Question:** is a viewer who could watch in several languages actually open to them?

**Why it matters:** titles offer multiple audio tracks, and it is tempting to treat that supply as evidence of language behaviour.

**Evidence:** original language, offered audio languages and the language recorded on each playback event are three separate facts. Joining every offered language to playback also multiplies watch time.

**Interpretation:** only consumed audio describes behaviour. Offered audio languages describe a title's language supply; whether that supply was realistically reachable also depends on access and catalogue availability.

**What this changed:** the three stay separate in every join and denominator. A title's language supply is relevant to eligibility: regional plans reach a title only through the languages it offers, and only while access and availability hold. See [access.py](../src/analytical_transforms/access.py).

**What it made us ask next:** language availability is recorded as an inventory, not a timeline — so how far can a language-openness measure be trusted over time?

---

## 5. A metric without a period has no denominator

**Question:** how much did a profile watch?

**Why it matters:** "how much" over an unspecified span cannot be compared with anything, and a later plan could quietly explain earlier viewing.

**Evidence:** accounts move between plans and through gaps, and profiles are created throughout the observation period.

**Interpretation:** every measure needs a declared window, and equal calendar length does not mean equal observable tenure.

**What this changed:** viewership is measured in named 90-day windows (`BASELINE_90`, `FINAL_90`), subscription context across the full 180 days, and every row carries its window dates. Event boundaries are half-open so windows never overlap. See [data model](data_model.md#time-windows).

**What it made us ask next:** inside a window, what could each profile actually reach?

---

## 6. Narrow viewing can be narrow access

**Question:** is a profile that watched few titles disengaged?

**Why it matters:** this is the exact confusion the business question warns against.

**Evidence:** a profile created late in a window, an account between subscriptions, and a regional plan reaching part of the catalogue all shrink the real choice set — to a materially narrower reachable catalogue.

**Interpretation:** under-utilisation only means something relative to what was reachable.

**What this changed:** opportunity is computed day by day as profile existence, historical access, and released, available, plan-eligible catalogue. Access an account held before a profile existed belongs to the account, not the profile. An independent check rebuilds the same quantities from source tables without reusing the implementation's logic. See [opportunity.py](../src/analytical_transforms/opportunity.py) and [opportunity_checks.py](../src/validation/opportunity_checks.py).

**What it made us ask next:** which profiles have enough evidence and access to be compared at all?

---

## 7. Eligibility is a guardrail, not a segment

**Question:** which profiles belong in the main comparison?

**Why it matters:** comparing a profile with three days of access against one with ninety produces differences that are about observation, not behaviour.

**Evidence:** profiles vary widely in entitled days, active days and qualified viewing within the same window.

**Interpretation:** a minimum evidence threshold makes comparison fair — but it must not quietly remove the concentrated viewers the question is about.

**What this changed:** eligibility requires 30 entitled days, 3 active days and 120 qualified watch minutes, with no minimum breadth. Ineligible profiles remain in the mart with every component visible. See [eligibility.py](../src/analytical_transforms/eligibility.py).

**What it made us ask next:** among eligible profiles, which outcome measures are trustworthy?

---

## 8. "Didn't continue" and "not yet known" are different

**Question:** after finishing an episode, did the viewer go on to the next?

**Why it matters:** continuation is one of the strongest signals of stickiness — and one of the easiest to measure unfairly.

**Evidence:** a next episode may not have been released yet, access may lapse inside the follow-up period, and viewing near the end of the data simply has less time to be observed.

**Interpretation:** only an opportunity that was genuinely open, and fully observed, can produce a negative outcome.

**What this changed:** each continuation opportunity opens only when the next episode is reachable and has exactly one outcome — known positive, known negative or unknown. Rates pool known outcomes only; unknown outcomes are never counted as failures. See [continuation.py](../src/analytical_transforms/continuation.py) and [`continuation_state_integrity.sql`](../sql/mart_audit/continuation_state_integrity.sql).

**What it made us ask next:** do the other outcome measures hold themselves to the same standard?

---

## 9. The title-level mart has been audited

**Question:** does `profile_title_window` measure what the architecture says it measures?

**Why it matters:** it is the foundation for breadth, concentration, depth and stickiness. Anything wrong here propagates into every later measure.

**Evidence:** the mart was reviewed by hand against its measurement semantics — qualified starts, meaningful titles, title opportunity and continuation outcomes — and its automated grain, opportunity and continuation contracts all pass ([evidence](../evidence/mart_audit/README.md)).

**Interpretation:** title-level evidence is fit to support downstream measurement at its intended grain. That is not the same as every derived field being fit to become a fingerprint input.

**What this changed:** attention moves from title-level evidence to the viewer-level measurement base.

**What it made us ask next:** does `profile_viewership_window` hold each outcome to a legitimate denominator? Abandonment is the first case to settle — the mart carries both an all-qualified-starts denominator and a known-outcomes denominator, and the behavioural measure should use whichever the review supports. After that: which candidate measures are stable, sufficiently evidenced and non-redundant enough to define fingerprints?

---

## 10. Making the measurement logic visible

**Date:** 2026-09-11

**Question:** can a reviewer see why the grain, opportunity and continuation rules exist, rather than take them on trust?

**Why it matters:** measurement rules read as technicalities until their scale is visible — and a rule whose purpose is not visible is easily dropped later.

**Evidence:** three figures drawn directly from the current marts ([`figures/`](../figures)): depth within a parent title by programme type, days of title opportunity within each 90-day window, and the composition of continuation outcomes.

**Interpretation:** each shows a simplification that would distort measurement — episodes counted as titles, unequal availability treated as equal, unknown outcomes treated as failure. They document measurement conditions; they are not behavioural findings.

**What this changed:** the figures sit beside the rules they support, in the [README](../README.md#selected-analytical-figures), [mart architecture](mart_architecture.md#profile_title_window) and [measurement methodology](measurement_methodology.md#opportunity).

**What it made us ask next:** nothing new — the `profile_viewership_window` audit remains the next step.

---

## 11. Watching nothing, touching something and watching longer are different facts

**Date:** 2026-09-13

**Question:** before `profile_viewership_window` is used to describe anyone's viewing, does each row mean what it claims — one profile, in one window — and can its activity and session measures be rebuilt from raw playback?

**Why it matters:** every later statement about depth, habit, concentration or headroom will stand on this table. If it quietly dropped profiles that watched nothing, blurred shallow sampling into engagement, or aggregated sessions differently from how they happened, those statements would inherit the error and still look precise.

**Evidence:** two audit blocks, both passed ([audit evidence](../evidence/mart_audit/README.md#human-semantic-audit-profile_viewership_window)).

The first tested grain, coverage and row meaning. The mart holds exactly one row per profile per window, and all 13,037 profiles appear in both windows — including those that played nothing.

| Profiles | BASELINE_90 | FINAL_90 |
| --- | ---: | ---: |
| No playback | 1,841 | 976 |
| Playback but no qualified start | 30 | 34 |
| At least one qualified start | 11,166 | 12,027 |
| Main-analysis eligible | 8,761 | 9,762 |

No row contradicts itself: qualified minutes never exceed total minutes, meaningful titles never exceed titles touched, the meaningful-title fields agree, and rows without playback carry no viewing, sessions or meaningful titles. Inactive, unqualified, ineligible and eligible profiles were also read by hand to check that each state looks like what it claims to be.

The second tested activity, volume and sessions. Every internal relationship held, and when the measures were rebuilt from raw sessions and events, event counts, autoplay counts, active days, first and last event timestamps and session counts matched exactly. Watch minutes and session durations matched to within numerical precision. Descriptively, for profiles with any playback, the two windows look like this:

| Per active profile | BASELINE_90 | FINAL_90 |
| --- | ---: | ---: |
| Active profiles | 11,196 | 12,061 |
| Watch minutes | 1,799.98 | 1,940.29 |
| Active days | 22.27 | 21.70 |
| Sessions | 25.93 | 25.00 |
| Mean session length, minutes | 50.35 | 57.49 |
| Median session length, minutes | 38.79 | 45.48 |
| Sessions per active day | 1.13 | 1.13 |

Qualified viewing accounts for 99.56% of watch minutes in the baseline window and 99.66% in the final window.

**Interpretation:** keeping profiles that watched nothing is deliberate, and it turned out to be one of the more important properties of the table. A profile that existed and had access during the window but played nothing is an observation, not missing data. In a streaming service, entitlement can sit next to a large reachable catalogue and still produce no viewing at all — availability is supply, not demand. Remove those rows and the viewer base is biased toward people who already engaged, and the contrast between what could have been watched and what was watched, which any later diagnosis of unrealised viewing depends on, disappears before it can be examined.

The 30 and 34 profiles with playback but no qualified start are few, but they make a distinction visible that matters well beyond their number: touching content is not the same as taking part in the catalogue. The qualified-watch share shows that qualification removes almost no viewing *time*, and it would be easy to conclude the rule is cosmetic. It is not. A shallow sample adds almost nothing to hours but can add a title to a viewer's apparent range, so qualification may matter far more to breadth than to volume. A platform that counted every brief play as consumption could report wide library reach that viewers never meaningfully engaged with — exactly the misreading a catalogue-utilisation question cannot afford. How much it changes breadth here is a question for the next audit, not something these totals show.

Eligibility settled into its proper role: a statement about evidence, not about people. An ineligible profile stays in the mart with every component visible; it simply has too little access or activity to be compared fairly. That distinction has commercial weight. A profile with one isolated viewing occasion should not become a loyalist, a sampler or an under-utiliser because a segmentation needs every row to belong somewhere. "We have evidence of a stable behaviour" and "we have too little evidence to say" are different findings, and the pathway keeps them in order: first whether there is enough evidence, then under what conditions the viewing happened, then fair measurement, and only then behavioural pattern and segment identity.

The activity shape is the first place a behavioural story could be told too early. The final window has more active profiles and more viewing per active profile, but slightly fewer active days and sessions, materially longer sessions, and the same number of sessions per active day. Descriptively, that could be consistent with deeper viewing occasions rather than more frequent ones. It does not yet distinguish between explanations. Programme mix, title concentration, device context and stickiness may all matter, but their relationship to this activity pattern has not yet been tested, and the remaining viewer-level behavioural blocks still require their own semantic review. What it does establish is that volume and frequency are separate dimensions. Two viewers can reach similar hours through frequent short returns or through a few long sittings, and those patterns can carry different implications for habit, the kind of content that suits them, retention, and how much room for more viewing realistically exists.

Two results are hygiene rather than insight, but they protect what comes next. `first_event_ts` and `last_event_ts` are the earliest and latest event *start* times, not the end of the last playback. Viewing span, recency and persistence will all be derived from these fields, and each needs to know which anchor it inherits, or it will quietly mix two definitions of "when". Similarly, session minutes measure elapsed session time while watch minutes sum playback across events; they are different constructs and are kept apart.

The reconciliation also produced a useful false alarm. Under a one-millionth-of-a-minute tolerance, thousands of profiles showed differences between stored and rebuilt minutes. None exceeded 0.001 minute; the largest watch-time gap was about 0.002 seconds, with no systematic direction, and session durations behaved the same way. Given the exact count and timestamp reconciliation around them, those differences are numerical residue rather than disagreement about what was watched. The lesson is not that databases round numbers. It is that a reconciliation threshold has to be chosen to separate a semantic difference from machine-level noise — otherwise a correct table gets investigated as a broken one, or, worse, a real discrepancy hides among thousands of meaningless ones.

**What this changed:** the viewer-level base is now trusted for grain, coverage, activity, volume and sessions. Reproducing raw playback is not a finding about viewers; its value is that later claims about depth, habit, concentration or opportunity will not rest on a grain error, an aggregation mistake, an ambiguous time anchor or a mismatched denominator. None of this answers the business question. Concentration, the mechanism behind it and any genuine viewing headroom all remain open.

**What it made us ask next:** if activity is measured faithfully, is breadth — and the concentration built on it? The longer sessions in the final window could be spread across many titles or given almost entirely to one, and this table's activity fields cannot say which. The next audit asks whether distinct and meaningful titles, genres, top-title qualified share, title HHI and genre concentration in the viewer base agree with `profile_title_window` and `profile_genre_window` — and how much qualification changes apparent breadth, given how little it changes hours.
