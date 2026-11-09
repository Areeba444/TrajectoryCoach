#!/usr/bin/env python
"""Run G3 transfer study: 3 conditions × 5 seeds + sensitivity analysis.

Saves results to results/phase2/e4_g3_transfer.json.
"""
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from coach.simulator import run_transfer_study, sensitivity_analysis

OUTPUT_DIR = _ROOT / 'results' / 'phase2'
OUTPUT = OUTPUT_DIR / 'e4_g3_transfer.json'

CONDITIONS = ('unassisted', 'on_demand', 'trajectory')
SEEDS = [0, 1, 2, 3, 4]


def main():
    print('Running G3 transfer study ...')
    results = {
        'conditions': [],
        'sensitivity': [],
    }

    for condition in CONDITIONS:
        condition_results = []
        for seed in SEEDS:
            print(f'  condition={condition}, seed={seed} ...')
            r = run_transfer_study(condition=condition, seed=seed)
            # Remove large arrays from individual results to keep JSON manageable
            r_summary = {k: v for k, v in r.items()
                        if k not in ('transfer_scores', 'latent_skills')}
            condition_results.append(r_summary)
        results['conditions'].append({
            'condition': condition,
            'runs': condition_results,
            'mean_transfer_r': round(
                sum(r['transfer_spearman_r'] for r in condition_results) / len(condition_results), 4
            ),
            'mean_assisted_r': round(
                sum(r['assisted_completion_r'] for r in condition_results) / len(condition_results), 4
            ),
        })
        print(f'  {condition}: mean transfer_r = {results["conditions"][-1]["mean_transfer_r"]}')

    print('Running sensitivity analysis ...')
    sens = sensitivity_analysis(n_tasks_range=[2, 4, 6, 8], seed=0)
    results['sensitivity'] = sens
    print('  Sensitivity:', sens)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f'\nResults saved to {OUTPUT}')


if __name__ == '__main__':
    main()

