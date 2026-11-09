"""Create the fixed learner split used by every Phase 2 experiment.

Rule: learners are sorted by integer identifier; every third learner
(positions 2, 5, 8, ... counting from zero) is assigned to the test set.
The rule is fixed in advance and uses no outcome, so it cannot be tuned.
The test learners are never used for threshold choice or prompt design.
"""
import csv, gzip, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main(source=ROOT / 'data' / 'zenodo_24_students.csv.gz',
         out=ROOT / 'data' / 'splits.json'):
    counts = {}
    with gzip.open(source, 'rt', encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            counts[row['student']] = counts.get(row['student'], 0) + 1
    learners = sorted(counts, key=int)
    test = [s for i, s in enumerate(learners) if i % 3 == 2]
    dev = [s for s in learners if s not in set(test)]
    payload = {
        'rule': 'learners sorted by integer id; every third learner (index % 3 == 2) is test',
        'source': source.name,
        'dev': dev,
        'test': test,
        'dev_events': sum(counts[s] for s in dev),
        'test_events': sum(counts[s] for s in test),
        'total_events': sum(counts.values()),
        'events_per_learner': {s: counts[s] for s in learners},
        'note': ('Phase 1 reported replay over all 24 learners. Phase 2 reports headline '
                 'numbers on the test learners only. The dev learners are used for every '
                 'design decision, threshold and prompt.'),
    }
    out.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in payload.items() if k != 'events_per_learner'}, indent=2))


if __name__ == '__main__':
    main(*[pathlib.Path(a) for a in sys.argv[1:]])
