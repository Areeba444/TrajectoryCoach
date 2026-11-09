#!/usr/bin/env python
"""Run experiments E1–E6 and save results to results/phase2/experiments_<split>.json.

Usage:
    python -m scripts.run_experiments --split test
    python -m scripts.run_experiments --split dev
"""
import argparse
import json
import pathlib
import sys
import time
import tracemalloc

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from coach.core import TrajectoryCoach, decision_dict
from coach.dataset import load_split
from coach.timing import detect_junctures, compute_metrics, cluster_bootstrap
from coach.baselines import OnDemandBaseline
from coach.grounding import validate_scaffold

OUTPUT_DIR = _ROOT / 'results' / 'phase2'

# ── Ablation variant definitions ─────────────────────────────────────────────
ABLATIONS = [
    {
        'name': 'full_system',
        'desc': 'Full system (E3)',
        'kwargs': dict(mode='adaptive', cooldown=180, max_prompts=3,
                       use_timing_gate=True, use_evidence_floor=True),
    },
    {
        'name': 'no_cooldown',
        'desc': 'No cooldown',
        'kwargs': dict(mode='no_cooldown', cooldown=0, max_prompts=3,
                       use_timing_gate=True, use_evidence_floor=True),
    },
    {
        'name': 'no_budget',
        'desc': 'No episode budget',
        'kwargs': dict(mode='adaptive', cooldown=180, max_prompts=999,
                       use_timing_gate=True, use_evidence_floor=True),
    },
    {
        'name': 'no_response_wait',
        'desc': 'No response wait',
        'kwargs': dict(mode='no_memory', cooldown=180, max_prompts=3,
                       use_timing_gate=True, use_evidence_floor=True),
    },
    {
        'name': 'no_evidence_floor',
        'desc': 'No evidence floor (G2 disabled)',
        'kwargs': dict(mode='adaptive', cooldown=180, max_prompts=3,
                       use_timing_gate=True, use_evidence_floor=False),
    },
    {
        'name': 'no_timing_gate',
        'desc': 'No timing gate (G1 disabled)',
        'kwargs': dict(mode='adaptive', cooldown=180, max_prompts=3,
                       use_timing_gate=False, use_evidence_floor=True),
    },
    {
        'name': 'phase1_policy',
        'desc': 'Phase 1 policy (original defaults)',
        'kwargs': dict(mode='adaptive', cooldown=180, max_prompts=3,
                       use_timing_gate=False, use_evidence_floor=False),
    },
]


def run_coach(events, **kwargs):
    """Run coach over events; return (decisions, junctures, metrics, scaffold_count).

    For ablation variants, detect_junctures can be skipped (pass skip_junctures=True
    via kwargs — it is popped before passing to TrajectoryCoach).
    """
    skip_junctures = kwargs.pop('skip_junctures', False)
    coach = TrajectoryCoach(**kwargs)
    decisions = []
    for event in events:
        d = coach.observe(event)
        decisions.append(d)

    scaffold_count = sum(1 for d in decisions if d.phase != 'wait')

    if skip_junctures:
        # Cheap counting path for ablations that just need scaffold_count
        return decisions, [], {}, scaffold_count

    dec_dicts = [
        {'phase': d.phase, 'reason': d.reason, 'prompt': d.prompt, 'evidence': d.evidence}
        for d in decisions
    ]
    junctures = detect_junctures(events, dec_dicts)
    metrics = compute_metrics(junctures)
    return decisions, junctures, metrics, scaffold_count


def run_ablation(events, ablation: dict, full_junctures: list | None = None) -> dict:
    """Run one ablation variant and return a result dict.

    If full_junctures is provided (from the full-system run), skip re-detection.
    For non-full-system variants we only need scaffold_count + efficiency.
    For full_system we need proper juncture metrics.
    """
    is_full = ablation['name'] == 'full_system'

    tracemalloc.start()
    t0 = time.monotonic()

    if is_full:
        decisions, junctures, metrics, scaffold_count = run_coach(events, **ablation['kwargs'])
    else:
        # Skip expensive juncture detection; compute minimal metrics from decisions
        coach = TrajectoryCoach(**ablation['kwargs'])
        decisions = [coach.observe(e) for e in events]
        scaffold_count = sum(1 for d in decisions if d.phase != 'wait')
        # For ablation table we still need interruption/pause metrics; compute from decisions
        dec_dicts = [
            {'phase': d.phase, 'reason': d.reason, 'prompt': d.prompt, 'evidence': d.evidence}
            for d in decisions
        ]
        junctures = detect_junctures(events, dec_dicts)
        metrics = compute_metrics(junctures)

    runtime = time.monotonic() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        'name': ablation['name'],
        'desc': ablation['desc'],
        'scaffold_count': scaffold_count,
        'interruption_rate': metrics.get('interruption_rate', 0.0),
        'pause_aligned_rate': metrics.get('pause_aligned_rate', 0.0),
        'coverage': metrics.get('coverage', 0.0),
        'deliberation_delta': metrics.get('deliberation_delta', 0.0),
        'runtime_seconds': round(runtime, 3),
        'peak_memory_mb': round(peak / 1024 / 1024, 3),
    }


def run_e2_on_demand(events, seeds=(0, 1, 2)):
    """E2: AIMS on-demand comparator, 3 models × seeds."""
    results = []
    for model in ('pause', 'stuck', 'uniform'):
        for seed in seeds:
            baseline = OnDemandBaseline(model=model, seed=seed)
            for event in events:
                baseline.observe(event)
            m = baseline.metrics()
            results.append(m)
    return results


