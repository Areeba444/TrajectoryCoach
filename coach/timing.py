"""Gap 1 — Intervention timing: timing gate, juncture detection, metrics.

The gate holds a triggered scaffold until a cognitive pause (gap ≥
GATE_SECONDS) arrives within PAUSE_HORIZON.  If a newer juncture triggers
first, the held scaffold is superseded.  If the horizon expires with no
pause, the scaffold is dropped.

Thresholds are engineering defaults, not validated diagnoses of cognition.
No course outcome is observed or inferred.
"""
import math, random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
from .core import Decision, Event

# ── Thresholds (all in seconds) ────────────────────────────────────────────
GATE_SECONDS    = 45    # inactivity gap that counts as a cognitive pause
PAUSE_HORIZON   = 300   # discard the held scaffold if no pause by this point
BURST_THRESHOLD = 15    # gaps below this are treated as typing bursts


# ── Per-learner gate state ──────────────────────────────────────────────────
@dataclass
class _GateState:
    pending_decision: Optional[Decision] = None
    pending_since: Optional[float]       = None   # wall-clock when scaffold was held
    last_event_time: Optional[float]     = None


class TimingGate:
    """Holds one pending scaffold per learner until a pause confirms delivery.

    Thread-safety: not required (single-threaded replay).
    """

    def __init__(self,
                 gate_seconds: float = GATE_SECONDS,
                 pause_horizon: float = PAUSE_HORIZON):
        self.gate_seconds  = gate_seconds
        self.pause_horizon = pause_horizon
        self._states: dict[str, _GateState] = defaultdict(_GateState)

    # ── Public interface ────────────────────────────────────────────────────

    def hold(self, student: str, decision: Decision, now: float) -> None:
        """Register a scaffold as pending for this learner."""
        gs = self._states[student]
        gs.pending_decision = decision
        gs.pending_since    = now
        gs.last_event_time  = now

    def tick(self, student: str, event_time: float) -> Optional[Decision]:
        """
        Notify the gate of a new event.  Returns the held Decision if the
        gap since the last event constitutes a pause (≥ gate_seconds) and
        the horizon has not expired.  Returns None otherwise.
        """
        gs = self._states[student]
        if gs.pending_decision is None:
            gs.last_event_time = event_time
            return None

        gap = (event_time - gs.last_event_time) if gs.last_event_time is not None else 0.0
        gs.last_event_time = event_time

        # Horizon check — drop if too much time passed without a pause
        age = event_time - gs.pending_since
        if age > self.pause_horizon:
            gs.pending_decision = None
            gs.pending_since    = None
            return None

        # Pause check
        if gap >= self.gate_seconds:
            decision = gs.pending_decision
            gs.pending_decision = None
            gs.pending_since    = None
            return decision

        return None

    def supersede(self, student: str) -> bool:
        """Cancel the held scaffold because a newer juncture arrived."""
        gs = self._states[student]
        had = gs.pending_decision is not None
        gs.pending_decision = None
        gs.pending_since    = None
        return had

    def drop(self, student: str) -> bool:
        """Explicitly drop the held scaffold (horizon expired externally)."""
        return self.supersede(student)

    def pending(self, student: str) -> bool:
        """True if a scaffold is currently held for this learner."""
        return self._states[student].pending_decision is not None


# ── Juncture detection (post-hoc, for evaluation) ──────────────────────────

def detect_junctures(
        events: list[Event],
        decisions: list[dict],
        gate_seconds: float = GATE_SECONDS,
        pause_horizon: float = PAUSE_HORIZON,
        burst_threshold: float = BURST_THRESHOLD,
) -> list[dict]:
    """
    Map each non-wait decision to a juncture record describing its fate.

    Returns a list of dicts with keys:
        student, triggered_at, phase, delivered_at,
        outcome ('released' | 'superseded' | 'dropped'),
        pause_gap, interrupted
    """
    # Build a per-student time-ordered event list
    by_student: dict[str, list[Event]] = defaultdict(list)
    for e in events:
        by_student[e.student].append(e)
    for lst in by_student.values():
        lst.sort(key=lambda e: (e.time, e.source_row))

    # Build decision lookup by (student, source_row)
    dec_lookup: dict[tuple, dict] = {}
    for d in decisions:
        ev = d.get('evidence', {})
        key = (str(ev.get('student', '')), int(ev.get('source_row', 0)))
        dec_lookup[key] = d

    junctures = []
    for student, evts in by_student.items():
        # Walk events; for each triggered scaffold apply gate logic
        pending: Optional[tuple[float, dict]] = None   # (triggered_at, decision)
        last_time: Optional[float] = None

        for i, evt in enumerate(evts):
            gap = (evt.time - last_time) if last_time is not None else 0.0
            key = (student, evt.source_row)

            # Does this event carry a triggered scaffold?
            if key in dec_lookup and dec_lookup[key]['phase'] != 'wait':
                dec = dec_lookup[key]
                if pending is not None:
                    # Previous scaffold superseded by this one
                    junctures.append({
                        'student'      : student,
                        'triggered_at' : pending[0],
                        'phase'        : pending[1]['phase'],
                        'delivered_at' : None,
                        'outcome'      : 'superseded',
                        'pause_gap'    : None,
                        'interrupted'  : None,
                    })
                pending = (evt.time, dec)

            # Gate tick
            if pending is not None:
                trig_at, dec = pending
                age = evt.time - trig_at

                if age > pause_horizon:
                    junctures.append({
                        'student'      : student,
                        'triggered_at' : trig_at,
                        'phase'        : dec['phase'],
                        'delivered_at' : None,
                        'outcome'      : 'dropped',
                        'pause_gap'    : None,
                        'interrupted'  : None,
                    })
                    pending = None
                elif gap >= gate_seconds:
                    interrupted = gap < burst_threshold   # always False here, but kept for clarity
                    junctures.append({
                        'student'      : student,
                        'triggered_at' : trig_at,
                        'phase'        : dec['phase'],
                        'delivered_at' : evt.time,
                        'outcome'      : 'released',
                        'pause_gap'    : gap,
                        'interrupted'  : gap < burst_threshold,
                    })
                    pending = None

            last_time = evt.time

        # Remaining pending at end-of-stream → dropped
        if pending is not None:
            trig_at, dec = pending
            junctures.append({
                'student'      : student,
                'triggered_at' : trig_at,
                'phase'        : dec['phase'],
                'delivered_at' : None,
                'outcome'      : 'dropped',
                'pause_gap'    : None,
                'interrupted'  : None,
            })

    return junctures


