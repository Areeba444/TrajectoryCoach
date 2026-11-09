"""Base-paper comparator: learner-requested (on-demand) scaffolding.

The base paper [Phung et al., AIED 2025] delivers a hint only when the learner
asks for one. It reports 725 hints requested by 102 students over 14 questions,
which is 0.507 requests per student per question. We cannot observe real help
requests in the Zenodo logs, so request moments are *simulated* at that rate.
This is an adaptation of the base paper's interaction policy to our data, not a
reproduction of its reported numbers.

Two request models are provided so the comparator is not a straw man:

uniform   request moments fall anywhere in the learner's work on a question.
stuck     request moments are weighted towards repeated-execution episodes,
          which is where a learner is more likely to ask for help.
pause     request moments fall inside natural pauses, and the hint is
          delivered 20 s into the pause. A learner who stops to ask for help
          has by definition stopped typing, so this is the fairest comparator
          and is the one reported as the headline E2 result. It is matched to
          the proposed system on interruption by construction, which moves the
          comparison onto coverage and the behavioural measure.
"""
import math, random
from .core import EDIT, Decision, TrajectoryCoach

BASE_PAPER_RATE = 725 / (102 * 14)  # 0.5074... requests per student-question
PAUSE_GATE = 20.0                   # seconds of inactivity before a 'pause' request

PROMPTS = {
    'plan': 'Before the next step, state your goal and one input-output example you expect.',
    'monitor': 'What hypothesis are you checking with this run, and what result would support it?',
    'evaluate': 'What evidence would you use to check correctness, including an edge case?',
}


def _poisson(rng, lam):
    """Knuth's algorithm; the rate here is small so the loop is short."""
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def _phase_at(window_runs, window_edits, event, first_edit):
    """Which scaffold a requested hint turns into, given what is observable."""
    if event.event == 'submit':
        return 'evaluate'
    if event.event == 'run' and window_runs >= 3 and window_edits:
        return 'monitor'
    if first_edit and event.event in EDIT:
        return 'plan'
    return 'plan'  # a request always receives help; planning is the safe default


class OnDemandCoach:
    """Replays a learner-requested comparator over grouped events.

    Requests are drawn per (student, part, exercise) unit at the base paper's
    reported rate. Each request yields exactly one scaffold, so the comparator
    is never silent when the learner asks.
    """

    def __init__(self, request_model='stuck', seed=0, rate=BASE_PAPER_RATE,
                 window_seconds=300, run_threshold=3):
        if request_model not in ('uniform', 'stuck', 'pause'):
            raise ValueError('request_model must be uniform, stuck or pause')
        self.request_model, self.seed, self.rate = request_model, seed, rate
        self.window_seconds, self.run_threshold = window_seconds, run_threshold

    def _weights(self, events):
        """Stuck proxy: events inside a repeated-execution window weigh more."""
        weights, window, runs, edits = [], [], 0, 0
        for e in events:
            window.append(e)
            if e.event == 'run':
                runs += 1
            elif e.event in EDIT:
                edits += 1
            while window and e.time - window[0].time > self.window_seconds:
                old = window.pop(0)
                if old.event == 'run':
                    runs -= 1
                elif old.event in EDIT:
                    edits -= 1
            w = 1.0
            if runs >= self.run_threshold and edits:
                w = 4.0
            elif e.event == 'submit':
                w = 2.0
            weights.append(w)
        return weights

    def _pause_weights(self, events):
        """A learner who asks for help has stopped working first."""
        weights, prev = [], None
        for e in events:
            gap = 0.0 if prev is None else e.time - prev
            weights.append(1.0 if gap >= PAUSE_GATE else 0.0)
            prev = e.time
        if not any(weights):          # a unit with no pause at all
            weights = [1.0] * len(events)
        return weights

    def run(self, groups):
        """Return the list of delivered Decisions across all units."""
        rng = random.Random(self.seed)
        delivered = []
        for key in sorted(groups):
            events = groups[key]
            n = _poisson(rng, self.rate)
            if not n or not events:
                continue
            if self.request_model == 'uniform':
                idx = sorted(rng.randrange(len(events)) for _ in range(n))
            elif self.request_model == 'pause':
                idx = sorted(_weighted_index(rng, self._pause_weights(events)) for _ in range(n))
            else:
                idx = sorted(_weighted_index(rng, self._weights(events)) for _ in range(n))
            window, runs, edits, first_edit = [], 0, 0, True
            seen = set()
            for i, e in enumerate(events):
                window.append(e)
                if e.event == 'run':
                    runs += 1
                elif e.event in EDIT:
                    edits += 1
                while window and e.time - window[0].time > self.window_seconds:
                    old = window.pop(0)
                    if old.event == 'run':
                        runs -= 1
                    elif old.event in EDIT:
                        edits -= 1
                if i in idx and i not in seen:
                    seen.add(i)
                    phase = _phase_at(runs, edits, e, first_edit)
                    at = e.time
                    if self.request_model == 'pause' and i > 0:
                        # The request is made during the pause, not at the next keystroke.
                        at = min(e.time, events[i - 1].time + PAUSE_GATE)
                    evidence = {'student': e.student, 'part': e.part, 'exercise': e.exercise,
                                'source_row': e.source_row, 'time': at,
                                'window_seconds': self.window_seconds,
                                'window_events': len(window), 'runs': runs, 'edits': edits,
                                'current_event': e.event, 'outcomes_observed': False,
                                'request_model': self.request_model}
                    delivered.append(Decision(phase, 'Learner requested help (simulated)',
                                              PROMPTS[phase], evidence, 'on_demand'))
                if e.event in EDIT:
                    first_edit = False
        return delivered


def _weighted_index(rng, weights):
    total = sum(weights)
    r = rng.random() * total
    acc = 0.0
    for i, w in enumerate(weights):
        acc += w
        if r <= acc:
            return i
    return len(weights) - 1
