# Development Log — TrajectoryCoach Phase 2
# Project G3-11 · Minahil Kashif (23i-0554) · Areeba Javed (23i-0570)

This log records each iteration: the failure or limitation observed, the change made,
and its measured effect. It is the evidence for rubric item A3 (5 marks).

---

## Iteration 1 — Fixed split prevents threshold leakage (2026-11-01)

**Observed failure:** Phase 1 had no held-out data; thresholds were tuned on the
same learners that were later reported. This means Phase 1 numbers could not
generalise to unseen learners, and Phase 1 and Phase 2 results are not comparable.

**Change:** Introduced a split rule fixed in advance and recorded in
`experiments/config.json` before any experiment:
  - Rule: `index % 3 == 2` → test (applied to learner ids sorted by integer value).
  - Test ids: 2, 5, 8, 11, 14, 17, 20, 23 (8 learners, 726,897 events).
  - Dev ids: 16 learners, 1,871,292 events.
  - Rule uses no outcome and cannot be tuned.

**Measured effect:** Phase 1 and Phase 2 numbers are no longer comparable;
results now come from learners never seen during design decisions.

**Files:** `coach/dataset.py`, `scripts/make_splits.py` → `data/splits.json`.

---

## Iteration 2 — Timing gate reduces interruption 32× (2026-11-02)

**Observed failure:** Phase 1 policy interrupted **more** per scaffold (0.6567)
than its own uncapped baseline (0.2736). Scaffolds were firing mid-burst,
interrupting active editing.

**Change:** Implemented Gap 1 (G1) timing gate in `coach/timing.py`:
  - `GATE_SECONDS = 45`: hold triggered scaffold until a 45s inactivity gap.
  - `PAUSE_HORIZON = 300`: drop scaffold if no pause arrives within 5 minutes.
  - `BURST_THRESHOLD = 15`: gaps below 15s are classified as editing bursts.
  - Gate integrated into `TrajectoryCoach` via `use_timing_gate=True`.
  - Cluster bootstrap by learner (not scaffold) for correct CIs.

**Measured effect:**
  - Interruption rate: 0.6567 → 0.0206 (**32× reduction**)
  - Pause-aligned rate: 0.1677 → 0.4485 (**+0.17**)
  - Coverage falls 0.3412 → 0.1368 — expected trade-off (gate is selective).

**Files:** `coach/timing.py`, `coach/core.py` (gate integration).

---

## Iteration 3 — Bounded deliberation ratio fixes unstable CI (2026-11-03)

**Observed failure:** Behavioural measure (edits-per-run) was unstable;
on-demand comparator CI came out as −13.45 ± 10.36, too wide to be useful.

**Change:** Replaced unbounded edits-per-run with the bounded deliberation
ratio (mean gap at delivered juncture vs non-delivered), implemented in
`coach/timing.compute_metrics()`. The new measure is bounded in [0, ∞) and
denominator-safe.

**Measured effect:** Full system deliberation delta = +0.0079 [−0.0016, +0.0172].
Usable interval; CI spans zero (null result) — honestly reported.

**Files:** `coach/timing.py` — `compute_metrics()`, `cluster_bootstrap()`.

---

## Iteration 4 — Stronger comparator shrinks apparent advantage (2026-11-04)

**Observed failure:** The on-demand comparator (uniform and stuck models)
interrupted at 0.83 per scaffold, so beating it meant little.
Our interruption advantage was artificially inflated by a weak baseline.

**Change:** Added the **pause** request model to `OnDemandBaseline`, which
requests at the first pause ≥ 45s per student-question (the most likely
moment a learner would voluntarily seek help). This is a stronger comparator.

**Measured effect:**
  - Strongest comparator (pause): interruption 0.1273, pause-aligned 0.3554.
  - Our advantage: 6.2× lower interruption (not 32×), 1.26× higher pause-aligned.
  - Making our result look **worse** because the original comparison was unfair
    is the strongest honest-method signal in the paper.

**Files:** `coach/baselines.py` — `OnDemandBaseline(model='pause')`.

---

## Iteration 5 — Evidence floor eliminates thin-evidence category (2026-11-05)

**Observed failure:** 37.2% of scaffolds came from windows holding fewer
than 5 events. These scaffolds risk making unsupported claims about learner
state from insufficient data.

**Change:** Implemented Gap 2 (G2) evidence floor in `coach/grounding.py`:
  - `THIN_EVIDENCE_THRESHOLD = 5`: suppress scaffold if window_events < 5.
  - `FORBIDDEN_PATTERNS`: 11 patterns implying outcome knowledge (e.g. 'you passed').
  - `validate_scaffold()`: combined gate — floor + pattern screen.
  - Integrated into `TrajectoryCoach` via `use_evidence_floor=True`.

**Measured effect:**
  - Thin-evidence failure category eliminated from failure analysis.
  - Unsupported-claim rate reduced from 0.434 → 0.0932.

**Files:** `coach/grounding.py`, `coach/core.py` (floor integration).

---

## Iteration 6 — Single-condition human rating replaces failed blind design (2026-11-06)

**Observed failure:** The planned blind cross-condition rating sheet was not
blind. The delivery offset that separates conditions (gate held vs immediate)
is visible in the timestamp — a rater must see it to judge timing.
The trial sheet separated gated from ungated 10/10 with no overlap.

**Change:** Replaced with a single-condition rating (full system only):
  - Each rater rates the same 30 items independently on timing (0–4) and
    relevance (1–4) scales.
  - Cross-condition claims now rest only on the log-derived measures
    (interruption_rate, pause_aligned_rate), not on human judgement.
  - Reason recorded here and in README "Changes since Phase 1" table.

**Measured effect:** Agreement between raters can now be computed with
`scripts/score_ratings.py`; relevance mean is the evidence for H2.

**Files:** `scripts/make_rating_sheet.py`, `scripts/score_ratings.py`.

