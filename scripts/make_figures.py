"""Build every figure in the paper from the saved results files.

No number is typed in here. If a results file changes, rerun this script and
the figures follow.
"""
import json, pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results' / 'phase2'
FIGS = ROOT / 'figures'

INK = '#1a1a1a'
MUTED = '#6b7280'
BLUE = '#2563eb'
AMBER = '#b45309'
TEAL = '#0f766e'
ROSE = '#b91c1c'
GREY = '#9ca3af'

plt.rcParams.update({'font.size': 9, 'axes.edgecolor': INK, 'axes.labelcolor': INK,
                     'text.color': INK, 'xtick.color': INK, 'ytick.color': INK,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'figure.facecolor': 'white', 'savefig.facecolor': 'white',
                     'font.family': 'DejaVu Sans'})


def load(name):
    return json.loads((RESULTS / name).read_text(encoding='utf-8'))


def _val(run, field):
    return run.get(field + '_mean', run.get('timing', {}).get(field))


# ---------------------------------------------------------------- figure 1
def architecture():
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.set_xlim(0, 112); ax.set_ylim(-4, 50); ax.axis('off')
    W, H = 20, 17

    def box(x, y, title, lines, colour, fill='white'):
        ax.add_patch(FancyBboxPatch((x, y), W, H, boxstyle='round,pad=0.5',
                                    linewidth=1.3, edgecolor=colour, facecolor=fill))
        ax.text(x + W / 2, y + H - 3.2, title, ha='center', va='center',
                fontsize=8.3, fontweight='bold', color=colour)
        for i, line in enumerate(lines):
            ax.text(x + W / 2, y + H - 7.4 - i * 3.5, line, ha='center', va='center',
                    fontsize=6.6, color=MUTED)

    def harrow(x1, x2, y, label, colour=GREY):
        ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle='-|>',
                                     mutation_scale=9, linewidth=1.0, color=colour))
        ax.text((x1 + x2) / 2, y + 1.6, label, ha='center', fontsize=6.2, color=MUTED)

    def varrow(x, y1, y2, colour=GREY, label='', side=1):
        ax.add_patch(FancyArrowPatch((x, y1), (x, y2), arrowstyle='-|>',
                                     mutation_scale=9, linewidth=1.0, color=colour))
        if label:
            ax.text(x + 1.4 * side, (y1 + y2) / 2, label, ha='left' if side > 0 else 'right',
                    va='center', fontsize=6.2, color=colour)

    cols = [1, 30, 59, 88]
    top, bot = 29, 5
    box(cols[0], top, 'Environment', ['learner file on disk',
                                      'edit / run / submit', 'code never leaves'], INK)
    box(cols[1], top, 'Trajectory state', ['300 s sliding window',
                                           'counts, session, episode',
                                           'intervention memory'], TEAL)
    box(cols[2], top, 'Policy', ['plan / monitor /', 'evaluate / wait',
                                 'budget + cooldown'], BLUE)
    box(cols[3], top, 'Timing gate  G1', ['hold if mid-burst',
                                          'release after 20 s pause',
                                          'drop after horizon'], AMBER, '#fffbeb')
    box(cols[1], bot, 'Read-only tools', ['trajectory summary',
                                          'prior interventions',
                                          'reflection, evidence row'], TEAL)
    box(cols[2], bot, 'Evidence floor  G2', ['refuse below 5 events',
                                             'schema + validator',
                                             'no outcome or affect'], AMBER, '#fffbeb')
    box(cols[3], bot, 'Scaffold out', ['one question',
                                       'reason + evidence row',
                                       'deterministic fallback'], INK)

    mid = top + H / 2
    for i in range(3):
        harrow(cols[i] + W, cols[i + 1], mid, ['events', 'window', 'candidate'][i])
    varrow(cols[1] + W / 2, top, bot + H, TEAL)
    varrow(cols[2] + W / 2, bot + H, top, AMBER, 'veto', side=1)
    harrow(cols[1] + W, cols[2], bot + H / 2, 'facts', TEAL)
    harrow(cols[2] + W, cols[3], bot + H / 2, 'checked', AMBER)
    varrow(cols[3] + W / 2, top, bot + H, AMBER)

    ax.add_patch(FancyArrowPatch((cols[3] + W / 2, bot), (cols[0] + W / 2, bot - 3),
                                 arrowstyle='-|>', mutation_scale=9, linewidth=1.0,
                                 color=GREY, connectionstyle='angle,angleA=-90,angleB=0,rad=3'))
    ax.text(cols[1], bot - 2.4, 'shown to the learner', ha='left', fontsize=6.3, color=MUTED)
    ax.text(56, 48.5, 'G3, the delayed no-AI transfer instrument, is validated '
                      'separately and sits outside this loop',
            ha='center', fontsize=6.8, color=MUTED, style='italic')
    fig.tight_layout()
    fig.savefig(FIGS / 'fig1_architecture.pdf', bbox_inches='tight')
    fig.savefig(FIGS / 'fig1_architecture.png', dpi=220, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- figure 2
def tradeoff():
    d = load('experiments_test.json')['runs']
    want = [('E1_baseline_rule', 'E1 rule baseline', GREY, 'o'),
            ('E2_base_paper_pause', 'E2 on-demand (pause)', AMBER, 's'),
            ('E2_base_paper_stuck', 'E2 on-demand (stuck)', AMBER, 'v'),
            ('E2_base_paper_uniform', 'E2 on-demand (uniform)', AMBER, '^'),
            ('E5_ablation_no_timing_gate', 'no timing gate', ROSE, 'D'),
            ('E5_ablation_no_evidence_floor', 'no evidence floor', ROSE, 'P'),
            ('E3_proposed_full', 'E3 proposed system', BLUE, '*')]
    fig, ax = plt.subplots(figsize=(3.5, 2.9))
    for key, label, colour, marker in want:
        run = d.get(key)
        if not run:
            continue
        x, y = _val(run, 'interruption_rate'), _val(run, 'juncture_coverage')
        if x is None or y is None:
            continue
        size = 190 if marker == '*' else 48
        ax.scatter(x, y, s=size, c=colour, marker=marker, zorder=3,
                   edgecolors='white', linewidths=0.7, label=label)
    ax.set_xlabel('interruption rate  (lower is better)')
    ax.set_ylabel('decision-point coverage')
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.legend(fontsize=6.2, frameon=False, loc='upper left', handletextpad=0.3)
    fig.tight_layout()
    fig.savefig(FIGS / 'fig2_tradeoff.pdf', bbox_inches='tight')
    fig.savefig(FIGS / 'fig2_tradeoff.png', dpi=220, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- figure 3
def ablation():
    d = load('experiments_test.json')['runs']
    rows = [('full system', 'E3_proposed_full'),
            ('- cooldown', 'E5_ablation_no_cooldown'),
            ('- episode budget', 'E5_ablation_no_budget'),
            ('- response wait', 'E5_ablation_no_memory'),
            ('- evidence floor', 'E5_ablation_no_evidence_floor'),
            ('- timing gate', 'E5_ablation_no_timing_gate'),
            ('Phase 1 policy', 'E5_ablation_none_phase1')]
    labels, vals, cols = [], [], []
    for label, key in rows:
        run = d.get(key)
        if not run:
            continue
        labels.append(label)
        vals.append(_val(run, 'interruption_rate'))
        cols.append(BLUE if key == 'E3_proposed_full' else GREY)
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    ax.barh(range(len(vals)), vals, color=cols, height=0.62)
    ax.set_yticks(range(len(vals))); ax.set_yticklabels(labels, fontsize=7.4)
    ax.invert_yaxis()
    ax.set_xlabel('interruption rate on the test split')
    for i, v in enumerate(vals):
        ax.text(v + 0.012, i, f'{v:.3f}', va='center', fontsize=6.8, color=INK)
    ax.set_xlim(0, max(vals) * 1.22)
    ax.grid(axis='x', alpha=0.25, linewidth=0.6)
    fig.tight_layout()
    fig.savefig(FIGS / 'fig3_ablation.pdf', bbox_inches='tight')
    fig.savefig(FIGS / 'fig3_ablation.png', dpi=220, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- figure 4
def transfer():
    d = load('e4_g3_transfer.json')
    s = d['sensitivity_transfer_task_count']
    ns = sorted(s, key=int)
    means = [s[n]['transfer_vs_skill_mean'] for n in ns]
    sds = [s[n]['transfer_vs_skill_sd'] for n in ns]
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.errorbar([int(n) for n in ns], means, yerr=sds, marker='o', color=BLUE,
                capsize=3, linewidth=1.3, markersize=4.5)
    ax.axhline(d['target_transfer_correlation'], color=AMBER, linestyle='--',
               linewidth=1.0)
    ax.text(float(ns[-1]), d['target_transfer_correlation'] + 0.012,
            'Phase 1 target 0.70', ha='right', fontsize=6.6, color=AMBER)
    ax.set_xlabel('transfer tasks in the rubric')
    ax.set_ylabel('Spearman r with latent skill')
    ax.set_xticks([int(n) for n in ns])
    ax.grid(alpha=0.25, linewidth=0.6)
    fig.tight_layout()
    fig.savefig(FIGS / 'fig4_transfer.pdf', bbox_inches='tight')
    fig.savefig(FIGS / 'fig4_transfer.png', dpi=220, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- figure 5
def failures():
    d = load('failure_analysis.json')
    counts = d['counts']
    items = sorted(counts.items(), key=lambda kv: -kv[1])
    labels = [k.replace('_', ' ') for k, _ in items]
    vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    ax.barh(range(len(vals)), vals, color=ROSE, height=0.6, alpha=0.85)
    ax.set_yticks(range(len(vals))); ax.set_yticklabels(labels, fontsize=7.2)
    ax.invert_yaxis()
    ax.set_xlabel(f'cases among {d["delivered_scaffolds"]} delivered scaffolds')
    for i, v in enumerate(vals):
        ax.text(v + max(vals) * 0.015, i, str(v), va='center', fontsize=6.8)
    ax.set_xlim(0, max(vals) * 1.2)
    ax.grid(axis='x', alpha=0.25, linewidth=0.6)
    fig.tight_layout()
    fig.savefig(FIGS / 'fig5_failures.pdf', bbox_inches='tight')
    fig.savefig(FIGS / 'fig5_failures.png', dpi=220, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    FIGS.mkdir(exist_ok=True)
    architecture()
    for name, fn in (('tradeoff', tradeoff), ('ablation', ablation),
                     ('transfer', transfer), ('failures', failures)):
        try:
            fn()
        except FileNotFoundError as exc:
            print(f'skipped {name}: {exc}')
    print('figures written to', FIGS)
    for p in sorted(FIGS.glob('*')):
        print('  ', p.name)
