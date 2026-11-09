#!/usr/bin/env python
"""Generate data/splits.json with the fixed dev/test split rule.

Idempotent: safe to run multiple times; always produces the same output.
"""
import json
import pathlib
import sys

# Ensure project root is on path
_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from coach.dataset import learner_ids

OUTPUT = _ROOT / 'data' / 'splits.json'


def main():
    dev = learner_ids('dev')
    test = learner_ids('test')
    splits = {
        'rule': 'index % 3 == 2',
        'dev': dev,
        'test': test,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(splits, indent=2) + '\n', encoding='utf-8')
    print(f'Written {OUTPUT}')
    print(f'  dev  ({len(dev)} learners): {dev}')
    print(f'  test ({len(test)} learners): {test}')


if __name__ == '__main__':
    main()

