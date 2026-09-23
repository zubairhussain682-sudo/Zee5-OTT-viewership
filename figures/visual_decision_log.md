# Visual decision log

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
