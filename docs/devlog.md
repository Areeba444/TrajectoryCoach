# Development log

Each entry records what was observed, what changed because of it, and what the
change measured. Every number is from a file in `results/phase2/` and can be
regenerated with the scripts named in the entry. Entries are in order.

---

## 2026-10-17 — Phase 1 baseline

**State.** Event engine with four policies (`rule`, `adaptive`, `no_memory`,
`no_cooldown`), a read-only tool interface, an OpenAI adapter that had never
been called, and a replay over all 24 learners.

**Limitation carried into Phase 2.** Every Phase 1 number came from the same
24 learners that the thresholds were chosen on, so nothing was held out. No
live model call had been made, so no cost, latency or reliability figure
existed. The reported prompt counts were operational only.

---

## 2026-11-07 — Fixed learner split

**Observed.** Phase 1 reported replay numbers over all 24 learners, so the
window length, cooldown and prompt budget were effectively tuned on the same
data the results came from.

**Change.** `scripts/make_splits.py` writes `data/splits.json` using a rule
fixed in advance: learners sorted by identifier, every third learner to test.
The rule uses no outcome, so it cannot be tuned. Dev holds 16 learners and
1,871,292 events; test holds 8 learners and 726,897 events.

**Effect.** All headline numbers now come from learners never used for any
design decision. Phase 1 figures are not comparable to Phase 2 figures and are
not reported as if they were.

---

## 2026-11-07 — Measured interruption for the first time, and found the policy worse than its own baseline

**Observed.** Added log-derived timing measures (`coach/timing.py`) and ran
them over the test split. The Phase 1 `adaptive` policy interrupted a typing
burst on **0.657** of its scaffolds, against **0.274** for the uncapped `rule`
baseline. The policy that was supposed to be more considerate was two and a
half times worse per scaffold.

**Cause.** The episode budget and the cooldown remove scaffolds
indiscriminately. The ones that survive are concentrated in dense
edit–run activity, which is exactly where an interruption costs most. Cutting
volume is not the same as choosing moments.

**Change.** Added the **timing gate** (`gate_seconds`, `gate_horizon` in
`coach/core.py`). A scaffold that would land inside a burst is held, and
released only once the learner has been inactive for 20 s; it is dropped if
no pause arrives within the horizon. This is the G1 component and it can be
switched off for ablation.

**Effect.** Interruption fell from **0.657 to 0.026** on the test split, a
25-fold reduction, and pause alignment rose from 0.168 to 0.424. Decision-point
coverage fell from 0.341 to 0.146: the gate buys calm at the cost of silence.
Both directions are reported.

*Reproduce:* `python -m scripts.run_experiments --split test`

---

## 2026-11-07 — Replaced an unstable behavioural measure

**Observed.** The first behavioural measure was edits per run after a scaffold
minus edits per run before it. Windows containing one or two executions sent
the ratio to very large values, so the bootstrap interval for the on-demand
comparator came out as −13.45 ± 10.36 — a number with no usable meaning.

**Change.** Replaced it with the bounded deliberation ratio,
edits / (edits + runs), scored only on windows holding at least five actions.

**Effect.** Intervals became usable. The full system now measures **+0.003,
95% CI [−0.004, +0.008]**, which includes zero, while every baseline is
reliably negative (rule baseline −0.014, CI [−0.019, −0.006]). The honest
reading is that the gate removes a negative shift rather than producing a
positive one.

---

## 2026-11-07 — Strengthened the base-paper comparator after it proved too weak

**Observed.** The first on-demand comparator placed simulated help requests
uniformly, or weighted towards repeated-execution windows. Both interrupted
on about **0.83** of scaffolds. Winning against that is meaningless: two
thirds of all events in this dataset are keystrokes, so any randomly chosen
moment is inside a burst.

**Cause.** A learner who stops to ask for help has, by definition, stopped
typing. Sampling request moments uniformly models something no learner does.

**Change.** Added the `pause` request model, which places requests only inside
natural pauses and delivers the hint 20 s into the pause, matching the
proposed system's own delivery rule. This is now the headline E2 comparator.

**Effect.** Comparator interruption fell from 0.837 to **0.127**, which cut our
own advantage from roughly 32-fold to roughly 5-fold. The weaker comparators
are still reported, labelled as weaker.

---

## 2026-11-07 — Failure analysis exposed scaffolds built on almost no evidence

**Observed.** `scripts/run_failure_analysis.py` over the test split found that
**37.2%** of delivered scaffolds came from an observation window holding fewer
than five events, so the stated reason rested on almost nothing. A further
40.0% were superseded while held and 24.8% were dropped when no pause arrived.

**Change.** Added the **evidence floor** (`min_evidence` in `coach/core.py`):
no scaffold is delivered from a window below five events. This is a G2
component, because grounding means refusing to speak without evidence as much
as it means checking what is said.

**Effect.** Recorded in `results/phase2/experiments_test.json` as the
`E5_ablation_no_evidence_floor` contrast against `E3_proposed_full`.

*Reproduce:* `python -m scripts.run_failure_analysis`

---

## 2026-11-08 — Abandoned a blind cross-condition rating sheet

