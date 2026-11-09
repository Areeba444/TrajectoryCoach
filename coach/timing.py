"""G1 metrics: is a scaffold delivered at an appropriate moment?

Phase 1 proposed educator ratings of timing appropriateness. Two educator
raters were not available inside Phase 2, so timing is measured from the logs
instead, with a small blind human rating kept as a validation sample. The
log-derived measures below are fixed before any comparison is run.

IMPORTANT. This is a replay of logs recorded in 2016. No learner in the data
ever saw a scaffold from this system. Nothing measured here can be an effect
of prompting. Every measure below describes *which moments a policy selects*
and what the learner did at those moments anyway. deliberation_delta in
particular is a property of the selected moments, not a treatment effect, and
must not be reported as one.

interruption_rate   prompt lands inside a typing burst: an edit within
                    BURST seconds before and within BURST seconds after. A
                    lower value is better; this is the primary G1 measure.
pause_aligned       prompt is followed by a natural pause of at least PAUSE
                    seconds, so the learner can read it without losing flow.
juncture_precision  prompt lands on an observable decision point (first edit
                    of a task, a repeated-execution window, or a submission).
                    True by construction for the proposed policy; reported for
                    completeness, not as evidence.
juncture_coverage   share of all observable decision points that received a
                    prompt within COVER seconds.
median_response_gap seconds from the prompt to the learner's next event.
deliberation_delta  change in the deliberation ratio, edits / (edits + runs),
                    in the 300 s after the prompt compared with the 300 s
                    before. The ratio is bounded in [0, 1], so it is stable
                    when a window contains very few executions. Positive means
                    proportionally more editing and less blind re-running,
                    which is the behavioural direction a planning or
                    monitoring scaffold is meant to encourage. Windows with
                    fewer than MIN_WINDOW events are not scored.
"""
import bisect, random, statistics
from .core import EDIT

BURST = 5.0
PAUSE = 20.0
COVER = 30.0
WINDOW = 300.0
MIN_WINDOW = 5


class TimingIndex:
    """Per-learner timeline used to score any policy's delivered prompts."""

    def __init__(self, events):
        self.times, self.kinds = {}, {}
        for e in events:
            self.times.setdefault(e.student, []).append(e.time)
            self.kinds.setdefault(e.student, []).append(e.event)

    def _slice(self, student, lo, hi):
        t = self.times.get(student)
        if not t:
            return [], []
        a, b = bisect.bisect_left(t, lo), bisect.bisect_right(t, hi)
        return t[a:b], self.kinds[student][a:b]

    def _edit_within(self, student, at, before):
        lo, hi = (at - BURST, at) if before else (at, at + BURST)
        _, kinds = self._slice(student, lo, hi)
        return any(k in EDIT for k in kinds)

    def _next_gap(self, student, at):
        t = self.times.get(student) or []
        i = bisect.bisect_right(t, at)
        return (t[i] - at) if i < len(t) else None

    def _deliberation(self, student, lo, hi):
        """Share of actions that are edits rather than executions, in [0, 1]."""
        _, kinds = self._slice(student, lo, hi)
        runs = sum(1 for k in kinds if k == 'run')
        edits = sum(1 for k in kinds if k in EDIT)
        total = runs + edits
        return (edits / total) if total >= MIN_WINDOW else None

    def score_one(self, student, at):
        gap = self._next_gap(student, at)
        before = self._deliberation(student, at - WINDOW, at)
        after = self._deliberation(student, at, at + WINDOW)
        return {
            'interrupting': (self._edit_within(student, at, True)
                             and self._edit_within(student, at, False)),
            'pause_aligned': gap is not None and gap >= PAUSE,
            'response_gap': gap,
            'deliberation_delta': (after - before) if (before is not None and after is not None) else None,
        }


