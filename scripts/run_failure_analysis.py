#!/usr/bin/env python
"""Analyze full system junctures and categorize into 6 failure types.

Failure types:
  1. Superseded while held
  2. Suppressed submission (no evaluate scaffold at a submit)
  3. Held then dropped (no pause arrived)
  4. Late delivery (> 120s after triggering juncture)
  5. Abandoned after (no learner event within 30 min)
  6. Interrupted a burst

Saves results to results/phase2/failure_analysis.json.
"""
import json
import pathlib
import sys
from collections import defaultdict

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from coach.core import TrajectoryCoach
from coach.dataset import load_split
from coach.timing import detect_junctures, BURST_THRESHOLD

OUTPUT_DIR = _ROOT / 'results' / 'phase2'
OUTPUT = OUTPUT_DIR / 'failure_analysis.json'

LATE_THRESHOLD = 120.0   # seconds: delivery > 120s after juncture = late
ABANDON_THRESHOLD = 1800  # 30 minutes

FAILURE_TYPES = {
    1: 'Superseded while held',
    2: 'Suppressed submission (no evaluate scaffold at submit)',
    3: 'Held then dropped (no pause arrived)',
    4: 'Late delivery (>120s after triggering juncture)',
    5: 'Abandoned after (no learner event within 30 min)',
    6: 'Interrupted a burst',
}


def main():
    print('Loading test split events ...')
    events = load_split(split='test')
    print(f'  {len(events)} events loaded.')

    # Run full system
    print('Running full system ...')
    coach = TrajectoryCoach(
        mode='adaptive', cooldown=180, max_prompts=3,
        use_timing_gate=True, use_evidence_floor=True,
    )
    decisions = []
    for event in events:
        d = coach.observe(event)
        decisions.append(d)

    dec_dicts = [
        {'phase': d.phase, 'reason': d.reason, 'prompt': d.prompt, 'evidence': d.evidence}
        for d in decisions
    ]
    junctures = detect_junctures(events, dec_dicts)
    print(f'  {len(junctures)} junctures detected.')

    # Build student event index for failure analysis
    student_events = defaultdict(list)
    for ev in events:
        student_events[ev.student].append(ev)

    # Identify submits with no evaluate scaffold
    submit_events = [(ev, dec) for ev, dec in zip(events, decisions)
                     if ev.event == 'submit']
    suppressed_submissions = [
        (ev, dec) for ev, dec in submit_events if dec.phase == 'wait'
    ]

    # Categorize failures
    counts = {i: 0 for i in range(1, 7)}
    failure_examples = {i: [] for i in range(1, 7)}
    success_examples = []

    for j in junctures:
        outcome = j['outcome']
        pause_gap = j.get('pause_gap')
        delivered_at = j.get('delivered_at')
        triggered_at = j.get('triggered_at', j.get('time', 0))
        interrupted = j.get('interrupted', False)

        if outcome == 'superseded':
            counts[1] += 1
            if len(failure_examples[1]) < 2:
                failure_examples[1].append(j)
        elif outcome == 'dropped':
            counts[3] += 1
            if len(failure_examples[3]) < 2:
                failure_examples[3].append(j)
        elif outcome == 'released':
            if interrupted:
                counts[6] += 1
                if len(failure_examples[6]) < 2:
                    failure_examples[6].append(j)
            elif delivered_at is not None and delivered_at - triggered_at > LATE_THRESHOLD:
                counts[4] += 1
                if len(failure_examples[4]) < 2:
                    failure_examples[4].append(j)
            else:
                # Success
                if len(success_examples) < 2:
                    success_examples.append(j)

    # Type 2: suppressed submissions
    counts[2] = len(suppressed_submissions)
    for ev, dec in suppressed_submissions[:2]:
        failure_examples[2].append({
            'student': ev.student,
            'time': ev.time,
            'phase': dec.phase,
            'reason': dec.reason,
        })

    # Type 5: check for abandoned sessions (last event in student stream far in time)
    for student, s_events in student_events.items():
        sorted_events = sorted(s_events, key=lambda e: e.time)
        for i in range(len(sorted_events) - 1):
            gap = sorted_events[i + 1].time - sorted_events[i].time
            if gap > ABANDON_THRESHOLD:
                counts[5] += 1
                if len(failure_examples[5]) < 2:
                    failure_examples[5].append({
                        'student': student,
                        'time': sorted_events[i].time,
                        'gap': gap,
                        'type': 'abandoned',
                    })

    total_junctures = len(junctures)
    result = {
        'total_junctures': total_junctures,
        'failure_types': {},
        'success_examples': success_examples,
        'failure_examples': {},
    }

    for ftype, label in FAILURE_TYPES.items():
        count = counts[ftype]
        share = round(count / max(total_junctures, 1), 4)
        result['failure_types'][str(ftype)] = {
            'label': label,
            'count': count,
            'share': share,
        }
        result['failure_examples'][str(ftype)] = failure_examples[ftype]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f'\nFailure analysis saved to {OUTPUT}')
    print('Failure type counts:')
    for ftype, label in FAILURE_TYPES.items():
        print(f'  [{ftype}] {label}: {counts[ftype]}')


if __name__ == '__main__':
    main()

