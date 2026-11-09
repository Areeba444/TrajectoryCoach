| Gap | Method / component | Metric | Base paper result | Our result | Addressed? | Caveat |
|---|---|---|---|---|---|---|
| Gap 1: timing | Timing gate: hold a scaffold until a 20 s pause | Interruption rate on held-out prefixes | 0.127 ± 0.014 (on-demand at pauses) | 0.021 | Partially | Ablating the gate raises interruption to 0.269; coverage falls against the uncapped baseline |
| Gap 2: grounding | Evidence floor, JSON schema, validator, read-only tools | Share of scaffolds containing an unsupported claim | 0.530 (unconstrained, same model) | 0.140 | Partially | Deterministic screen, not a semantic verifier |
| Gap 3: transfer | Delayed no-AI transfer task and four-point rubric | Spearman r with latent skill, simulated learners | 0.724 (assisted completion) | 0.793 ± 0.036 | Partially | Instrument validation only; no human learners |
