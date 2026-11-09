"""Run the deterministic Phase 2 experiments (E1, E2, E3, E5, E6) and the G1 analysis.

Everything here runs offline on the fixed test split. No model calls are made,
so the numbers are reproducible on any machine with Python 3.10+.

    python -m scripts.run_experiments --split test
"""
import argparse, json, pathlib, statistics, time, tracemalloc
from coach.core import TrajectoryCoach, decision_dict
from coach.dataset import iter_events, group_by_learner_exercise, load_splits
from coach.baselines import OnDemandCoach, BASE_PAPER_RATE
from coach import timing

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results' / 'phase2'
LOGS = ROOT / 'logs'
SEEDS = (0, 1, 2)


def run_policy(mode, events, **kw):
    engine = TrajectoryCoach(mode=mode, **kw)
    delivered, phases, reasons = [], {}, {}
    tracemalloc.start()
    t0 = time.perf_counter()
    for e in events:
        d = engine.observe(e)
        phases[d.phase] = phases.get(d.phase, 0) + 1
        reasons[d.reason] = reasons.get(d.reason, 0) + 1
        if d.phase != 'wait':
            delivered.append(d)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return delivered, {'mode': mode, 'config': kw, 'gate_stats': dict(engine.gate_stats),
                       'events': len(events), 'phases': phases,
                       'reasons': reasons, 'runtime_seconds': round(elapsed, 3),
                       'events_per_second': round(len(events) / elapsed) if elapsed else None,
                       'peak_memory_mb': round(peak / 1e6, 1),
                       'prompts': len(delivered),
                       'prompts_per_1000_events': round(1000 * len(delivered) / len(events), 3)}


def run_on_demand(model, groups, seed, events_n):
    coach = OnDemandCoach(request_model=model, seed=seed)
    t0 = time.perf_counter()
    delivered = coach.run(groups)
    elapsed = time.perf_counter() - t0
    return delivered, {'mode': f'on_demand_{model}', 'seed': seed, 'events': events_n,
                       'request_rate_per_student_question': round(BASE_PAPER_RATE, 4),
                       'runtime_seconds': round(elapsed, 3), 'prompts': len(delivered),
                       'prompts_per_1000_events': round(1000 * len(delivered) / events_n, 3)}


def write_trace(name, delivered, limit=200):
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / f'{name}.jsonl').open('w', encoding='utf-8') as w:
        for d in delivered[:limit]:
            w.write(json.dumps(decision_dict(d)) + '\n')


def mean_sd(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None, None
    return (round(statistics.fmean(vals), 4),
            round(statistics.stdev(vals), 4) if len(vals) > 1 else 0.0)


def main(split='test'):
    RESULTS.mkdir(parents=True, exist_ok=True)
    print(f'loading {split} split ...', flush=True)
    events = list(iter_events(split))
    groups = group_by_learner_exercise(events)
    index = timing.TimingIndex(events)
    juncts = timing.junctures(events)
    print(f'{len(events)} events, {len(groups)} learner-question units, '
          f'{len(juncts)} decision points', flush=True)

    out = {'split': split, 'split_rule': load_splits()['rule'],
           'events': len(events), 'learner_question_units': len(groups),
           'decision_points': len(juncts), 'runs': {}}

    # E1 baseline, E3 proposed system policy, E5 ablations -- all deterministic.
    FULL = {'gate_seconds': 20, 'min_evidence': 5}
    for label, mode, kw in [('E1_baseline_rule', 'rule', {}),
                            ('E3_proposed_full', 'adaptive', FULL),
                            ('E5_ablation_no_timing_gate', 'adaptive', {'min_evidence': 5}),
                            ('E5_ablation_no_evidence_floor', 'adaptive', {'gate_seconds': 20}),
                            ('E5_ablation_no_memory', 'no_memory', FULL),
                            ('E5_ablation_no_cooldown', 'no_cooldown', FULL),
                            ('E5_ablation_no_budget', 'no_budget', FULL),
                            ('E5_ablation_none_phase1', 'adaptive', {})]:
        print(f'running {label} ...', flush=True)
        delivered, summary = run_policy(mode, events, **kw)
        summary['timing'] = timing.evaluate(delivered, index, juncts)
        out['runs'][label] = summary
        write_trace(label, delivered)

    # E2 base-paper comparator -- stochastic, so repeated with three seeds.
    for model in ('pause', 'stuck', 'uniform'):
        per_seed = []
        for seed in SEEDS:
            print(f'running E2_base_paper_{model} seed={seed} ...', flush=True)
            delivered, summary = run_on_demand(model, groups, seed, len(events))
            summary['timing'] = timing.evaluate(delivered, index, juncts, seed=seed)
            per_seed.append(summary)
            if seed == SEEDS[0]:
                write_trace(f'E2_base_paper_{model}', delivered)
        agg = {'mode': f'on_demand_{model}', 'seeds': list(SEEDS), 'per_seed': per_seed}
        for field, getter in [('prompts', lambda s: s['prompts']),
                              ('prompts_per_1000_events', lambda s: s['prompts_per_1000_events']),
                              ('interruption_rate', lambda s: s['timing']['interruption_rate']),
                              ('pause_aligned', lambda s: s['timing']['pause_aligned']),
                              ('juncture_precision', lambda s: s['timing']['juncture_precision']),
                              ('juncture_coverage', lambda s: s['timing']['juncture_coverage']),
                              ('deliberation_delta', lambda s: s['timing']['deliberation_delta'])]:
            m, sd = mean_sd([getter(s) for s in per_seed])
            agg[field + '_mean'], agg[field + '_sd'] = m, sd
        out['runs'][f'E2_base_paper_{model}'] = agg

    (RESULTS / f'experiments_{split}.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(f'\nwrote {RESULTS / f"experiments_{split}.json"}')
    for k, v in out['runs'].items():
        if 'per_seed' in v:
            print(f'{k:28s} prompts={v["prompts_mean"]:>9.1f} +/-{v["prompts_sd"]:<8.1f} '
                  f'interrupt={v["interruption_rate_mean"]} pause={v["pause_aligned_mean"]}')
        else:
            t = v['timing']
            print(f'{k:28s} prompts={v["prompts"]:>9d}            '
                  f'interrupt={round(t["interruption_rate"],4)} pause={round(t["pause_aligned"],4)} '
                  f'cover={round(t["juncture_coverage"],4)}')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--split', default='test', choices=['test', 'dev', 'all'])
    main(**vars(ap.parse_args()))
