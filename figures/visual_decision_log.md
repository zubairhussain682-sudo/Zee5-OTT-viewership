# Visual decision log

## Test 5 — realistic opportunity conditioning — 2026-10

**Question:** once realistic opportunity is introduced, which Test 5 findings need visual explanation — the scale of the broad/regional difference in choice set, whether concentration moves consistently with that access difference, and whether the strongest Test 4 mechanisms survive being read inside opportunity families?

**Established:** broad and regional profiles differ far more in reachable catalogue than in meaningful breadth; concentration differences do not take one consistent sign across activity context; focused-successful and selective-core keep opposite completion signatures after opportunity conditioning; and selective-core replay stays clearly above peer context under broad access.

**Not established:** causal access effects, catalogue conversion or utilisation, recommendation exposure, statistical equivalence between broad and regional concentration, final segments, durable identities or headroom.

**Figures**

| # | File | Relationship | Form | Mode |
| --- | --- | --- | --- | --- |
| 12 | [`figure_12_reach_vs_breadth_index.png`](figure_12_reach_vs_breadth_index.png) | Relative magnitude | Indexed horizontal lollipop/dot comparison | Explanatory |
| 13 | [`figure_13_concentration_difference_by_opportunity_family.png`](figure_13_concentration_difference_by_opportunity_family.png) | Deviation from zero across ordered activity quintiles | Line/marker comparison | Explanatory |
| 14A | [`figure_14a_completion_after_opportunity_conditioning.png`](figure_14a_completion_after_opportunity_conditioning.png) | Deviation from activity benchmark | Zero-centred dot comparison | Explanatory |
| 14B | [`figure_14b_replay_after_opportunity_conditioning.png`](figure_14b_replay_after_opportunity_conditioning.png) | Deviation from activity benchmark | Zero-centred dot comparison | Explanatory |

**Reasoning:** Figure 12 puts reachable catalogue and meaningful breadth on one dimensionless broad/regional index because plotting their raw values together would mix incompatible units, while keeping them in separate charts left the reader to perform the central comparison mentally. Regional = 1.0 is an indexing device only, not a target and not a utilisation baseline. Figure 13 is zero-centred because the analytical question is the direction and size of the broad/regional difference once activity is held comparable. Figures 14A and 14B reuse the Test 4 deviation language and encoding so that opportunity conditioning reads as a continuation of the same mechanism test rather than a newly invented score, and they stay separate because completion and replay are distinct outcomes that move differently.

**Rejected:** splitting Figure 12 into 12A and 12B, because the central comparison was then spread across incompatible axes and had to be reassembled mentally. Presenting meaningful titles over reachable titles as a "conversion rate", because reachability is not recommendation exposure or consideration and the ratio is diagnostic only. Any catalogue-utilisation framing. Uncertainty bands on Figure 13, because the published evidence carries group means and support counts but no standard errors or confidence intervals. A new hollow-marker thin rule to flag regional selective-core in Figure 14B, because the project's existing `<30` state-cell rule does not classify those plotted rows as thin and redefining it for one figure would quietly change the standard. A headline figure for the genre incremental-model result, because it is supporting context and the gain is modest.

**Not carried:** Figure 12 does not imply that regional profiles use the catalogue more efficiently, and it is not a conversion or utilisation chart. Figure 13 does not prove a null effect or statistical equivalence; it shows that opportunity family imposes no single concentration direction. Figure 14A does not establish that broad access causes stronger completion, and the position of broad points relative to regional ones is not promoted into a separate finding. Figure 14B does not treat the large Baseline regional selective-core deviation as durable. Baseline against Final remains descriptive here, not within-profile change.

**Source data:** every plotted value comes from the two published Test 5 evidence tables — [`opportunity_family_activity_contrasts.csv`](../evidence/viewer_diagnosis/opportunity_family_activity_contrasts.csv) (Figures 12 and 13) and [`opportunity_conditioned_candidate_mechanisms.csv`](../evidence/viewer_diagnosis/opportunity_conditioned_candidate_mechanisms.csv) (Figures 14A and 14B). Figure 12's indices are the family-wide weighted broad and regional levels reconstructed from the quintile rows of the first table. The `measured n` labels are profiles meeting each metric's evidence threshold. No profile-level data is added to the repository, and no separate figure-data table was needed.