def run_e6_offline_efficiency(events, ablation: dict) -> dict:
    """E6: offline efficiency measurement (throughput)."""
    tracemalloc.start()
    t0 = time.monotonic()
    run_coach(events, **ablation['kwargs'])
    runtime = time.monotonic() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        'events_per_second': round(len(events) / runtime, 1) if runtime > 0 else 0,
        'runtime_seconds': round(runtime, 3),
        'peak_memory_mb': round(peak / 1024 / 1024, 3),
        'n_events': len(events),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', default='test', choices=['dev', 'test'])
    args = parser.parse_args()

    # ── Load events ONCE and reuse for all experiments ──────────────────────
    print(f'Loading {args.split} split events ...')
    events = load_split(split=args.split)
    n_events = len(events)
    print(f'  {n_events} events loaded.')

    results = {
        'split': args.split,
        'n_events': n_events,
        'e1_rule_baseline': None,
        'e2_on_demand': [],
        'e3_full_system': None,
        'e5_ablations': [],
        'e6_efficiency': None,
    }

    # E1: Rule baseline (single pass, no gate/floor)
    print('E1: Rule baseline ...')
    t0 = time.monotonic()
    tracemalloc.start()
    coach_rule = TrajectoryCoach(mode='rule')
    decisions_rule = [coach_rule.observe(e) for e in events]
    runtime_rule = time.monotonic() - t0
    _, peak_rule = tracemalloc.get_traced_memory(); tracemalloc.stop()
    dec_dicts_rule = [
        {'phase': d.phase, 'reason': d.reason, 'prompt': d.prompt, 'evidence': d.evidence}
        for d in decisions_rule
    ]
    junctures_rule = detect_junctures(events, dec_dicts_rule)
    metrics_rule = compute_metrics(junctures_rule)
    scaffold_count_rule = sum(1 for d in decisions_rule if d.phase != 'wait')
    results['e1_rule_baseline'] = {
        'scaffold_count': scaffold_count_rule,
        'runtime_seconds': round(runtime_rule, 3),
        'peak_memory_mb': round(peak_rule / 1024 / 1024, 3),
        'events_per_second': round(n_events / runtime_rule, 1),
        **metrics_rule,
    }
    print(f'  Rule baseline: {scaffold_count_rule} scaffolds, {runtime_rule:.1f}s')

    # E2: On-demand baselines (3 models × 3 seeds = 9 runs)
    print('E2: On-demand baselines (9 runs) ...')
    results['e2_on_demand'] = run_e2_on_demand(events, seeds=[0, 1, 2])
    print(f'  On-demand: {len(results["e2_on_demand"])} runs done')

    # E5: All ablations in one loop (full system is variant 0 = E3)
    print('E5: Ablation study (7 variants, includes E3) ...')
    for ablation in ABLATIONS:
        print(f'  [{ablation["name"]}] ...', end=' ', flush=True)
        result = run_ablation(events, ablation)
        results['e5_ablations'].append(result)
        print(f'{result["scaffold_count"]} scaffolds, {result["runtime_seconds"]:.1f}s')

    # E3 is the full_system ablation result
    results['e3_full_system'] = next(
        r for r in results['e5_ablations'] if r['name'] == 'full_system'
    )
    print(f'  E3 full system: {results["e3_full_system"]["scaffold_count"]} scaffolds')

    # E6: Offline efficiency — compare rule baseline vs full system
    print('E6: Offline efficiency ...')
    full_ablation = next(a for a in ABLATIONS if a['name'] == 'full_system')
    e6 = run_e6_offline_efficiency(events, full_ablation)
    e6['rule_baseline'] = {
        'runtime_seconds': results['e1_rule_baseline']['runtime_seconds'],
        'events_per_second': results['e1_rule_baseline']['events_per_second'],
        'peak_memory_mb': results['e1_rule_baseline']['peak_memory_mb'],
    }
    results['e6_efficiency'] = e6
    print(f'  Throughput: {e6["events_per_second"]} events/sec, '
          f'memory: {e6["peak_memory_mb"]} MB')

    # Bootstrap CIs for E3 full system (reuse events, run coach once more)
    print('Computing bootstrap CIs for E3 ...')
    t0 = time.monotonic()
    coach_full = TrajectoryCoach(
        mode='adaptive', cooldown=180, max_prompts=3,
        use_timing_gate=True, use_evidence_floor=True,
    )
    full_decs = [coach_full.observe(e) for e in events]
    full_dec_dicts = [
        {'phase': d.phase, 'reason': d.reason, 'prompt': d.prompt, 'evidence': d.evidence}
        for d in full_decs
    ]
    full_junctures = detect_junctures(events, full_dec_dicts)
    ci = cluster_bootstrap(full_junctures, n_boot=1000, seed=0)
    results['e3_full_system']['bootstrap_ci'] = ci
    print(f'  Bootstrap done in {time.monotonic()-t0:.1f}s')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f'experiments_{args.split}.json'
    output_path.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f'\nResults saved to {output_path}')
    e3 = results['e3_full_system']
    print(f'Summary:')
    print(f'  E1 rule baseline : {scaffold_count_rule} scaffolds')
    print(f'  E3 full system   : {e3["scaffold_count"]} scaffolds')
    print(f'  Interruption     : E1={results["e1_rule_baseline"].get("interruption_rate",0):.4f}  '
          f'E3={e3.get("interruption_rate",0):.4f}')
    print(f'  Pause-aligned    : E1={results["e1_rule_baseline"].get("pause_aligned_rate",0):.4f}  '
          f'E3={e3.get("pause_aligned_rate",0):.4f}')


if __name__ == '__main__':
    main()

