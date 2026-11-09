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

from coach.core import TrajectoryCoach
from coach.dataset import load_split

OUTPUT_DIR = _ROOT / 'results' / 'phase2'
OUTPUT = OUTPUT_DIR / 'rating_sheet.csv'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=30, help='Number of items to sample')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    print('Extracting real delivered scaffolds from full system (E3) on test split...')
    coach = TrajectoryCoach(
        mode='adaptive',
        cooldown=180,
        max_prompts=3,
        use_timing_gate=True,
        use_evidence_floor=True
    )
    events = load_split(split='test')

    by_phase = {'plan': [], 'monitor': [], 'evaluate': []}
    for e in events:
        d = coach.observe(e)
        if d.phase in by_phase and d.prompt:
            by_phase[d.phase].append({
                'student': e.student,
                'part': e.part,
                'exercise': e.exercise,
                'source_row': e.source_row,
                'phase': d.phase,
                'prompt': d.prompt,
                'reason': d.reason,
            })

    print(f'Delivered scaffolds by phase: ' +
          f'plan={len(by_phase["plan"])}, ' +
          f'monitor={len(by_phase["monitor"])}, ' +
          f'evaluate={len(by_phase["evaluate"])}')

    rng = random.Random(args.seed)
    # Stratify sample evenly across available phases
    per_phase = args.n // 3
    sample = []
    for ph in ['plan', 'monitor', 'evaluate']:
        pool = by_phase[ph]
        k = min(per_phase, len(pool))
        sample.extend(rng.sample(pool, k))

    # If any remainder, sample from all remaining
    if len(sample) < args.n:
        needed = args.n - len(sample)
        remaining = [item for ph in by_phase for item in by_phase[ph] if item not in sample]
        sample.extend(rng.sample(remaining, needed))

    # Shuffle sample order
    rng.shuffle(sample)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'row_id', 'student', 'part', 'exercise', 'source_row',
            'phase', 'prompt', 'timing', 'relevance',
        ])
        writer.writeheader()
        for i, d in enumerate(sample, 1):
            writer.writerow({
                'row_id': i,
                'student': d.get('student', ''),
                'part': d.get('part', ''),
                'exercise': d.get('exercise', ''),
                'source_row': d.get('source_row', ''),
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