def junctures(events, window_seconds=300, run_threshold=3):
    """Every observable decision point in the stream, as (student, time).

    This is exactly the candidate set the uncapped rule policy fires on, so it
    is the denominator for coverage.
    """
    out, state = [], {}
    for e in events:
        s = state.setdefault(e.student, {'win': [], 'runs': 0, 'edits': 0,
                                         'first': True, 'task': None, 'last': None})
        if s['task'] != (e.part, e.exercise) or (s['last'] is not None and e.time - s['last'] > 1800):
            s.update(win=[], runs=0, edits=0, first=True, task=(e.part, e.exercise))
        s['win'].append(e)
        if e.event == 'run':
            s['runs'] += 1
        elif e.event in EDIT:
            s['edits'] += 1
        while s['win'] and e.time - s['win'][0].time > window_seconds:
            old = s['win'].pop(0)
            if old.event == 'run':
                s['runs'] -= 1
            elif old.event in EDIT:
                s['edits'] -= 1
        if e.event == 'submit':
            out.append((e.student, e.time))
        elif s['first'] and e.event in EDIT:
            out.append((e.student, e.time))
        elif e.event == 'run' and s['runs'] >= run_threshold and s['edits']:
            out.append((e.student, e.time))
        if e.event in EDIT:
            s['first'] = False
        s['last'] = e.time
    return out


def _cluster_bootstrap(per_learner, reps=1000, seed=0):
    """Resample learners, not prompts, because prompts cluster within learners."""
    keys = sorted(per_learner)
    pooled = [v for k in keys for v in per_learner[k]]
    if not pooled:
        return None, None, None
    point = statistics.fmean(pooled)
    rng, draws = random.Random(seed), []
    for _ in range(reps):
        sample = []
        for _ in keys:
            sample.extend(per_learner[keys[rng.randrange(len(keys))]])
        if sample:
            draws.append(statistics.fmean(sample))
    draws.sort()
    lo = draws[int(0.025 * len(draws))]
    hi = draws[int(0.975 * len(draws)) - 1]
    return point, lo, hi


def evaluate(decisions, index, all_junctures, seed=0):
    """Score a policy's delivered prompts against the G1 measures."""
    by_learner_int, by_learner_pause, by_learner_delta = {}, {}, {}
    gaps, hit = [], set()
    jset = {}
    for s, t in all_junctures:
        jset.setdefault(s, []).append(t)
    for s in jset:
        jset[s].sort()
    precise = 0
    for d in decisions:
        s, at = d.evidence['student'], d.evidence['time']
        m = index.score_one(s, at)
        by_learner_int.setdefault(s, []).append(1.0 if m['interrupting'] else 0.0)
        by_learner_pause.setdefault(s, []).append(1.0 if m['pause_aligned'] else 0.0)
        if m['deliberation_delta'] is not None:
            by_learner_delta.setdefault(s, []).append(m['deliberation_delta'])
        if m['response_gap'] is not None:
            gaps.append(m['response_gap'])
        times = jset.get(s, [])
        i = bisect.bisect_left(times, at - COVER)
        if i < len(times) and times[i] <= at + COVER:
            precise += 1
            hit.add((s, times[i]))
    n = len(decisions)
    ip, ilo, ihi = _cluster_bootstrap(by_learner_int, seed=seed)
    pp, plo, phi = _cluster_bootstrap(by_learner_pause, seed=seed)
    dp, dlo, dhi = _cluster_bootstrap(by_learner_delta, seed=seed)
    return {
        'prompts': n,
        'interruption_rate': ip, 'interruption_ci': [ilo, ihi],
        'pause_aligned': pp, 'pause_aligned_ci': [plo, phi],
        'juncture_precision': (precise / n) if n else None,
        'juncture_coverage': (len(hit) / len(all_junctures)) if all_junctures else None,
        'median_response_gap': statistics.median(gaps) if gaps else None,
        'deliberation_delta': dp, 'deliberation_delta_ci': [dlo, dhi],
        'learners_prompted': len(by_learner_int),
    }