## Test 4 — post-choice response and concentration mechanism — 2026-09

**Question:** what post-choice behaviours sit underneath concentrated viewing, and which of those findings are important enough to communicate visually before opportunity is added in Test 5?

**Established:** post-choice response is not one generic stickiness construct; validated resume is an intermediate pathway; replay requires a fixed observability horizon; and the same high concentration can correspond to materially different completion and replay behaviour as meaningful breadth increases. Several of those directions survive separate watch-hours and active-days controls.

**Not established:** final viewer segments, viewing headroom, causality, recommendation failure, durable viewer identity, or that replay necessarily occurs on the dominant title. Entitlement, catalogue reachability, language opportunity and other pre-choice constraints remain to be tested.

**Figures**

| # | File | Relationship | Form | Mode |
| --- | --- | --- | --- | --- |
| 09 | [`figure_09_resume_is_a_pathway.png`](figure_09_resume_is_a_pathway.png) | Part-to-whole | 100% stacked horizontal bar | Explanatory |
| 10A | [`figure_10a_rewatch_capture_by_horizon.png`](figure_10a_rewatch_capture_by_horizon.png) | Cumulative distribution / change across horizon | Line | Explanatory |
| 10B | [`figure_10b_rewatch_observability_by_horizon.png`](figure_10b_rewatch_observability_by_horizon.png) | Observability across horizon | Line | Explanatory |
| 11A | [`figure_11a_completion_deviation_high_concentration.png`](figure_11a_completion_deviation_high_concentration.png) | Deviation from activity benchmark | Zero-centred deviation line/dot comparison | Explanatory |
| 11B | [`figure_11b_replay_deviation_high_concentration.png`](figure_11b_replay_deviation_high_concentration.png) | Deviation from activity benchmark | Zero-centred deviation line/dot comparison | Explanatory |

Figures 11A and 11B are the headline Test 4 mechanism visual. Figures 06–08 are reserved for the Test 3 visual sequence.

**Reasoning:** Figure 09 uses part-to-whole because the analytical point is the composition of eventual outcomes after a validated resume, not the raw number of resumed assets. Figure 10 is intentionally split: 10A asks how much eventual replay a horizon captures, while 10B asks how much follow-up remains observable. Combining them on one axis would force the reader to compare different constructs visually. Figure 11 uses a zero baseline because the values are deviations from comparable activity peers, and "above or below context" is the actual analytical question. Watch-hours and active-days controls remain separate; averaging them would invent a score the analysis never defined.

**Rejected:** a Sankey diagram for resume outcomes, because flow magnitude is not the question and it would visually overcomplicate a simple semantic result. A dense 5×5 breadth × concentration heatmap as the headline mechanism figure, because four control/outcome combinations would demand heavy visual decoding and hide the central contrast. The rejected 4D.2 crossed watch-hours × active-days benchmark is not visualised, because its reference strata were too sparse and the design was rejected analytically.

**Not carried:** Figure 09 does not imply that resuming causes completion. Figure 10 does not claim that 14 days captures all replay; it documents the trade-off used to standardise measurement. Figure 11 deliberately focuses on concentration Q5 and breadth Q1–Q3, so it is not a complete map of every breadth × concentration cell; the full cell evidence remains in the published CSV. Baseline versus Final differences shown here are descriptive, not within-profile longitudinal change.

**Source data:** every plotted value is read directly from the published evidence tables — [`return_semantic_closure.csv`](../evidence/mart_audit/return_semantic_closure.csv) (Figure 09), [`rewatch_latency_observability.csv`](../evidence/mart_audit/rewatch_latency_observability.csv) (Figures 10A and 10B) and [`concentration_mechanism_controls.csv`](../evidence/viewer_diagnosis/concentration_mechanism_controls.csv) (Figures 11A and 11B). No separate figure-data tables are needed. The n labels in Figures 11A and 11B are measured profiles: those meeting the evidence threshold behind each deviation (at least five known outcomes for completion, at least three for replay).
