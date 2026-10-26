# Segmentation evidence

**Question:** who was segmented, which routes make up each segment, and what does each route's evidence show about how its viewers' viewing changed?

**Why it matters:** the segments rest on route-level evidence and on placement decisions that each carry a stated reason. A reader should be able to check every segment's membership, every route's mechanism signature and every count the [journal](../../docs/analysis_journal.md#28-where-the-evidence-converged-and-the-population-it-converged-on) cites, without access to profile-level data.

**Populations.**

| Population | Profiles | Used for |
| --- | ---: | --- |
| Investigated population | 6,228 | Every segment: Track A 3,565, Track B 1,100, Track C 1,563 |
| Paired eligible | 8,199 | The ledger, and the parent routes the paired tracks were drawn from |
| Final eligible | 9,762 | Context only; the 3,534 Final-eligible viewers not advanced by Test 7.7 are not segmented |

The C×B states keep their original Test 4 rankings over each window's full eligible population. Nothing is re-ranked over the investigated viewers.

**Provenance.** Every table is curated from the accepted, verified Test 7.7 evidence package and the viewer-level evidence record built for the investigated population. Nothing is transcribed from narrative prose, and no profile-level row is published. The rules behind every column are in [methodology: segmentation of the investigated population](../../docs/measurement_methodology.md#segmentation-of-the-investigated-population).

**Conventions used in every table:**
- Change statistics are distributions of **individual** Final − Baseline differences. A median of change is never the difference of two window medians, and component medians are never added together.
- Top-title share levels are fractions (0–1); share changes are percentage points.
- Hours are qualified watch hours; titles are meaningful parent titles.
- Values are rounded to four decimal places.
- Group IDs (A01–A18, B01–B03, C01–C06) are the stable identifiers of the 27 historical routes, used to join the tables.

---

## Who was segmented

### `investigated_population_ledger.csv`

**Grain:** one row per Baseline family × Final family route (all 36, zero routes included), plus an `All paired` total row.

**Columns:**

| Column | Meaning |
| --- | --- |
| `paired_profiles` | Paired viewers on the route |
| `titles_up_hours_up` | Viewers whose meaningful titles and qualified hours both increased |
| `advanced_track_a` | Of those, viewers advanced by Test 7.7 (Track A) |
| `titles_up_hours_up_not_advanced` | The remainder, on pathways not selected for investigation |
| `titles_up_hours_not_up` | Viewers whose titles increased while hours did not |
| `advanced_track_b` | Of those, viewers advanced to the breadth-only review track (Track B) |
| `titles_up_hours_not_up_not_advanced` | The remainder |

**Reading it:** the total row reconciles the published Test 7 counts to the tracks: 3,784 viewers grew both titles and hours, 3,565 were advanced and 219 were not; 1,652 broadened without more hours, 1,100 were advanced and 552 were not. The 219 sit mostly on Focused Successful stayers (120). Test 7.7 selected by mechanism and pathway, not by growth sign alone, so a viewer outside an advanced pathway is unselected, not lost.

### `investigated_population_evidence_record.csv`

**Grain:** one row per recorded quantity of the viewer-level evidence record, in five sections:
- `POPULATION`: profiles per track; reconstructed equals expected.
- `QA`: 647 technical and reconciliation checks, all passed; no source table modified.
- `COVERAGE`: 10,893 eligible profile-windows and 32,679 profile × window × outcome rows.
- `OUTCOME_SUPPORT`: per window, track and outcome, the profiles that are supported, those below support with a positive denominator, those with a zero denominator, and those with a missing denominator. Support rules: completion ≥ 5 known outcomes, continuation ≥ 5 observed opportunities, replay ≥ 3 known outcomes.
- `HETEROGENEITY`: individual changes that run against their route's median direction on a historical finding (2,957 of the 3,565 Track A profiles have at least one).

**What it does not establish:** the QA counts are integrity checks, not confirmations of a behavioural reading. Running against the route's direction is descriptive heterogeneity, not a data failure or an individual diagnosis.

---

## What the segments are made of

### `segment_route_membership.csv`

**Grain:** one row per historical route (27).

**Columns:**
- `track`, `baseline_family`, `final_family`, `exact_state_disposition` and `selection_rule` define the route.
- `segment_id`, `segment` and `growth_pattern` give its placement.
- `placement_basis` is one of:
  - `ROUTE_MECHANISM`: placed with routes whose mechanism signatures agree;
  - `BEHAVIOUR_OVER_ORIGIN`: placed by behaviour where its origin family pointed elsewhere;
  - `FINAL_CONFIGURATION`: Track C, placed by Final family and scale, with no trajectory implied.
- `placement_note` records the reason for every non-default placement and every closer call.

### `segment_summary.csv`

**Grain:** one row per segment, plus a total. It gives the routes in each segment and its profiles by track; the total reconciles to 6,228.

Segment-level medians are **not** published. Route medians can't be combined into a segment median, and a segment claim is read route by route from the tables below.

---

## How each route's viewing changed

### `route_mechanism_signature.csv`

**Grain:** one row per paired route (21: Tracks A and B).

**Columns:**

| Group | Columns |
| --- | --- |
| Scale and level | `hours_baseline_median`, `hours_final_median`, `titles_*_median`, `top_share_*_median` |
| Individual change | `hours_change_p25/median/p75`, `titles_change_*`, `top_share_change_*` (pp), with `*_increased_n` and `*_decreased_n` |
| Kept-title hours | `kept_title_hours_change_p25/median/p75`: change in hours on titles meaningful in both windows |
| Hours by title fate | `dropped_title_hours_*` (Baseline hours on titles no longer meaningful), `new_title_hours_*` (Final hours on newly meaningful titles) |
| Title turnover | `titles_added_*`, `titles_dropped_*`, `titles_kept_*` |
| Time organisation | `active_days_change_median`, `qualifying_sessions_change_median`, `qualified_minutes_per_session_change_median` |

**Reading it:** attention spread (`top_share_change_median`), kept-title hours and hours by title fate are the mechanism signature; Baseline hours are scale. Opening-up routes show a clear negative top-share change, near-flat kept-title hours and most new hours on new titles. Deepening routes show flat or rising top share and positive kept-title hours. For Track B, the time-organisation columns carry the difference from their growing twins.

### `route_outcomes_and_context.csv`

**Grain:** one row per paired route (21).

**Columns:**
- Completion, continuation and 14-day replay for viewers supported in both windows: `*_dual_supported_n`, the pooled rates in each window, and the median individual change in pp.
- The median individual change in reachable parent titles, outside-anchor share and episodic share.

**Reading it:** completion is the primary post-choice corroboration and continuation is secondary. `replay14_role` is `CONTEXT_ONLY`: replay fell on 18 of these 21 routes, consistent with the shorter follow-up late in the Final window, so its direction isn't used as inclination evidence. Reachable titles rose by a median of 61–64 on every route, which is why access doesn't explain who grew.

### `route_vs_parent_hours.csv`

**Grain:** one row per paired route (21).

**Columns:**
- `parent_route`: the full paired transition the route was selected from.
- The parent's, the selected route's and the not-selected remainder's sizes, plus their Baseline, Final and individual-change hours medians.

**Reading it:** the tracks were selected by the direction of hours change, so selected routes cross their parent's median from opposite sides. That is the regression to the mean described in [journal entry 31](../../docs/analysis_journal.md#31-same-appetite-less-time). Two parent definitions differ for the Residual twins: the heavy spreaders (A16) were drawn from Residual stayers whose exact state moved (2,019), and the widening viewers (B02) from all Residual stayers (2,949). Broad Distributed → Residual shows a route median hiding its growers: the parent's median change is −4.37 hours, while the 144 selected viewers gained 23.33.

### `final_only_placement.csv`

**Grain:** one row per Track C route (6).

**Columns:**
- Median profile age at the start of the Final window.
- Final hours, titles and top-title share medians.
- Supported Final completion (`completion_supported_n` and its pooled rate).
- The segment each route is placed beside.

**Reading it:** five of the six routes have a median profile age of 0–8 days and match a growth segment's Final family and scale. The Focused Successful route (median age 283 days, 3.57 hours, two titles) matches none and forms its own segment. 916 of the 1,563 have a supported Final completion rate; the rest are unsupported, not low.

---

**What these tables do not establish:** that every member of a segment did what its routes' medians describe; that any viewer will grow; how much additional qualified viewing an intervention would produce; or causal effects of access, programme mix or content. Segment membership for Track C describes current configuration, not growth. The size of each segment's opportunity is measured by controlled testing, as set out in [journal entry 33](../../docs/analysis_journal.md#33-what-the-investigation-established-and-what-it-hands-on).
