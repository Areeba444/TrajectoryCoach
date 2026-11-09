"""E4-G3: does the delayed, no-AI transfer rubric measure internalised skill?

Phase 1 proposed a seven-day delayed transfer task scored with a rubric, and a
human classroom study. The human study is out of scope for Phase 2, so this
validates the instrument on parametrised simulated learners instead. It is a
measurement check, not evidence that coaching improves human learning, and
nothing here should be read as a learning outcome.

The question: after an assisted session, does the transfer score rank learners
by their internalised skill more faithfully than assisted completion does?
"""
import argparse, json, pathlib, statistics

from coach.simulator import run_study, CONDITIONS
from coach.stats import spearman, bootstrap_ci, mean_sd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results' / 'phase2'
SEEDS = (0, 1, 2, 3, 4)
TARGET = 0.70   # the Phase 1 pre-registered target for the transfer correlation


def one_run(condition, seed, n, transfer_tasks):
    rows = run_study(n_learners=n, condition=condition, seed=seed,
                     transfer_difficulties=transfer_tasks)
    skill = [r['latent_skill_after'] for r in rows]
    transfer = [r['transfer_score'] for r in rows]
    assisted = [r['assisted_completion'] for r in rows]
    reliance = [r['reliance'] for r in rows]
    # Within skill terciles, does assisted completion still track reliance?
    order = sorted(range(len(rows)), key=lambda i: skill[i])
    third = max(1, len(order) // 3)
    within = []
    for start in range(0, len(order), third):
        block = order[start:start + third]
        if len(block) >= 8:
            v = spearman([assisted[i] for i in block], [reliance[i] for i in block])
            if v is not None:
                within.append(v)
    return {
        'condition': condition, 'seed': seed, 'learners': len(rows),
        'transfer_vs_skill': spearman(transfer, skill),
        'assisted_vs_skill': spearman(assisted, skill),
        'assisted_vs_reliance_within_skill': statistics.fmean(within) if within else None,
        'mean_transfer_score': statistics.fmean(transfer),
        'mean_assisted_completion': statistics.fmean(assisted),
        'mean_skill_gain': statistics.fmean([r['skill_gain'] for r in rows]),
    }


def main(learners=120, conditions=CONDITIONS, seeds=SEEDS):
    RESULTS.mkdir(parents=True, exist_ok=True)
    tasks = (0.35, 0.5, 0.65, 0.8)
    out = {'learners_per_run': learners, 'seeds': list(seeds),
           'target_transfer_correlation': TARGET,
           'note': ('Simulated learners only. This validates the transfer instrument; '
                    'it is not evidence about human learning.'),
           'by_condition': {}, 'sensitivity_transfer_task_count': {}}

    for condition in conditions:
        runs = [one_run(condition, s, learners, tasks) for s in seeds]
        agg = {'runs': runs}
        for field in ('transfer_vs_skill', 'assisted_vs_skill',
                      'assisted_vs_reliance_within_skill', 'mean_transfer_score',
                      'mean_assisted_completion', 'mean_skill_gain'):
            m, sd = mean_sd([r[field] for r in runs])
            agg[field + '_mean'] = round(m, 4) if m is not None else None
            agg[field + '_sd'] = round(sd, 4) if sd is not None else None
        pooled = run_study(n_learners=learners * 4, condition=condition, seed=99,
                           transfer_difficulties=tasks)
        t = [r['transfer_score'] for r in pooled]
        k = [r['latent_skill_after'] for r in pooled]
        a = [r['assisted_completion'] for r in pooled]
        lo, hi = bootstrap_ci(t, k)
        alo, ahi = bootstrap_ci(a, k)
        agg['pooled_transfer_vs_skill'] = round(spearman(t, k), 4)
        agg['pooled_transfer_ci'] = [round(lo, 4), round(hi, 4)]
        agg['pooled_assisted_vs_skill'] = round(spearman(a, k), 4)
        agg['pooled_assisted_ci'] = [round(alo, 4), round(ahi, 4)]
        agg['meets_target'] = agg['transfer_vs_skill_mean'] >= TARGET
        out['by_condition'][condition] = agg

    for n_tasks in (2, 4, 6, 8):
        diffs = tuple(0.3 + 0.5 * i / max(1, n_tasks - 1) for i in range(n_tasks))
        runs = [one_run('trajectory', s, learners, diffs) for s in seeds]
        m, sd = mean_sd([r['transfer_vs_skill'] for r in runs])
        out['sensitivity_transfer_task_count'][str(n_tasks)] = {
            'transfer_vs_skill_mean': round(m, 4), 'transfer_vs_skill_sd': round(sd, 4)}

    (RESULTS / 'e4_g3_transfer.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('--- G3 transfer instrument (simulated learners) ---')
    for c, a in out['by_condition'].items():
        print(f"{c:12s} transfer~skill {a['transfer_vs_skill_mean']:.3f} "
              f"(sd {a['transfer_vs_skill_sd']:.3f}, pooled CI {a['pooled_transfer_ci']})   "
              f"assisted~skill {a['assisted_vs_skill_mean']:.3f}   "
              f"target met: {a['meets_target']}")
    print('\ntransfer tasks needed:')
    for n, v in out['sensitivity_transfer_task_count'].items():
        print(f"  {n:>2s} tasks  r = {v['transfer_vs_skill_mean']:.3f} "
              f"(sd {v['transfer_vs_skill_sd']:.3f})")
    print(f"\nwrote {RESULTS / 'e4_g3_transfer.json'}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--learners', type=int, default=120)
    main(**vars(ap.parse_args()))
