# Data in this repository

This repository is an analytical record, not a data store.

Full-resolution operational and analytical tables are maintained in the analysis environment, outside Git. They are large, they change as analysis proceeds, and a version-control history is the wrong place to keep them.

What the repository holds instead is what someone needs to understand and check the reasoning:

- **Methodology** — the business framing, data model, measurement rules and mart design in [`docs/`](../docs).
- **Reproducible analytical code** — the opportunity, qualification, continuation and eligibility logic in [`src/analytical_transforms`](../src/analytical_transforms), with independent checks and boundary fixtures in [`src/validation`](../src/validation), and diagnostic scripts in [`scripts/diagnostics`](../scripts/diagnostics).
- **Selected SQL** — schema understanding and mart audit queries in [`sql/`](../sql), chosen because each settles a consequential measurement question.
- **Compact evidence** — small outcome tables in [`evidence/`](../evidence) that support what the documentation claims.
- **Visual outputs** — in [`figures/`](../figures) as analysis produces them.

The boundary fixtures run on small in-memory frames and need no database or full tables.

When a published result needs data to be reproduced, the smallest derived table that supports it will be added to `evidence/`, with its grain, window, units and filters stated. A compact extract is never presented as a substitute for population-level evidence.
