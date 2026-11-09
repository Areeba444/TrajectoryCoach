#!/usr/bin/env python
"""Generate figures from results/phase2/ data.

Uses matplotlib if available; falls back to ASCII text summaries.

Usage:
    python -m scripts.make_figures
"""
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DIR = _ROOT / 'results' / 'phase2'
FIGURES_DIR = _ROOT / 'figures'

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def _load(filename):
    p = RESULTS_DIR / filename
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return None


def _bar_chart(labels, values, title, xlabel, ylabel, filename):
    """Save a bar chart to figures/. Requires matplotlib."""
    if not HAS_MATPLOTLIB:
        print(f'  [skip] {filename}: matplotlib not installed')
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(labels, values, color='steelblue', edgecolor='white')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticklabels(labels, rotation=25, ha='right', fontsize=8)
    plt.tight_layout()
    out = FIGURES_DIR / filename
    fig.savefig(str(out), dpi=150)
    plt.close(fig)
    print(f'  Saved: {out}')


def _scatter(xs, ys, xlabel, ylabel, title, filename):
    if not HAS_MATPLOTLIB:
        print(f'  [skip] {filename}: matplotlib not installed')
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(xs, ys, alpha=0.5, s=20, color='steelblue')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    plt.tight_layout()
    out = FIGURES_DIR / filename
    fig.savefig(str(out), dpi=150)
    plt.close(fig)
    print(f'  Saved: {out}')


def fig2_tradeoff(exp):
    """Fig 2 — Interruption vs coverage scatter for ablations."""
    if not exp or not exp.get('e5_ablations'):
        print('  [skip] fig2: no ablation data')
        return
    ablations = exp['e5_ablations']
    names  = [a['name'] for a in ablations]
    intrs  = [a.get('interruption_rate', 0) for a in ablations]
    covs   = [a.get('coverage', 0) for a in ablations]
    if HAS_MATPLOTLIB:
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(covs, intrs, s=80, color='steelblue', zorder=3)
        for n, x, y in zip(names, covs, intrs):
            ax.annotate(n, (x, y), textcoords='offset points', xytext=(4, 4), fontsize=7)
        ax.set_xlabel('Coverage (delivered / triggered)')
        ax.set_ylabel('Interruption rate')
        ax.set_title('Fig 2 — Interruption vs Coverage (ablation variants)')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        out = FIGURES_DIR / 'fig2_tradeoff.png'
        fig.savefig(str(out), dpi=150)
        plt.close(fig)
        print(f'  Saved: {out}')
    else:
        print('  Fig 2 (text summary):')
        for n, i, c in zip(names, intrs, covs):
            print(f'    {n:<25} interruption={i:.4f}  coverage={c:.4f}')


def fig3_ablation_bars(exp):
    """Fig 3 — Ablation bar chart for interruption rate."""
    if not exp or not exp.get('e5_ablations'):
        return
    ablations = exp['e5_ablations']
    labels = [a['name'] for a in ablations]
    intrs  = [a.get('interruption_rate', 0) for a in ablations]
    _bar_chart(labels, intrs,
               'Fig 3 — Interruption Rate by Ablation Variant',
               'Variant', 'Interruption Rate', 'fig3_ablation.png')


def fig4_transfer(transfer):
    """Fig 4 — Transfer Spearman r by condition."""
    if not transfer or not transfer.get('sensitivity'):
        return
    sens = transfer['sensitivity']
    xs = [s['n_tasks'] for s in sens]
    ys = [s['spearman_r'] for s in sens]
    if HAS_MATPLOTLIB:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(xs, ys, marker='o', color='steelblue')
        ax.set_xlabel('Number of transfer tasks')
        ax.set_ylabel('Spearman r (transfer ~ latent skill)')
        ax.set_title('Fig 4 — Transfer instrument sensitivity')
        ax.axhline(0.70, color='red', linestyle='--', alpha=0.7, label='Target r=0.70')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        out = FIGURES_DIR / 'fig4_transfer.png'
        fig.savefig(str(out), dpi=150)
        plt.close(fig)
        print(f'  Saved: {out}')
    else:
        print('  Fig 4 (sensitivity):')
        for s in sens:
            bar = '#' * int(s['spearman_r'] * 30)
            print(f'    n_tasks={s["n_tasks"]}: r={s["spearman_r"]:.4f} {bar}')


def fig5_failures(failures):
    """Fig 5 — Failure category distribution."""
    if not failures or not failures.get('failure_types'):
        return
    types = failures['failure_types']
    labels = [v['label'][:25] for v in types.values()]
    shares = [v['share'] for v in types.values()]
    _bar_chart(labels, shares,
               'Fig 5 — Failure Type Distribution',
               'Category', 'Share of Junctures', 'fig5_failures.png')


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    print(f'Generating figures → {FIGURES_DIR}')
    print(f'matplotlib: {"available" if HAS_MATPLOTLIB else "NOT installed — text summaries only"}')
    print()

    exp      = _load('experiments_test.json')
    transfer = _load('e4_g3_transfer.json')
    failures = _load('failure_analysis.json')

    # Fig 1 — architecture diagram (manual / LaTeX TikZ, cannot be auto-generated)
    print('Fig 1 — architecture: create manually in LaTeX (TikZ) or Canva')

    fig2_tradeoff(exp)
    fig3_ablation_bars(exp)
    fig4_transfer(transfer)
    fig5_failures(failures)

    print('\nDone.')
    if not HAS_MATPLOTLIB:
        print('Install matplotlib to generate PNG/PDF figures: pip install matplotlib')


if __name__ == '__main__':
    main()

