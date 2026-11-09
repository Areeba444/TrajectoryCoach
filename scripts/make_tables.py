"""Generate every table in the paper and the README gap-resolution table.

Numbers come only from results/phase2/*.json, so the paper cannot drift from
the repository. Missing result files produce a visible TODO rather than a
silent blank, so an unrun experiment is obvious.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results' / 'phase2'
TABLES = ROOT / 'paper' / 'tables'
MISSING = r'\textit{not run}'


def load(name):
    p = RESULTS / name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


def num(v, places=3, dash=MISSING):
    return dash if v is None else f'{v:.{places}f}'


def pm(run, field, places=3):
    """mean +- sd for a stochastic run, or the plain value for a fixed one."""
    if run is None:
        return MISSING
    if field + '_mean' in run:
        m, s = run.get(field + '_mean'), run.get(field + '_sd')
        return MISSING if m is None else f'{m:.{places}f} $\\pm$ {s:.{places}f}'
    v = run.get(field, run.get('timing', {}).get(field))
    return num(v, places)


def write(name, body):
    (TABLES / name).write_text(body, encoding='utf-8')
    print('wrote', TABLES / name)


def table_main(exp):
    runs = exp['runs']
    order = [('E1', 'Rule baseline (uncapped)', 'E1_baseline_rule'),
             ('E2', 'Base paper, on-demand at pauses', 'E2_base_paper_pause'),
             ('E2', 'Base paper, on-demand when stuck', 'E2_base_paper_stuck'),
             ('E2', 'Base paper, on-demand uniform', 'E2_base_paper_uniform'),
             ('E3', 'Proposed system', 'E3_proposed_full')]
    rows = []
    for tag, label, key in order:
        r = runs.get(key)
        bold = key == 'E3_proposed_full'
        name = f'\\textbf{{{label}}}' if bold else label
        rows.append(' & '.join([tag, name, pm(r, 'prompts', 0),
                                pm(r, 'interruption_rate'), pm(r, 'pause_aligned'),
                                pm(r, 'juncture_coverage'),
                                pm(r, 'deliberation_delta', 4)]) + r' \\')
    return (r'''\begin{table*}[t]
\centering
\caption{Main results on the held-out test split (%d events, %d learner--question units,
%d observable decision points). On-demand rows are the mean and standard deviation over
three seeds; the other rows are deterministic. Lower is better for interruption.
No learner in the logs saw a scaffold, so the deliberation column describes the moments a
policy selects, not an effect of prompting.}
\label{tab:main}
\begin{tabular}{llrrrrr}
\toprule
 & Condition & Scaffolds & Interruption & Pause-aligned & Coverage & Deliberation $\Delta$ \\
\midrule
''' % (exp['events'], exp['learner_question_units'], exp['decision_points'])
            + '\n'.join(rows) + '\n' + r'''\bottomrule
\end{tabular}
\end{table*}
''')


def table_ablation(exp):
    runs = exp['runs']
    order = [('Full system', 'E3_proposed_full'),
             ('$-$ cooldown', 'E5_ablation_no_cooldown'),
             ('$-$ episode budget', 'E5_ablation_no_budget'),
             ('$-$ response wait', 'E5_ablation_no_memory'),
             ('$-$ evidence floor (G2)', 'E5_ablation_no_evidence_floor'),
             ('$-$ timing gate (G1)', 'E5_ablation_no_timing_gate'),
             ('Phase 1 policy, no components', 'E5_ablation_none_phase1')]
    rows = []
    for label, key in order:
        r = runs.get(key)
        rows.append(' & '.join([label, pm(r, 'prompts', 0), pm(r, 'interruption_rate'),
                                pm(r, 'pause_aligned'), pm(r, 'juncture_coverage')]) + r' \\')
    return (r'''\begin{table}[t]
\centering
\caption{Ablation on the test split. Each row removes one component from the full
system. The timing gate accounts for almost all of the reduction in interruption;
removing the response wait and removing the episode budget give identical results,
so the response wait never binds once the cooldown and the gate are active.}
\label{tab:ablation}
\begin{tabular}{lrrrr}
\toprule
Configuration & Scaffolds & Interruption & Pause-aligned & Coverage \\
\midrule
''' + '\n'.join(rows) + '\n' + r'''\bottomrule
\end{tabular}
\end{table}
''')


def table_efficiency(exp, llm):
    runs = exp['runs']
    rows = []
    for label, key in (('Rule baseline', 'E1_baseline_rule'),
                       ('Proposed system', 'E3_proposed_full')):
        r = runs.get(key, {})
        rows.append(' & '.join([
            label, f"{r.get('runtime_seconds', 0):.1f}",
            f"{r.get('events_per_second') or 0:,}".replace(',', '\\,'),
            f"{r.get('peak_memory_mb', 0):.1f}",
            f"{r.get('prompts_per_1000_events', 0):.2f}"]) + r' \\')
    det = '\n'.join(rows)
    if llm:
        e = llm['efficiency_constrained']
        u = llm['efficiency_unconstrained']
        model = llm['model'].replace('_', r'\_')
        live = (r'\midrule' + '\n'
                r'\multicolumn{5}{l}{\textit{Live model: %s, temperature %s, seed %s}} \\' % (
                    model, llm['temperature'], llm['seed']) + '\n'
                + ' & '.join(['Constrained generation', str(e['api_calls']),
                              f"{e['total_tokens']:,}".replace(',', '\\,'),
                              num(e['mean_latency_seconds'], 2),
                              num(e['rejection_rate'], 3)]) + r' \\' + '\n'
                + ' & '.join(['Unconstrained generation', str(u['api_calls']),
                              f"{u['total_tokens']:,}".replace(',', '\\,'),
                              num(u['mean_latency_seconds'], 2), '--']) + r' \\' + '\n'
                + r'\multicolumn{5}{l}{\footnotesize Columns for the live rows are: API '
                  r'calls, total tokens, mean latency (s), validator rejection rate.} \\')
    else:
        live = (r'\midrule' + '\n'
                r'\multicolumn{5}{l}{\textit{Live model runs: %s}} \\' % MISSING)
    return (r'''\begin{table}[t]
\centering
\caption{Efficiency and reliability (E6). The offline rows replay the full test split on
one CPU core with no network. Columns for those rows are: runtime (s), events per second,
peak memory (MB), scaffolds per 1000 events.}
\label{tab:efficiency}
\begin{tabular}{lrrrr}
\toprule
Condition & \multicolumn{4}{c}{measures} \\
\midrule
''' + det + '\n' + live + '\n' + r'''\bottomrule
\end{tabular}
\end{table}
''')


def table_failures(fa):
    rows = []
    for k, v in sorted(fa['counts'].items(), key=lambda kv: -kv[1]):
        rows.append(' & '.join([k.replace('_', ' '), str(v),
                                num(v / fa['delivered_scaffolds'], 3)]) + r' \\')
    return (r'''\begin{table}[t]
\centering
\caption{Failure categories over the %d scaffolds the full system delivered on the test
split. Categories are not exclusive; %d scaffolds (%s) carry at least one flag.}
\label{tab:failures}
\begin{tabular}{lrr}
\toprule
Category & Cases & Share of delivered \\
\midrule
''' % (fa['delivered_scaffolds'], fa['failure_scaffolds'], num(fa['failure_rate'], 3))
            + '\n'.join(rows) + '\n' + r'''\bottomrule
\end{tabular}
\end{table}
''')


def gap_rows(exp, g3, llm):
    runs = exp['runs']
    prop = runs.get('E3_proposed_full', {})
    base = runs.get('E2_base_paper_pause', {})
    abl = runs.get('E5_ablation_no_timing_gate', {})
    g1_ours = pm(prop, 'interruption_rate')
    g1_base = pm(base, 'interruption_rate')
    g1_verdict = 'Partially'
    if llm:
        g2_ours = num(llm['constrained']['unsupported_rate'])
        g2_base = num(llm['unconstrained']['unsupported_rate'])
        rate = llm['constrained']['unsupported_rate']
        g2_verdict = 'Fully' if rate is not None and rate <= 0.05 else 'Partially'
    else:
        g2_ours = g2_base = MISSING
        g2_verdict = 'Not'
    t = g3['by_condition']['trajectory']
    g3_ours = f"{t['transfer_vs_skill_mean']:.3f} $\\pm$ {t['transfer_vs_skill_sd']:.3f}"
    g3_base = f"{t['assisted_vs_skill_mean']:.3f}"
    g3_verdict = 'Partially'
    return [
        ('Gap 1: timing', 'Timing gate: hold a scaffold until a 20\\,s pause',
         'Interruption rate on held-out prefixes',
         f'{g1_base} (on-demand at pauses)', g1_ours, g1_verdict,
         f'Ablating the gate raises interruption to {pm(abl, "interruption_rate")}; '
         'coverage falls against the uncapped baseline'),
        ('Gap 2: grounding', 'Evidence floor, JSON schema, validator, read-only tools',
         'Share of scaffolds containing an unsupported claim',
         f'{g2_base} (unconstrained, same model)', g2_ours, g2_verdict,
         'Deterministic screen, not a semantic verifier'),
        ('Gap 3: transfer', 'Delayed no-AI transfer task and four-point rubric',
         'Spearman $r$ with latent skill, simulated learners',
         f'{g3_base} (assisted completion)', g3_ours, g3_verdict,
         'Instrument validation only; no human learners'),
    ]


def table_gaps(rows):
    body = '\n'.join(' & '.join([r[0], r[1], r[2], r[3], r[4], r[5]]) + r' \\'
                     for r in rows)
    return (r'''\begin{table*}[t]
\centering
\caption{Gap-resolution table. ``Base paper result'' is our adaptation of the base
paper's interaction policy run on our data, not a number reproduced from the published
paper, which reports neither of these measures.}
\label{tab:gaps}
\begin{tabular}{p{1.6cm}p{3.5cm}p{3.1cm}p{2.9cm}p{2.2cm}l}
\toprule
Gap & Method / component & Metric & Base paper result & Our result & Addressed? \\
\midrule
''' + body + '\n' + r'''\bottomrule
\end{tabular}
\end{table*}
''')


def readme_gaps(rows):
    head = ('| Gap | Method / component | Metric | Base paper result | Our result '
            '| Addressed? | Caveat |\n|---|---|---|---|---|---|---|\n')
    clean = lambda s: (s.replace('$\\pm$', '±').replace('\\,', ' ')
                       .replace('\\textit{not run}', '_not run_')
                       .replace('$r$', 'r').replace('\\', ''))
    return head + '\n'.join('| ' + ' | '.join(clean(c) for c in r) + ' |' for r in rows) + '\n'


def table_ratings(h):
    pr = h.get('per_rater', {})
    rows = []
    for name, v in pr.items():
        label = name.replace('ratings_', '').replace('_', ' ').title()
        rows.append(' & '.join([label, num(v['timing_mean'], 2), num(v['timing_sd'], 2),
                                num(v['relevance_mean'], 2), num(v['relevance_sd'], 2)]) + r' \\')
    rows.append(r'\midrule')
    rows.append(' & '.join(['Pooled', num(h['mean_timing'], 2), num(h['sd_timing'], 2),
                            num(h['mean_relevance'], 2), num(h['sd_relevance'], 2)]) + r' \\')
    return (r'''\begin{table}[t]
\centering
\caption{Human rating of %d scaffolds from the full system, by the two authors
independently. Linearly weighted $\kappa$ is %s for timing and %s for relevance, which
is fair rather than strong agreement. The sheet showed raters the phase and the prompt
text but not when the scaffold was delivered, so the timing column is reported for
completeness and no claim rests on it.}
\label{tab:ratings}
\begin{tabular}{lrrrr}
\toprule
Rater & Timing & SD & Relevance & SD \\
\midrule
''' % (h['rated_in_common'], num(h['timing_weighted_kappa'], 3),
       num(h['relevance_weighted_kappa'], 3))
            + '\n'.join(rows) + '\n' + r'''\bottomrule
\end{tabular}
\end{table}
''')


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    exp = load('experiments_test.json')
    g3 = load('e4_g3_transfer.json')
    fa = load('failure_analysis.json')
    llm = load('e4_g2_grounding.json')
    if exp:
        write('main.tex', table_main(exp))
        write('ablation.tex', table_ablation(exp))
        write('efficiency.tex', table_efficiency(exp, llm))
    if fa:
        write('failures.tex', table_failures(fa))
    h = load('human_ratings.json')
    if h:
        write('ratings.tex', table_ratings(h))
    if exp and g3:
        rows = gap_rows(exp, g3, llm)
        write('gaps.tex', table_gaps(rows))
        (ROOT / 'docs' / 'gap_resolution.md').write_text(readme_gaps(rows), encoding='utf-8')
        print('wrote', ROOT / 'docs' / 'gap_resolution.md')
    if not llm:
        print('\nNOTE: e4_g2_grounding.json is missing, so G2 and the live-model '
              'efficiency rows show "not run". Run scripts/run_llm_experiments.py '
              'and rerun this script.')


if __name__ == '__main__':
    main()
