"""Build a human rating sheet for the scaffolds the full system delivered.

Phase 1 specified two educator raters scoring timing appropriateness on a
0--4 scale. Educators were not available in Phase 2, so the two authors rate
a sample themselves. This gives the human relevance score that hypothesis H2
needs, and a human check on whether the moments the system picks look
reasonable.

WHY THIS IS NOT A BLIND COMPARISON BETWEEN CONDITIONS. We built one first and
it did not work, and the paper should say so. The conditions differ precisely
in how long the learner has been inactive when the scaffold arrives: the
timing gate always delivers a fixed interval into a pause, while the ungated
policy delivers immediately. That gap is also the thing a rater must see in
order to judge timing at all. In a trial sheet the gap separated the gated
and ungated conditions perfectly, so no amount of relabelling made the sheet
blind. The cross-condition comparison therefore rests on the log-derived
measures, and the human rating is reported as a single-condition quality
check on the delivered system.

    python -m scripts.make_rating_sheet
    # each rater fills in their own copy, independently, then:
    python -m scripts.score_ratings results/phase2/rating_sheet_minahil.csv \
                                    results/phase2/rating_sheet_areeba_rated.csv
"""
import argparse, bisect, csv, json, pathlib, random

from coach.dataset import iter_events

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOGS = ROOT / 'logs'
RESULTS = ROOT / 'results' / 'phase2'
SOURCE = 'E3_proposed_full'

SHORT = {'text_insert': 'edit', 'text_remove': 'edit', 'text_paste': 'paste',
         'focus_gained': 'focus-in', 'focus_lost': 'focus-out',
         'run': 'RUN', 'submit': 'SUBMIT'}

HEADER = ['id', 'timing', 'relevance', 'local_timeline', 'events_in_window',
          'runs_in_window', 'edits_in_window', 'phase', 'scaffold']

INSTRUCTIONS = [
    ['# Human rating sheet, TrajectoryCoach full system'],
    ['# Rate every row on your own. Do not discuss any row with the other rater'],
    ['# until both sheets are finished, or the agreement figure is meaningless.'],
    [''],
    ['# local_timeline reads left to right, each step showing the gap from the'],
    ['# previous action. >>> SCAFFOLD HERE <<< is where the question appeared.'],
    ['# edit, paste, RUN, SUBMIT, focus-in and focus-out are all the system sees.'],
    ['# It never sees the code, the output, or whether anything worked.'],
    [''],
    ['# timing: was this a good moment to interrupt?'],
    ['#   0 badly timed, cuts across active work   1 poorly timed   2 neutral'],
    ['#   3 well timed                             4 lands at a natural break'],
    [''],
    ['# relevance: does the question fit what the timeline actually shows?'],
    ['#   1 unrelated, or asserts something the evidence does not support'],
    ['#   2 loosely related   3 relevant   4 clearly the right question here'],
    [''],
    ['# Fill in timing and relevance only. Change nothing else.'],
    [''],
]


def _timeline(split='test'):
    times, kinds = {}, {}
    for e in iter_events(split):
        times.setdefault(e.student, []).append(e.time)
        kinds.setdefault(e.student, []).append(e.event)
    return times, kinds


def _context(times, kinds, student, at, back=6, forward=3):
    t = times.get(student) or []
    if not t:
        return ''
    i = bisect.bisect_right(t, at)
    parts, prev = [], None
    for j in range(max(0, i - back), i):
        gap = '' if prev is None else f'+{round(t[j] - prev)}s '
        parts.append(f'{gap}{SHORT.get(kinds[student][j], kinds[student][j])}')
        prev = t[j]
    if prev is not None:
        parts.append(f'+{round(at - prev)}s >>> SCAFFOLD HERE <<<')
    else:
        parts.append('>>> SCAFFOLD HERE <<<')
    prev = at
    for j in range(i, min(len(t), i + forward)):
        parts.append(f'+{round(t[j] - prev)}s {SHORT.get(kinds[student][j], kinds[student][j])}')
        prev = t[j]
    return ' | '.join(parts)


def main(items=30, seed=20261108):
    path = LOGS / f'{SOURCE}.jsonl'
    if not path.exists():
        raise SystemExit(f'missing {path}; run scripts/run_experiments.py first')
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    rng = random.Random(seed)
    rng.shuffle(records)
    times, kinds = _timeline()
    RESULTS.mkdir(parents=True, exist_ok=True)
    chosen = records[:items]
    with (RESULTS / 'rating_sheet.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        for line in INSTRUCTIONS:
            w.writerow(line)
        w.writerow(HEADER)
        for n, item in enumerate(chosen, 1):
            e = item['evidence']
            w.writerow([f'R{n:03d}', '', '',
                        _context(times, kinds, e['student'], e['time']),
                        e.get('window_events', ''), e.get('runs', ''),
                        e.get('edits', ''), item['phase'], item['prompt']])
    meta = {'source_condition': SOURCE, 'items': len(chosen), 'seed': seed,
            'design': 'single condition; see module docstring for why a blind '
                      'cross-condition sheet was abandoned'}
    (RESULTS / 'rating_meta.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(f'wrote {RESULTS / "rating_sheet.csv"} with {len(chosen)} rows')
    print('each rater saves their own copy as rating_sheet_<name>.csv and fills it in')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--items', type=int, default=30)
    main(**vars(ap.parse_args()))
