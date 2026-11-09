"""AIMS base-paper on-demand hint comparator (Experiment 2 baseline).

Three request models:
  'pause'   – request at first pause >= 45s (most likely to be learner-initiated)
  'stuck'   – request at run #3+ within window (stuck-detection heuristic)
  'uniform' – uniform random request at AIMS rate per student-question

Target rate from AIMS paper: 725 hints / 102 students / 14 questions ≈ 0.5077.
"""
import random
from collections import defaultdict
from typing import Optional

from .core import Event, Decision, LearnerState, TrajectoryCoach, EVENTS
from .timing import GATE_SECONDS, compute_metrics, detect_junctures

# AIMS paper target rate
AIMS_REQUEST_RATE = 0.5077   # requests per student-question

_MODELS = {'pause', 'stuck', 'uniform'}


class OnDemandBaseline:
    """
    Simulates AIMS-style on-demand hints on replay data.
    For each request model, produces the same metrics as the full system.

    Usage:
        b = OnDemandBaseline(model='pause', seed=0)
        for event in events:
            decision = b.observe(event)  # returns Decision or None
        metrics = b.metrics()
    """

    def __init__(self, model: str = 'pause', seed: int = 0):
        if model not in _MODELS:
            raise ValueError(f'Unknown model {model!r}. Choose from {sorted(_MODELS)}.')
        self.model = model
        self.seed = seed
        self._rng = random.Random(seed)

        # Per-student-question state
        self._requested: set[tuple[str, str, str]] = set()   # (student, part, exercise)
        self._last_time: dict[str, float] = {}
        self._run_count: dict[tuple[str, str, str], int] = defaultdict(int)
        self._sq_requested: set[tuple[str, str, str]] = set()

        # Recorded decisions and events (for metric computation)
        self._events: list[Event] = []
        self._decisions: list[Decision] = []

        # For uniform model: pre-draw request decision per (student, part, exercise)
        self._uniform_draws: dict[tuple[str, str, str], bool] = {}

    def _sq_key(self, event: Event) -> tuple[str, str, str]:
        return (event.student, event.part, event.exercise)

    def _should_request_uniform(self, key: tuple[str, str, str]) -> bool:
        if key not in self._uniform_draws:
            self._uniform_draws[key] = self._rng.random() < AIMS_REQUEST_RATE
        return self._uniform_draws[key]

    def observe(self, event: Event) -> Optional[Decision]:
        """Process one event; return a Decision if a hint is requested, else None."""
        self._events.append(event)
        key = self._sq_key(event)
        last = self._last_time.get(event.student)
        gap = 0.0 if last is None else event.time - last
        self._last_time[event.student] = event.time

        # Build minimal evidence dict
        evidence = {
            'student': event.student,
            'part': event.part,
            'exercise': event.exercise,
            'source_row': event.source_row,
            'time': event.time,
            'gap_seconds': gap,
            'window_events': 1,
            'outcomes_observed': False,
        }

        decision = None

        if self.model == 'pause':
            # Request at the first pause >= GATE_SECONDS for each student-question
            if key not in self._sq_requested and gap >= GATE_SECONDS:
                self._sq_requested.add(key)
                decision = Decision(
                    phase='monitor',
                    reason=f'On-demand pause request (gap={gap:.0f}s)',
                    prompt='What hypothesis are you currently checking?',
                    evidence=evidence,
                    provider='on_demand_pause',
                )

        elif self.model == 'stuck':
            # Request when run count reaches 3 within a student-question
            if event.event == 'run':
                self._run_count[key] += 1
            if key not in self._sq_requested and self._run_count[key] >= 3:
                self._sq_requested.add(key)
                decision = Decision(
                    phase='monitor',
                    reason=f'On-demand stuck request (runs={self._run_count[key]})',
                    prompt='What hypothesis are you currently checking?',
                    evidence=evidence,
                    provider='on_demand_stuck',
                )

        elif self.model == 'uniform':
            # Stochastic request at AIMS rate per student-question (one per sq)
            if key not in self._sq_requested and self._should_request_uniform(key):
                self._sq_requested.add(key)
                decision = Decision(
                    phase='monitor',
                    reason='On-demand uniform request (AIMS rate)',
                    prompt='What hypothesis are you currently checking?',
                    evidence=evidence,
                    provider='on_demand_uniform',
                )

        wait = Decision(
            phase='wait',
            reason='No on-demand request',
            prompt='',
            evidence=evidence,
            provider=f'on_demand_{self.model}',
        )
        d = decision if decision is not None else wait
        self._decisions.append(d)
        return d if decision is not None else None

    def metrics(self) -> dict:
        """Compute timing metrics over all observed events."""
        # Convert decisions to dict format for detect_junctures
        dec_dicts = []
        for d in self._decisions:
            dec_dicts.append({
                'phase': d.phase,
                'reason': d.reason,
                'prompt': d.prompt,
                'evidence': d.evidence,
            })
        junctures = detect_junctures(self._events, dec_dicts)
        m = compute_metrics(junctures)
        m['model'] = self.model
        m['seed'] = self.seed
        m['total_requests'] = sum(1 for d in self._decisions if d.phase != 'wait')
        return m

