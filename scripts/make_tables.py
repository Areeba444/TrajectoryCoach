#!/usr/bin/env python
"""Generate LaTeX tables from results/phase2/ data.

Reads experiment results and prints table data in LaTeX format.
Full LaTeX generation to be refined in a later iteration.
"""
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DIR = _ROOT / 'results' / 'phase2'


def _load(filename):
    p = RESULTS_DIR / filename
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return None


def _float(v, decimals=3):
    if isinstance(v, float):
        return f'{v:.{decimals}f}'
    return str(v)


def main():
    print('Generating LaTeX tables from results/phase2/ ...')

    exp = _load('experiments_test.json')
    transfer = _load('e4_g3_transfer.json')
    failures = _load('failure_analysis.json')

    if exp and exp.get('e5_ablations'):
        print('\n% Table 1: Ablation study results')
        print(r'\begin{table}[h]')
        print(r'\begin{tabular}{lrrrr}')
        print(r'\hline')
        print(r'Variant & Scaffolds & Pause-aligned & Coverage & Delib. delta \\')
        print(r'\hline')
        for a in exp['e5_ablations']:
            print(f'{a["name"]} & {a["scaffold_count"]} & '
                  f'{_float(a["pause_aligned_rate"])} & '
                  f'{_float(a["coverage"])} & '
                  f'{_float(a["deliberation_delta"])} \\\\')
        print(r'\hline')
        print(r'\end{tabular}')
        print(r'\caption{Ablation study: Phase 2 system variants on test split.}')
        print(r'\end{table}')

    if exp and exp.get('e2_on_demand'):
        print('\n% Table 2: On-demand baselines (E2)')
        print(r'\begin{table}[h]')
        print(r'\begin{tabular}{llrr}')
        print(r'\hline')
        print(r'Model & Seed & Requests & Pause-aligned \\')
        print(r'\hline')
        for b in exp['e2_on_demand']:
            print(f'{b.get("model", "?")} & {b.get("seed", "?")} & '
                  f'{b.get("total_requests", 0)} & '
                  f'{_float(b.get("pause_aligned_rate", 0.0))} \\\\')
        print(r'\hline')
        print(r'\end{tabular}')
        print(r'\caption{On-demand baselines (AIMS comparator).}')
        print(r'\end{table}')

    if transfer and transfer.get('conditions'):
        print('\n% Table 3: G3 transfer study results')
        print(r'\begin{table}[h]')
        print(r'\begin{tabular}{lrr}')
        print(r'\hline')
        print(r'Condition & Mean transfer $\rho$ & Mean assisted $\rho$ \\')
        print(r'\hline')
        for c in transfer['conditions']:
            print(f'{c["condition"]} & '
                  f'{_float(c["mean_transfer_r"])} & '
                  f'{_float(c["mean_assisted_r"])} \\\\')
        print(r'\hline')
        print(r'\end{tabular}')
        print(r'\caption{G3 simulated learner transfer study.}')
        print(r'\end{table}')

    if failures and failures.get('failure_types'):
        print('\n% Table 4: Failure type analysis')
        print(r'\begin{table}[h]')
        print(r'\begin{tabular}{llrr}')
        print(r'\hline')
        print(r'Type & Label & Count & Share \\')
        print(r'\hline')
        for ftype, fdata in failures['failure_types'].items():
            print(f'{ftype} & {fdata["label"][:40]} & '
                  f'{fdata["count"]} & '
                  f'{_float(fdata["share"])} \\\\')
        print(r'\hline')
        print(r'\end{tabular}')
        print(r'\caption{Failure type analysis for full system on test split.}')
        print(r'\end{table}')

    print('\nTables printed. Copy into LaTeX document as needed.')


if __name__ == '__main__':
    main()

