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

---

## 12. Breadth and concentration describe different parts of catalogue use

**Date:** 2026-09-15

**Question:** when two viewers reach a similar number of meaningful titles, are they necessarily using the catalogue in a similar way?

**Why it matters:** breadth is an obvious place to start when the business concern is catalogue utilisation. If one viewer watches three parent titles and another watches twenty, it is tempting to describe the second as a much broader catalogue user. But breadth only tells us how far viewing reached. It says nothing about how attention was distributed across what was reached.

That distinction matters directly to the project question. Concentrated viewing is not automatically under-utilisation, and broad viewing is not automatically healthy distribution. A profile can reach twenty titles while still directing a large share of its viewing to one anchor programme. Another profile with the same twenty meaningful titles may distribute viewing much more evenly. If those profiles are collapsed into the same "breadth" description, the behaviour we are trying to diagnose disappears.

Before treating breadth and concentration as separate behavioural dimensions, however, both first had to survive semantic reconciliation. Otherwise we would be building sophisticated interpretations on top of aggregation artefacts, a cherished tradition in analytics that this project can live without.

**Evidence — meaningful breadth survives qualification:** the first question was whether the viewer-level breadth measures reproduce what exists in playback and the lower-grain marts ([audit evidence](../evidence/mart_audit/README.md#test-3--breadth-and-concentration)).

They did. Raw playback, `profile_title_window`, `profile_genre_window` and `profile_viewership_window` reconciled exactly for distinct assets, parent titles, genres, consumed audio languages, meaningful titles and meaningful genres. No mismatches were found.

That matters because title breadth in this project is deliberately parent-title breadth, not asset breadth. Ten episodes of one series are depth within one programme, not ten explored titles. The reconciliation confirms that this distinction survives aggregation into the viewer-level mart.

The next issue was qualification. A playback touch does not automatically mean meaningful catalogue use, and very short starts can inflate the apparent number of titles reached.

Qualification does change breadth, but much less than might have been expected:

| Active profiles | BASELINE_90 | FINAL_90 |
| --- | ---: | ---: |
| Profiles losing at least one title to qualification | 21.0% | 19.3% |
| Average raw titles → meaningful titles | 13.10 → 12.80 | 16.40 → 16.12 |
| Average meaningful-title retention | 97.5% | 98.2% |
| Profiles losing at least one genre | 6.1% | 4.8% |

Most affected profiles lose a single title: 1,710 of 2,351 in the baseline window and 1,685 of 2,324 in the final window.

**Interpretation:** shallow playback can exaggerate catalogue reach for some viewers, so qualification is necessary. But it is not driving the overall breadth structure. The broader title usage visible in the mart is not simply a mass of accidental or trivial touches.

The genre result needs more restraint. A genre contains many titles, and viewers do not face equal realistic title supply inside every genre. That genre counts rarely change after qualification tells us only that the number of genres touched usually survives the removal of shallow interactions. It does not establish stable genre openness or exploration.

**Analyst choice — why HHI:** if breadth tells us how many meaningful titles were reached, what measure best describes how viewing was distributed across them?

The simplest concentration measure already available is top-title share. It is useful and intuitive: if 40% of a viewer's qualified minutes belong to one parent title, that title clearly dominates the viewing pattern. But top-title share only sees the largest title.

Two viewers can have the same top-title share while distributing the rest of their viewing very differently. One might devote 30% to the top title and spread the remaining 70% almost evenly across nineteen others. Another might devote 30% to the top title, 25% to a second and 20% to a third, leaving little for everything else. Top-title share treats those patterns as identical.

For that reason, I chose to carry the Herfindahl-Hirschman Index, or HHI, alongside top-title share. For a viewer whose qualified watch minutes are split across meaningful titles in shares s₁, s₂, …, sₙ:

```text
HHI = Σ sᵢ²
```

Squaring the shares gives progressively more weight to large allocations. HHI therefore summarises concentration across the whole distribution of qualified viewing, rather than asking only how large the single biggest title is. In this project that is the point: the business problem is about how attention is allocated across catalogue choice. Top-title share identifies the strongest anchor; HHI tells us whether the rest of viewing is broadly dispersed or gathered into a small set of titles.

It is also important to be clear about what kind of statistical instrument HHI is. Here it is a descriptive concentration index, not an inferential statistic. It does not test a hypothesis, estimate causality or tell us whether concentration is desirable. It compresses the shape of a distribution into a comparable summary measure. The interpretation still belongs to the wider behavioural context.

HHI also has a structural limitation that matters considerably here. Its minimum depends on how many titles viewing is distributed across. A viewer who watches `n` titles in exactly equal shares has the lowest possible HHI:

```text
minimum HHI = 1 / n
```

A viewer with three meaningful titles therefore cannot reach the same low HHI as a viewer with thirty, even if both distribute attention perfectly evenly across their own titles. Part of the relationship between breadth and raw HHI is mathematical rather than behavioural ([Figure 04](../figures/figure_04_hhi_breadth_constraint.png)), which rules out simply reading "lower HHI" as "more distributed viewer" without also considering how many titles the viewer had.

To investigate that problem, I used an exploratory breadth-adjusted form:

```text
adjusted HHI = (HHI − 1/n) / (1 − 1/n)
```

An equal allocation across the viewer's observed `n` meaningful titles gives 0, and increasingly concentrated allocation approaches 1. The adjustment is useful for diagnosis because it removes the equal-share floor imposed by breadth. It is not yet an approved measure: this audit establishes that the adjustment is analytically useful, and the behavioural measurement layer still has to establish whether it is stable and appropriate enough to be adopted.

The same caution applies to HHI itself. HHI describes how concentrated viewing is; it does not explain why. High HHI could reflect strong satisfaction with a favourite programme, weak catalogue exploration, limited access, low realistic opportunity, or some combination of those.

**Evidence — breadth and concentration are not interchangeable:** among analytically eligible profiles with valid title HHI:

| Eligible profiles with valid title HHI | BASELINE_90 | FINAL_90 |
| --- | ---: | ---: |
| Profiles | 7,897 | 8,698 |
| Average meaningful titles | 17.31 | 21.67 |
| Average top-title share | 0.3727 | 0.3304 |
| Average adjusted top-title dominance | 0.2849 | 0.2519 |
| Average raw HHI | 0.2649 | 0.2213 |
| Average adjusted HHI | 0.1555 | 0.1241 |

Final-window eligible viewers were broader and descriptively less concentrated. The raw changes alone would not be enough, because greater breadth mechanically lowers the minimum possible concentration — but the breadth-adjusted measures moved in the same direction, so the lower concentration is not explained purely by greater breadth. This is descriptive only. The eligible populations are not identical across the two windows, so it is not evidence that individual viewers became more distributed over time.

The more consequential result came from comparing viewers at the same breadth. In `FINAL_90`, viewers with exactly 20 meaningful titles had a median top-title share of 19.3% but a 90th-percentile share of 35.2%, and a median adjusted HHI of 0.054 against a 90th percentile of 0.116. Every one of those viewers reached exactly twenty meaningful titles, so the difference cannot be dismissed as one group simply having broader catalogue reach.

| `FINAL_90`, exact meaningful titles | Profiles | Median top-title share | 90th-percentile top-title share | Median adjusted HHI | 90th-percentile adjusted HHI |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 15 | 154 | 24.6% | 37.7% | 0.075 | 0.143 |
| 20 | 129 | 19.3% | 35.2% | 0.054 | 0.116 |
| 30 | 78 | 14.7% | 23.4% | 0.038 | 0.078 |

The same structure remains at higher breadth: among viewers with exactly 30 meaningful titles, median adjusted HHI was 0.038 while the 90th percentile was 0.078.

![Line chart of median and 90th-percentile adjusted title HHI by exact meaningful-title count in the final 90-day window, showing a persistent upper concentration tail at every breadth](../figures/figure_05_adjusted_hhi_by_breadth.png)

**Interpretation:** breadth and concentration are genuinely distinct signals. A viewer can demonstrate substantial catalogue reach and still allocate a disproportionate share of viewing to a small part of that reached catalogue. A viewer with the same breadth can distribute attention considerably more evenly.

That gives the analysis its first credible candidate behavioural configuration: meaningful breadth accompanied by unusually concentrated attention relative to viewers with comparable breadth.

It is deliberately not being called a segment, and certainly not a headroom segment. Test 3 establishes that the configuration exists; it does not establish what causes it. Broad-but-concentrated viewing could represent perfectly healthy anchor-title loyalty. It becomes commercially interesting only if later evidence shows that concentration coexists with weak stickiness, failed exploration or substantial realistic opportunity that is not translating into sustained viewing.

**Genre concentration — context, not a new diagnosis:** is title concentration simply genre concentration measured another way? Raw title and genre HHI were moderately related, with correlations of 0.631 in the baseline window and 0.529 in the final window. Once both were adjusted for the breadth-dependent floor, the relationship weakened to 0.388 and 0.290.

Title and genre concentration overlap, but they are not redundant. Genre concentration can later help explain the shape of title concentration: a viewer may be concentrated on one title while otherwise moving across genres, or may concentrate attention inside a much narrower genre space. It cannot yet be read as narrow taste or unrealised opportunity, because realistic genre opportunity differs across viewers and plans and that denominator has not been normalised.

The audit also surfaced a small semantic imperfection: `genre_hhi` is populated for 30 baseline and 34 final-window profiles that have no meaningful genre at all. Concentration is undefined without a qualified genre allocation, so those rows are excluded from genre-concentration interpretation. The issue is bounded and does not touch the eligible concentration analysis, so it is recorded as a caveat rather than allowed to hijack the audit.

**What this changed:** Test 3 gives two separate candidate behavioural dimensions where previously there was one vague idea of "catalogue use":

- **meaningful breadth** — how far qualified viewing reached across parent titles;
- **concentration** — how qualified viewing was allocated across that reached set.

HHI earns its place alongside top-title share because it captures the full distribution rather than one dominant title, while its breadth-dependent floor means raw values must be interpreted with breadth in view. The broad-but-concentrated pattern is now established strongly enough to carry forward into the mechanism analysis, as a candidate configuration rather than a viewer segment. Concentration cannot safely be inferred from breadth, and breadth cannot safely substitute for concentration.

**Where this sits in the analytical pathway:** Test 3 is where the project begins to move from validating mart fields toward deciding which behavioural signals are credible enough to carry into the diagnosis. It does not define segments or identify viewing headroom. What it establishes is a distinction the rest of the analysis depends on: breadth describes how far meaningful viewing reaches across the catalogue; concentration describes how attention is allocated across that reach. Those two signals can now be treated separately rather than collapsed into a vague idea of "catalogue use." Test 4 will add post-start behaviour and stickiness, asking whether concentrated viewing reflects content that genuinely holds the viewer or weak engagement after selection. Test 5 will add realistic opportunity, asking whether the viewer actually had sufficient reachable alternatives for the observed pattern to be interpreted fairly. Only when those layers are combined can recurring behavioural fingerprints be interpreted as mechanisms, translated into defensible viewer segments, and then assessed for genuine viewing headroom. In that sense, Test 3 gives us a validated part of the concentration → mechanism → opportunity pathway, but deliberately stops before claiming what the concentration means.

**What it made us ask next:** the question is no longer simply whether a viewer is concentrated. It is: when viewing is concentrated, does that concentration reflect content that genuinely holds the viewer, or does it coexist with weak post-start engagement? Completion, abandonment, continuation, resumed viewing and related stickiness evidence form the next mechanism layer, and Test 4 has to establish whether those measures can be trusted before they are used to separate the broad-but-concentrated configuration into anything like healthy loyalty, weak engagement, constraint or potential unrealised viewing opportunity.