# ── Metric computation ──────────────────────────────────────────────────────

def compute_metrics(junctures: list[dict]) -> dict:
    """
    Compute primary timing metrics from a list of juncture records.

    Returns:
        scaffolds_delivered  : int
        total_junctures      : int
        interruption_rate    : float  fraction of delivered where interrupted == True
        pause_aligned_rate   : float  fraction where outcome == 'released'
        coverage             : float  delivered / total_junctures
        deliberation_delta   : float  mean pause_gap at released − mean gap at non-released
    """
    total     = len(junctures)
    delivered = [j for j in junctures if j['outcome'] == 'released']
    n_del     = len(delivered)

    if total == 0:
        return {
            'scaffolds_delivered' : 0,
            'total_junctures'     : 0,
            'interruption_rate'   : 0.0,
            'pause_aligned_rate'  : 0.0,
            'coverage'            : 0.0,
            'deliberation_delta'  : 0.0,
        }

    interrupted = [j for j in delivered if j.get('interrupted')]
    interruption_rate  = len(interrupted) / n_del if n_del else 0.0
    pause_aligned_rate = n_del / total
    coverage           = n_del / total   # same denominator for comparability

    # Deliberation delta: mean pause_gap at delivered vs at non-delivered (dropped/superseded)
    del_gaps     = [j['pause_gap'] for j in delivered if j['pause_gap'] is not None]
    non_del_gaps = [j['pause_gap'] for j in junctures
                    if j['outcome'] != 'released' and j['pause_gap'] is not None]
    mean_del     = sum(del_gaps)     / len(del_gaps)     if del_gaps     else 0.0
    mean_non_del = sum(non_del_gaps) / len(non_del_gaps) if non_del_gaps else 0.0
    deliberation_delta = mean_del - mean_non_del

    return {
        'scaffolds_delivered' : n_del,
        'total_junctures'     : total,
        'interruption_rate'   : round(interruption_rate,  4),
        'pause_aligned_rate'  : round(pause_aligned_rate, 4),
        'coverage'            : round(coverage,            4),
        'deliberation_delta'  : round(deliberation_delta, 4),
    }


# ── Cluster bootstrap (by learner) ─────────────────────────────────────────

def cluster_bootstrap(
        junctures: list[dict],
        n_boot: int = 1000,
        seed: int   = 0,
        alpha: float = 0.05,
) -> dict:
    """
    Bootstrap confidence intervals by resampling LEARNERS (not scaffolds).
    Scaffolds cluster within learners, so resampling scaffolds would
    understate the sampling variance.

    Returns {metric: [lower, upper]} for each numeric metric in compute_metrics.
    """
    rng = random.Random(seed)
    students = list({j['student'] for j in junctures})
    if not students:
        return {}

    by_student: dict[str, list[dict]] = defaultdict(list)
    for j in junctures:
        by_student[j['student']].append(j)

    boot_metrics: dict[str, list[float]] = defaultdict(list)
    for _ in range(n_boot):
        sample_students = rng.choices(students, k=len(students))
        sample_junctures = [j for s in sample_students for j in by_student[s]]
        m = compute_metrics(sample_junctures)
        for k, v in m.items():
            if isinstance(v, float):
                boot_metrics[k].append(v)

    lo_idx = int(math.floor(alpha / 2 * n_boot))
    hi_idx = int(math.ceil((1 - alpha / 2) * n_boot)) - 1
    ci = {}
    for k, vals in boot_metrics.items():
        vals.sort()
        ci[k] = [
            round(vals[max(0, lo_idx)], 4),
            round(vals[min(len(vals)-1, hi_idx)], 4),
        ]
    return ci

