# SQL

The public SQL is intentionally curated rather than exhaustive.

Queries are included when they:

- establish an important analytical grain or measurement rule;
- resolve a consequential ambiguity;
- protect a downstream interpretation from being misleading;
- or support a published analytical decision.

Routine debugging, inspection and redundant QA remain in the internal analytical workbench.

**`schema_understanding/`** — queries that establish the relational and temporal distinctions the diagnosis depends on: profile versus account, asset versus title, session versus event, and historical access.

**`mart_audit/`** — queries that test the measurement contracts required before behavioural diagnosis: meaningful title engagement, realistic opportunity, continuation observability and raw lineage — and, for the viewer-level base, grain and coverage, activity and session invariants, reconciliation with raw playback, breadth and concentration, and the historical opportunity fields behind reachable-catalogue conditioning.

**`diagnostics/`** — queries behind consequential diagnostic decisions: the known-outcome treatment of completion and abandonment, and the breadth × concentration mechanism check with separate activity controls. Their Python companions in [`scripts/diagnostics`](../scripts/diagnostics) rebuild resume and replay behaviour from raw playback. **Test 6C.2** is the exception to that pattern and is published in full as [`test6c2_baseline_anchor_cross_origin_behaviour.sql`](diagnostics/test6c2_baseline_anchor_cross_origin_behaviour.sql): it fixes each paired profile's Baseline title-origin anchor and measures Final viewing outside that ecosystem, which is the one Test 6 step a reviewer cannot reconstruct from the published tables alone. Opportunity conditioning added no query here on purpose: it reuses the breadth × concentration query unchanged so the states keep their original definition, and the reachable-catalogue and access-regime logic it adds is Python, in [`src/analytical_transforms/opportunity.py`](../src/analytical_transforms/opportunity.py).

Diagnostic SQL will be published only when it materially contributes to an insight, constraint, expectation or analytical decision.
