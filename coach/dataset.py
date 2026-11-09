"""Loading the IDE log and the fixed learner split."""
import csv, gzip, json, pathlib
from .core import Event

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / 'data' / 'zenodo_24_students.csv.gz'
DEFAULT_SPLITS = ROOT / 'data' / 'splits.json'


def load_splits(path=DEFAULT_SPLITS):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))


def learners_for(split, path=DEFAULT_SPLITS):
    if split == 'all':
        s = load_splits(path)
        return set(s['dev']) | set(s['test'])
    s = load_splits(path)
    if split not in ('dev', 'test'):
        raise ValueError('split must be dev, test or all')
    return set(s[split])


def iter_events(split='test', source=DEFAULT_SOURCE, splits_path=DEFAULT_SPLITS):
    """Yield Event objects for the learners in one split, in source order."""
    keep = learners_for(split, splits_path)
    opener = gzip.open if str(source).endswith('.gz') else open
    with opener(source, 'rt', encoding='utf-8', newline='') as f:
        for rownum, row in enumerate(csv.DictReader(f), 2):
            if str(row['student']) in keep:
                yield Event.from_row(row, rownum)


def group_by_learner_exercise(events):
    """Group events into (student, part, exercise) units, preserving order.

    This unit matches the 'per student per question' rate reported by the
    base paper, which the on-demand comparator samples from.
    """
    groups = {}
    for e in events:
        groups.setdefault((e.student, e.part, e.exercise), []).append(e)
    return groups
