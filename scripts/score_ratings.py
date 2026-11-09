#!/usr/bin/env python
"""Score two human rating sheets and compute inter-rater agreement.

Usage:
    python -m scripts.score_ratings results/phase2/ratings_minahil.csv results/phase2/ratings_areeba.csv

Output:
  - Mean timing (0-4), mean relevance (1-4), SDs for each rater and pooled
  - Linearly weighted kappa between the two raters for each scale
  - Agreement table

Linearly weighted kappa:
    kw = 1 - (sum_ij w_ij * O_ij) / (sum_ij w_ij * E_ij)
    where w_ij = |i - j| / (K - 1)  for K categories.
"""
import argparse
import csv
import math
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))


def _load_sheet(path: pathlib.Path) -> list[dict]:
    rows = []
    with path.open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            try:
                timing = float(row['timing']) if row.get('timing', '').strip() else None
                relevance = float(row['relevance']) if row.get('relevance', '').strip() else None
            except ValueError:
                continue
            if timing is not None and relevance is not None:
                rows.append({
                    'row_id': row.get('row_id', ''),
                    'timing': timing,
                    'relevance': relevance,
                })
    return rows


def _mean_sd(vals: list[float]) -> tuple[float, float]:
    if not vals:
        return float('nan'), float('nan')
    mu = sum(vals) / len(vals)
    var = sum((v - mu) ** 2 for v in vals) / len(vals)
    return round(mu, 3), round(math.sqrt(var), 3)


def _linear_weighted_kappa(ratings_a: list[float], ratings_b: list[float],
                             min_val: float, max_val: float) -> float:
    """Compute linearly weighted Cohen's kappa."""
    n = len(ratings_a)
    if n == 0:
        return float('nan')

    categories = sorted(set(ratings_a) | set(ratings_b))
    k = len(categories)
    if k == 1:
        return 1.0

    cat_idx = {c: i for i, c in enumerate(categories)}
    n_cats = k

    # Observed agreement matrix
    O = [[0.0] * n_cats for _ in range(n_cats)]
    for a, b in zip(ratings_a, ratings_b):
        i, j = cat_idx.get(a, 0), cat_idx.get(b, 0)
        O[i][j] += 1
    for i in range(n_cats):
        for j in range(n_cats):
            O[i][j] /= n

    # Marginals
    row_sums = [sum(O[i]) for i in range(n_cats)]
    col_sums = [sum(O[i][j] for i in range(n_cats)) for j in range(n_cats)]

    # Expected agreement matrix
    E = [[row_sums[i] * col_sums[j] for j in range(n_cats)] for i in range(n_cats)]

    # Weight matrix (linear)
    max_dist = n_cats - 1
    W = [[abs(i - j) / max_dist for j in range(n_cats)] for i in range(n_cats)]

    num = sum(W[i][j] * O[i][j] for i in range(n_cats) for j in range(n_cats))
    den = sum(W[i][j] * E[i][j] for i in range(n_cats) for j in range(n_cats))

    if den == 0:
        return float('nan')
    return round(1.0 - num / den, 4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('sheet_a', help='First rater CSV path')
    parser.add_argument('sheet_b', help='Second rater CSV path')
    args = parser.parse_args()

    path_a = pathlib.Path(args.sheet_a)
    path_b = pathlib.Path(args.sheet_b)

    if not path_a.exists():
        print(f'Error: {path_a} not found', file=sys.stderr)
        sys.exit(1)
    if not path_b.exists():
        print(f'Error: {path_b} not found', file=sys.stderr)
        sys.exit(1)

    rows_a = _load_sheet(path_a)
    rows_b = _load_sheet(path_b)

    # Align by row_id
    map_a = {r['row_id']: r for r in rows_a}
    map_b = {r['row_id']: r for r in rows_b}
    common_ids = sorted(set(map_a) & set(map_b))

    if not common_ids:
        print('No matching row_ids found between the two sheets.', file=sys.stderr)
        sys.exit(1)

    timing_a   = [map_a[rid]['timing']    for rid in common_ids]
    timing_b   = [map_b[rid]['timing']    for rid in common_ids]
    relev_a    = [map_a[rid]['relevance'] for rid in common_ids]
    relev_b    = [map_b[rid]['relevance'] for rid in common_ids]

    n = len(common_ids)
    print(f'Aligned items: {n}')
    print()

    # Descriptives
    mu_ta, sd_ta = _mean_sd(timing_a)
    mu_tb, sd_tb = _mean_sd(timing_b)
    mu_ra, sd_ra = _mean_sd(relev_a)
    mu_rb, sd_rb = _mean_sd(relev_b)
    mu_tp = round((mu_ta + mu_tb) / 2, 3)
    mu_rp = round((mu_ra + mu_rb) / 2, 3)

    print(f'  Rater A  —  timing: {mu_ta} ± {sd_ta}   relevance: {mu_ra} ± {sd_ra}')
    print(f'  Rater B  —  timing: {mu_tb} ± {sd_tb}   relevance: {mu_rb} ± {sd_rb}')
    print(f'  Pooled   —  timing: {mu_tp}              relevance: {mu_rp}')
    print()

    kappa_timing   = _linear_weighted_kappa(timing_a, timing_b, 0, 4)
    kappa_relev    = _linear_weighted_kappa(relev_a,  relev_b,  1, 4)
    print(f'Linearly weighted kappa:')
    print(f'  timing:    {kappa_timing}')
    print(f'  relevance: {kappa_relev}')
    print()

    # H2 target: mean relevance >= 3.0
    print(f'H2 target (mean relevance >= 3.0 / 4.0): ',
          'MET' if mu_rp >= 3.0 else 'NOT MET',
          f'(pooled mean = {mu_rp})')


if __name__ == '__main__':
    main()