**Observed.** Phase 1 promised educator ratings of timing appropriateness.
With no educators available, the first replacement was a sheet of 30
scaffolds drawn equally from the full system, the on-demand comparator and
the ungated ablation, shuffled under opaque identifiers so the two authors
could rate them without knowing the source.

**Why it failed.** The conditions differ precisely in how long the learner
has been inactive when the scaffold arrives, and that gap is also the thing a
rater must see to judge timing. A check of the trial sheet found the
inactivity bucket separated the gated and ungated conditions with no overlap
at all (gated 10/10 in the 5--30 s bucket, ungated 10/10 under 5 s), and the
on-demand comparator was additionally identifiable because every one of its
scaffolds was a planning prompt. No relabelling can blind a comparison whose
treatment is the thing being rated.

**Change.** Replaced it with a single-condition sheet: 30 scaffolds from the
full system, rated for timing and relevance by both authors independently,
scored with a linearly weighted kappa.

**Effect.** The cross-condition claim now rests entirely on the log-derived
measures. The human rating supplies the relevance figure that hypothesis H2
needs and a check that the chosen moments look reasonable to a person. This
is weaker than what Phase 1 promised and the paper says so.

*Reproduce:* `python -m scripts.make_rating_sheet`, then
`python -m scripts.score_ratings results/phase2/ratings_*.csv`

---

## 2026-11-09 — Rebuilt the measurement layer after the reported metrics proved degenerate

**Observed.** A parallel implementation of the experiment harness was committed
to the repository (commits `7721083`–`9d9bad5`). Reading its saved results in
`results/phase2/experiments_test.json` showed four faults that make the
reported numbers unusable:

1. `interruption_rate` was **0.0 in all thirteen conditions**, including the
   uncapped rule baseline and the unmodified Phase 1 policy. With a 45 s gate
   and a 15 s burst threshold, no edit can fall inside the burst window before
   a release, so the metric was zero by construction rather than by result.
2. `pause_aligned_rate` and `coverage` were identical in every row, so two of
   the three headline measures were the same quantity reported twice.
3. `coverage` used a different denominator per condition: the baseline divided
   by all 10,687 junctures while the full system divided by its own 1,328
   delivered scaffolds, giving 1.0. The conditions were therefore not
   comparable.
4. Seeds had no effect. The `pause` and `stuck` comparators returned identical
   values to four decimal places across seeds 0, 1 and 2, so the standard
   deviation required for stochastic configurations would have been exactly
   zero.

`deliberation_delta` was also unbounded, ranging from 82 s to 12,603 s across
conditions that differ only slightly.

**Change.** Restored the measurement layer described in the earlier entries:
the burst-based interruption test with the gate at 20 s, pause alignment and
coverage as separate quantities with a common denominator (all observable
decision points in the split), the bounded deliberation ratio, and the cluster
bootstrap over learners.

**Effect.** The measures discriminate again. Interruption now ranges from
0.0206 for the full system to 0.2736 for the uncapped baseline and 0.8365 for
the weakest comparator, and the ablation separates the timing gate
(0.0206 → 0.2690) from the components that turn out not to bind. Seeds now
vary: the on-demand comparators give 461.0 ± 11.4, 488.3 ± 12.5 and
483.7 ± 11.2 scaffolds.

**What was kept.** The 30-item inter-rater study committed in `9d9bad5` is
genuine work and is preserved unchanged in `results/phase2/ratings_*.csv`.
Rescoring it here reproduces the published figures exactly (weighted kappa
0.3284 for timing and 0.3426 for relevance, pooled relevance 3.383).

**One limitation found while porting it.** That rating sheet showed each rater
the scaffold phase and the prompt text but nothing about when the scaffold was
delivered relative to the learner's activity. Timing cannot be judged from a
prompt alone, so the timing column is reported for completeness and no claim
rests on it. The relevance column is unaffected and is the figure hypothesis
H2 uses. Agreement is fair rather than strong (kappa 0.34), and the paper
should say so rather than lead with the mean.

*Reproduce:* `python -m scripts.run_experiments --split test` and
`python -m scripts.score_ratings results/phase2/ratings_minahil.csv results/phase2/ratings_areeba.csv`

---

## Known limitations not fixed in Phase 2

These were observed and deliberately left, with reasons.

- **No learner ever saw a scaffold.** This is a replay of logs recorded before
  this system existed. Every measure describes which moments a policy selects and what the
  learner did anyway. None of it is an effect of prompting, and none of it is
  a learning outcome.
- **Educator raters were not available.** Phase 1 specified two educators
  rating timing on a 0–4 scale. Log-derived measures replace that, with a
  30-item rating by the two authors as the only human check. It is not blind
  between conditions, for the reason recorded above.
- **Juncture precision is partly circular.** The proposed policy fires at
  junctures by construction, so that column is reported for completeness and
  no claim rests on it.
- **The grounding checker is a screen, not a verifier.** It catches claims
  that are definitely outside the evidence. A fluent, plausible and wrong
  statement that avoids the pattern list will pass.
- **The transfer study uses simulated learners.** It validates the rubric as
  an instrument. It says nothing about whether coaching helps people.
- **The VS Code extension promised in Phase 1 was not built.** The delivered
  interface is a command-line session that watches a real file on disk. The
  event schema is unchanged, so an editor front end remains a drop-in.
