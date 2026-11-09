#!/usr/bin/env python
"""Groq-based G2 experiment: test constrained vs unconstrained generation.

Usage:
    python -m scripts.run_llm_experiments --smoke          # 1 prefix
    python -m scripts.run_llm_experiments --prefixes 10    # N prefixes
    python -m scripts.run_llm_experiments                  # 100 prefixes (default)

Requires GROQ_API_KEY environment variable.
"""
import argparse
import json
import os
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

OUTPUT_DIR = _ROOT / 'results' / 'phase2'
OUTPUT = OUTPUT_DIR / 'e_llm_grounding.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke', action='store_true', help='Run with 1 prefix')
    parser.add_argument('--prefixes', type=int, default=100, help='Number of prefixes to test')
    args = parser.parse_args()

    if not os.environ.get('GROQ_API_KEY'):
        print('Error: GROQ_API_KEY environment variable not set.', file=sys.stderr)
        sys.exit(1)

    n_prefixes = 1 if args.smoke else args.prefixes

    from coach.dataset import load_split
    from coach.core import TrajectoryCoach
    from coach.groq_provider import GroqProvider
    from coach.grounding import validate_scaffold, check_unsupported_claims

    print(f'Loading test split events ...')
    events = load_split(split='test')
    print(f'  {len(events)} events loaded. Using {n_prefixes} prefixes.')

    # Build prefixes: take the first N non-wait trigger points
    prefixes = []
    coach = TrajectoryCoach(mode='adaptive', cooldown=180, max_prompts=999,
                            use_timing_gate=False, use_evidence_floor=False)
    for event in events:
        d = coach.observe(event)
        if d.phase != 'wait':
            prefixes.append((d, event))
        if len(prefixes) >= n_prefixes:
            break

    print(f'  {len(prefixes)} non-wait decisions collected.')

    # Test constrained (with evidence floor) vs unconstrained
    results = {
        'n_prefixes': len(prefixes),
        'constrained': [],
        'unconstrained': [],
    }

    provider = GroqProvider()

    for i, (baseline, event) in enumerate(prefixes):
        print(f'  Prefix {i+1}/{len(prefixes)} ...')
        context = {
            'observation': baseline.evidence,
            'allowed_phase': baseline.phase,
            'reflection': '',
            'recent_decisions': [],
        }
        try:
            d = provider.generate(baseline, context)
            # Constrained: apply evidence floor check
            ok, violations = validate_scaffold(d.prompt, baseline.evidence)
            results['constrained'].append({
                'phase': d.phase,
                'prompt': d.prompt,
                'ok': ok,
                'violations': violations,
            })
            # Unconstrained: check raw output violations
            raw_violations = check_unsupported_claims(d.prompt, baseline.evidence)
            results['unconstrained'].append({
                'phase': d.phase,
                'prompt': d.prompt,
                'violations': raw_violations,
            })
        except Exception as e:
            print(f'    Error: {e}')
            results['constrained'].append({'error': str(e)})
            results['unconstrained'].append({'error': str(e)})

    # Summary stats
    n = len(prefixes)
    n_constrained_ok = sum(1 for r in results['constrained']
                          if r.get('ok') is True)
    n_unconstrained_ok = sum(1 for r in results['unconstrained']
                            if not r.get('violations'))
    results['summary'] = {
        'n_prefixes': n,
        'constrained_pass_rate': round(n_constrained_ok / n, 4) if n > 0 else 0,
        'unconstrained_pass_rate': round(n_unconstrained_ok / n, 4) if n > 0 else 0,
        'groq_stats': provider.stats(),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f'\nResults saved to {OUTPUT}')
    print(f'  Constrained pass rate: {results["summary"]["constrained_pass_rate"]}')
    print(f'  Unconstrained pass rate: {results["summary"]["unconstrained_pass_rate"]}')


if __name__ == '__main__':
    main()

