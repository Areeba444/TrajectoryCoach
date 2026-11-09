"""E3/E4-G2/E6 with a live model. Run this on a machine that can reach Groq.

    set GROQ_API_KEY=...            (Windows:  setx / $env:GROQ_API_KEY)
    python -m scripts.run_llm_experiments --smoke
    python -m scripts.run_llm_experiments --prefixes 100

--smoke makes a single call and prints the result, so the key and model are
checked before the full run. The full run samples held-out trajectory prefixes
from the test split, generates a scaffold for each under the constrained and
the unconstrained condition, scores both with the grounding checker, and
records tokens, latency and tool use.
"""
import argparse, json, pathlib, random, time

from coach.core import TrajectoryCoach, decision_dict
from coach.dataset import iter_events
from coach import grounding

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results' / 'phase2'
LOGS = ROOT / 'logs'


def smoke(model, temperature, seed):
    from coach.groq_provider import GroqProvider
    from coach.core import Decision
    p = GroqProvider(model=model, temperature=temperature, seed=seed, max_calls=4)
    baseline = Decision('monitor', 'Repeated executions within the observation window',
                        'placeholder', {'student': '2', 'part': '1', 'exercise': '3',
                                        'source_row': 1234, 'time': 0, 'runs': 4, 'edits': 51,
                                        'submissions': 0, 'window_events': 60,
                                        'window_seconds': 300, 'outcomes_observed': False})
    d = p.generate(baseline, {'observation': baseline.evidence, 'allowed_phase': 'monitor',
                              'reflection': '', 'recent_decisions': []})
    print(json.dumps({'phase': d.phase, 'prompt': d.prompt, 'reason': d.reason,
                      'provider': d.provider}, indent=2))
    print(json.dumps(p.efficiency(), indent=2))
    print('\nunsupported claims found:', grounding.check(d.prompt, baseline.evidence))


def main(prefixes=100, model=None, temperature=0.0, seed=0, sleep=1.0,
         split='test', gate_seconds=20, price_in=None, price_out=None):
    from coach.groq_provider import GroqProvider
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    print('pass 1: finding candidate prefixes ...', flush=True)
    engine = TrajectoryCoach(mode='adaptive', gate_seconds=gate_seconds)
    candidates = []
    for e in iter_events(split):
        d = engine.observe(e)
        if d.phase != 'wait':
            candidates.append(len(candidates))
    total = len(candidates)
    if total < prefixes:
        prefixes = total
    step = max(1, total // prefixes)
    chosen = set(range(0, total, step))
    while len(chosen) > prefixes:
        chosen.discard(max(chosen))
    print(f'{total} delivered scaffolds on {split}; sampling {len(chosen)} '
          f'every {step}th for the model runs', flush=True)

    con = GroqProvider(model=model, temperature=temperature, seed=seed,
                       max_calls=10 * len(chosen) + 50, constrained=True, use_tools=True)
    unc = GroqProvider(model=model, temperature=temperature, seed=seed,
                       max_calls=2 * len(chosen) + 10, constrained=False, use_tools=False)
    con.key = unc.key = con.key  # same credential, separate budgets

    print('pass 2: generating ...', flush=True)
    engine = TrajectoryCoach(mode='adaptive', gate_seconds=gate_seconds)
    con_records, unc_records, index = [], [], 0
    errors = []
    for e in iter_events(split):
        d = engine.observe(e)
        if d.phase == 'wait':
            continue
        here, index = index in chosen, index + 1
        if not here:
            continue
        context = {'observation': d.evidence, 'allowed_phase': d.phase,
                   'reflection': engine.states[e.student].reflection,
                   'recent_decisions': list(engine.states[e.student].recent_decisions)}
        try:
            cd = con.generate(dict_to_decision(d), dict(context, _coach=engine))
            con_records.append({'prompt': cd.prompt, 'evidence': d.evidence,
                                'phase': cd.phase, 'reason': cd.reason})
        except Exception as exc:
            errors.append(f'constrained: {type(exc).__name__}: {exc}')
            con_records.append({'prompt': d.prompt, 'evidence': d.evidence,
                                'phase': d.phase, 'reason': 'deterministic fallback'})
        time.sleep(sleep)
        try:
            ud = unc.generate_unconstrained(dict_to_decision(d), context)
            unc_records.append({'prompt': ud.prompt, 'evidence': d.evidence, 'phase': ud.phase})
        except Exception as exc:
            errors.append(f'unconstrained: {type(exc).__name__}: {exc}')
        time.sleep(sleep)
        if len(con_records) % 10 == 0:
            print(f'  {len(con_records)}/{len(chosen)} done', flush=True)

    out = {
        'split': split, 'sampled_prefixes': len(chosen), 'model': con.model,
        'temperature': temperature, 'seed': seed, 'gate_seconds': gate_seconds,
        'constrained': grounding.score(con_records),
        'unconstrained': grounding.score(unc_records),
        'efficiency_constrained': con.efficiency(price_in, price_out),
        'efficiency_unconstrained': unc.efficiency(price_in, price_out),
        'errors': errors[:50], 'error_count': len(errors),
    }
    (RESULTS / 'e4_g2_grounding.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    for name, recs in (('g2_constrained', con_records), ('g2_unconstrained', unc_records)):
        with (LOGS / f'{name}.jsonl').open('w', encoding='utf-8') as w:
            for r in recs:
                w.write(json.dumps(r) + '\n')
    with (LOGS / 'g2_agent_traces.jsonl').open('w', encoding='utf-8') as w:
        for t in con.traces:
            w.write(json.dumps(t) + '\n')
    print('\n--- G2 grounding ---')
    print(f"constrained   unsupported rate {out['constrained']['unsupported_rate']} "
          f"({out['constrained']['prompts_with_unsupported_claim']}/{out['constrained']['prompts']})")
    print(f"unconstrained unsupported rate {out['unconstrained']['unsupported_rate']} "
          f"({out['unconstrained']['prompts_with_unsupported_claim']}/{out['unconstrained']['prompts']})")
    print(json.dumps(out['efficiency_constrained'], indent=2))
    print(f"\nwrote {RESULTS / 'e4_g2_grounding.json'}")


def dict_to_decision(d):
    return d


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--prefixes', type=int, default=100)
    ap.add_argument('--model')
    ap.add_argument('--temperature', type=float, default=0.0)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--sleep', type=float, default=1.0)
    ap.add_argument('--split', default='test', choices=['test', 'dev'])
    ap.add_argument('--gate-seconds', type=int, default=20, dest='gate_seconds')
    ap.add_argument('--price-in', type=float, dest='price_in')
    ap.add_argument('--price-out', type=float, dest='price_out')
    a = vars(ap.parse_args())
    if a.pop('smoke'):
        smoke(a['model'], a['temperature'], a['seed'])
    else:
        main(**a)
