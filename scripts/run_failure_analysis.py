"""Failure analysis on the test split: categories, frequencies, and cases.

A failure here is a case where the system did not do the thing it is for:
it stayed silent at a moment that warranted a scaffold, spoke at a moment it
should not have, or produced a scaffold the learner had no chance to use.
Categories are counted over the whole test split, then two representative
successes and two representative failures are written out with their traces.
"""
import json, pathlib
from collections import Counter

from coach.core import TrajectoryCoach, EDIT, decision_dict
from coach.dataset import iter_events
from coach import timing

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results' / 'phase2'
LOGS = ROOT / 'logs'
THIN_WINDOW = 5          # a window with fewer events than this is thin evidence
ABANDONED = 1800.0       # no further activity within 30 min of the scaffold

CATEGORIES = {
    'held_then_dropped': 'Scaffold held for a pause that never came inside the horizon.',
    'superseded': 'A newer juncture replaced a scaffold that was still waiting.',
    'suppressed_submission': 'A submission produced no evaluate scaffold because the '
                             'episode budget or cooldown was active. This is the most '
                             'costly silence, since a submission is the clearest moment '
                             'to ask for a self-check.',
    'thin_evidence': 'Scaffold delivered from a window holding very few events, so the '
                     'stated reason rests on almost no observation.',
    'abandoned_after': 'Learner produced no further event within 30 minutes, so the '
                       'scaffold could not be acted on in that session.',
    'late_delivery': 'The gate delayed the scaffold by more than 120 s past the juncture '
                     'that triggered it, so it may no longer match what the learner is doing.',
}


def main(split='test', gate_seconds=20, min_evidence=5):
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    events = list(iter_events(split))
    index = timing.TimingIndex(events)

    engine = TrajectoryCoach(mode='adaptive', gate_seconds=gate_seconds,
                             min_evidence=min_evidence)
    counts = Counter()
    delivered, failures, successes = [], [], []
    submissions = 0

    for e in events:
        d = engine.observe(e)
        if e.event == 'submit':
            submissions += 1
        if d.phase == 'wait':
            if e.event == 'submit' and d.reason in (
                    'Task/session prompt budget exhausted', 'Cooldown active',
                    'Waiting for learner response',
                    'Observation window below the evidence floor'):
                counts['suppressed_submission'] += 1
            continue
        delivered.append(d)
        at = d.evidence['time']
        m = index.score_one(d.evidence['student'], at)
        flags = []
        if d.evidence.get('window_events', 99) < THIN_WINDOW:
            flags.append('thin_evidence')
        gap = m['response_gap']
        if gap is None or gap > ABANDONED:
            flags.append('abandoned_after')
        if d.evidence.get('delivery_delay', 0) > 120:
            flags.append('late_delivery')
        if m['interrupting']:
            flags.append('interrupted_burst')
        for f in flags:
            counts[f] += 1
        record = {'student': d.evidence['student'], 'phase': d.phase,
                  'reason': d.reason, 'prompt': d.prompt,
                  'source_row': d.evidence['source_row'],
                  'window_events': d.evidence.get('window_events'),
                  'runs': d.evidence.get('runs'), 'edits': d.evidence.get('edits'),
                  'delivery_delay': d.evidence.get('delivery_delay'),
                  'response_gap': gap, 'flags': flags}
        if flags:
            failures.append(record)
        elif gap is not None and gap < 300 and len(successes) < 400:
            successes.append(record)

    counts['held_then_dropped'] = engine.gate_stats.get('dropped', 0)
    counts['superseded'] = engine.gate_stats.get('superseded', 0)

    n = len(delivered)
    out = {
        'split': split, 'delivered_scaffolds': n, 'submissions_in_split': submissions,
        'category_definitions': CATEGORIES,
        'counts': dict(counts),
        'rates_over_delivered': {k: round(v / n, 4) for k, v in counts.items() if n},
        'failure_scaffolds': len(failures),
        'failure_rate': round(len(failures) / n, 4) if n else None,
        'representative_failures': failures[:2] + failures[len(failures) // 2:
                                                           len(failures) // 2 + 2],
        'representative_successes': successes[:2] + successes[len(successes) // 2:
                                                              len(successes) // 2 + 2],
    }
    (RESULTS / 'failure_analysis.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    with (LOGS / 'failure_cases.jsonl').open('w', encoding='utf-8') as w:
        for r in failures[:500]:
            w.write(json.dumps(r) + '\n')
    print(f'delivered {n} scaffolds; {len(failures)} carry at least one failure flag '
          f'({out["failure_rate"]})')
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f'  {k:24s} {v:6d}   {round(v / n, 4) if n else 0}')
    print(f'\nwrote {RESULTS / "failure_analysis.json"}')


if __name__ == '__main__':
    main()
