#!/usr/bin/env python
"""Generate a human rating sheet for the 30-item reliability sample.

Writes results/phase2/rating_sheet.csv with columns:
  row_id, student, part, exercise, source_row, phase, prompt,
  timing (blank – rater fills 0-4), relevance (blank – rater fills 1-4)

Usage:
    python -m scripts.make_rating_sheet
    python -m scripts.make_rating_sheet --n 30 --seed 42
"""
import argparse
import csv
import json
import pathlib
import random
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

OUTPUT_DIR = _ROOT / 'results' / 'phase2'
OUTPUT = OUTPUT_DIR / 'rating_sheet.csv'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=30, help='Number of items to sample')
    parser.add_argument('--seed', type=int, default=0, help='Random seed')
    parser.add_argument('--results', default=str(_ROOT / 'results' / 'phase2' / 'experiments_test.json'))
    args = parser.parse_args()

    results_path = pathlib.Path(args.results)
    if not results_path.exists():
        print(f'Error: results file not found: {results_path}')
        print('Run python -m scripts.run_experiments --split test first.')
        sys.exit(1)

    results = json.loads(results_path.read_text(encoding='utf-8'))

    # Collect all non-wait decisions from E3 (full system)
    e3 = results.get('e3_full_system', {})
    # We need to re-run to get actual decision texts – load from decisions.jsonl if present
    decisions_file = _ROOT / 'results' / 'phase2' / 'decisions.jsonl'

    items = []
    if decisions_file.exists():
        with decisions_file.open(encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    if d.get('phase', 'wait') != 'wait' and d.get('prompt', '').strip():
                        items.append(d)
                except json.JSONDecodeError:
                    continue
    else:
        # Fallback: generate placeholder items from experiment metadata
        print('Warning: decisions.jsonl not found; generating placeholder rating sheet.')
        for i in range(args.n):
            items.append({
                'phase': 'monitor',
                'prompt': f'[Placeholder item {i+1}] What hypothesis are you checking?',
                'evidence': {
                    'student': 'unknown', 'part': '1', 'exercise': str(i),
                    'source_row': i, 'time': float(i * 100),
                },
                'reason': 'Placeholder',
            })

    # Sample args.n items
    rng = random.Random(args.seed)
    if len(items) > args.n:
        sample = rng.sample(items, args.n)
    else:
        sample = items

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'row_id', 'student', 'part', 'exercise', 'source_row',
            'phase', 'prompt', 'timing', 'relevance',
        ])
        writer.writeheader()
        for i, d in enumerate(sample, 1):
            ev = d.get('evidence', {})
            writer.writerow({
                'row_id': i,
                'student': ev.get('student', ''),
                'part': ev.get('part', ''),
                'exercise': ev.get('exercise', ''),
                'source_row': ev.get('source_row', ''),
                'phase': d.get('phase', ''),
                'prompt': d.get('prompt', ''),
                'timing': '',    # rater fills: 0 = interrupts, 4 = well-timed
                'relevance': '', # rater fills: 1 = not relevant, 4 = highly relevant
            })

    print(f'Rating sheet written to {OUTPUT}')
    print(f'  Items: {len(sample)}')
    print()
    print('Instructions:')
    print('  Copy this file to rating_sheet_<yourname>.csv')
    print('  Fill in timing (0-4) and relevance (1-4) columns independently')
    print('  Do not discuss ratings until both raters are finished')
    print('  Timing 0 = interrupts active work, 4 = perfectly timed pause')
    print('  Relevance 1 = unrelated, 4 = directly relevant to observable behaviour')


if __name__ == '__main__':
    main()

