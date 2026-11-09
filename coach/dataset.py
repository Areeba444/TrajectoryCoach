"""Fixed dev/test split loader. No learning outcome is available.

Split rule (fixed before any experiment): every third learner by sorted
integer id (index % 3 == 2) goes to test.  This rule uses no outcome, so
it cannot be tuned.  Test learners were never used for threshold, prompt or
design decisions.
"""
import csv, gzip, pathlib
from .core import Event

# Fixed split rule — do not change without supervisor approval.
_ALL_IDS = list(range(24))                      # learners 0..23
TEST_IDS  = {str(i) for i in _ALL_IDS if _ALL_IDS.index(i) % 3 == 2}
DEV_IDS   = {str(i) for i in _ALL_IDS if _ALL_IDS.index(i) % 3 != 2}

_DATA_DEFAULT = pathlib.Path(__file__).resolve().parents[1] / 'data' / 'zenodo_24_students.csv.gz'


def learner_ids(split: str) -> list[str]:
    """Return sorted string ids for 'dev' or 'test'."""
    if split == 'test':
        return sorted(TEST_IDS, key=int)
    if split == 'dev':
        return sorted(DEV_IDS, key=int)
    raise ValueError(f'Unknown split: {split!r}. Use "dev" or "test".')


def load_split(gz_path: str | None = None, split: str = 'test') -> list[Event]:
    """Return events for the requested split in chronological source order.

    Events are sorted by student then timestamp (matching the preprocessing
    step in extract_subset.py).  No course outcomes are included.
    """
    path = pathlib.Path(gz_path) if gz_path else _DATA_DEFAULT
    ids  = set(learner_ids(split))
    events: list[Event] = []
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8', newline='') as f:
        for rownum, row in enumerate(csv.DictReader(f), 2):
            if str(row['student']) not in ids:
                continue
            try:
                events.append(Event.from_row(row, rownum))
            except (ValueError, KeyError):
                continue   # skip malformed rows; count is not checked here
    return events


def split_info() -> dict:
    """Return a dict describing the split rule and learner counts."""
    return {
        'rule'       : 'index % 3 == 2 → test',
        'dev_ids'    : sorted(DEV_IDS,  key=int),
        'test_ids'   : sorted(TEST_IDS, key=int),
        'n_dev'      : len(DEV_IDS),
        'n_test'     : len(TEST_IDS),
        'note'       : 'Rule uses no outcome; test set never used for design decisions.',
    }

