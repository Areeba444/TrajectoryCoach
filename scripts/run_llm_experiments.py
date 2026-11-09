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


def smoke(model, temperature, seed, prompt_version='v1'):
    from coach.groq_provider import GroqProvider
    from coach.core import Decision
    p = GroqProvider(model=model, temperature=temperature, seed=seed, max_calls=4,
                     prompt_version=prompt_version)
    baseline = Decision('monitor', 'Repeated executions within the observation window',
                        'placeholder', {'student': '2', 'part': '1', 'exercise': '3',
                                        'source_row': 1234, 'time': 0, 'runs': 4, 'edits': 51,
                                        'submissions': 0, 'window_events': 60,
                                        'window_seconds': 300, 'outcomes_observed': False})
    try:
        d = p.generate(baseline, {'observation': baseline.evidence, 'allowed_phase': 'monitor',
                                  'reflection': '', 'recent_decisions': []})
    except ValueError as exc:
        print('The validator rejected the model reply:', exc)
        print('Raw reply:', p.traces[-1].get('raw_reply') if p.traces else None)
        raise SystemExit(1)
    print(json.dumps({'phase': d.phase, 'prompt': d.prompt, 'reason': d.reason,
                      'provider': d.provider}, indent=2))
    print(json.dumps(p.efficiency(), indent=2))
    print('\nunsupported claims found:', grounding.check(d.prompt, baseline.evidence))


def _abort_on_rate_limit(exc, done):
    """A run that hit the rate limit is not a measurement: failed calls would be
    scored as clean deterministic fallbacks. Stop before anything is written."""
    msg = str(exc)
    if 'HTTP 429' in msg or 'Rate limit' in msg:
        print(f'\nSTOPPED after {done} prefixes: rate limit reached.\n{msg[:300]}\n'
              'Progress so far is saved in the checkpoint file; no result files were written. Wait for the limit to reset (the daily '
              'limit resets after 24 h; the per-minute limit after a minute), raise '
              '--sleep, and run again.', flush=True)
        raise SystemExit(2)


def main(prefixes=100, model=None, temperature=0.0, seed=0, sleep=1.0,
         split='test', gate_seconds=20, min_evidence=5, price_in=None, price_out=None,
         prompt_version='v1', max_new=0, fresh=False):
    # The full system is gate_seconds=20 plus min_evidence=5 (see run_experiments.FULL).
    # A run with another floor is saved under a suffixed name so it cannot overwrite
    # the headline result; min_evidence=0 is the '- evidence floor' contrast.
    tag = ('' if min_evidence == 5 else f'_floor{min_evidence}') + ('' if prompt_version == 'v1' else f'_{prompt_version}')
    from coach.groq_provider import GroqProvider
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    print('pass 1: finding candidate prefixes ...', flush=True)
    engine = TrajectoryCoach(mode='adaptive', gate_seconds=gate_seconds,
                             min_evidence=min_evidence)
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
                       max_calls=10 * len(chosen) + 50, constrained=True, use_tools=True, prompt_version=prompt_version)
    unc = GroqProvider(model=model, temperature=temperature, seed=seed,
                       max_calls=2 * len(chosen) + 10, constrained=False, use_tools=False)
    con.key = unc.key = con.key  # same credential, separate budgets

    print('pass 2: generating ...', flush=True)
    engine = TrajectoryCoach(mode='adaptive', gate_seconds=gate_seconds,
                             min_evidence=min_evidence)
    # Batch mode. Each finished prefix is appended to a checkpoint file, so a run that
    # hits the rate limit (or is stopped with --max-new) continues where it left off.
    # Nothing is scored until every sampled prefix has a real model reply.
    run_key = {'split': split, 'prefixes': len(chosen), 'model': con.model,
               'temperature': temperature, 'seed': seed, 'gate_seconds': gate_seconds,
               'min_evidence': min_evidence, 'prompt_version': prompt_version}
    ckpt = LOGS / f'g2_checkpoint{tag}.jsonl'
    done = {}
    if fresh and ckpt.exists():
        ckpt.unlink()
    if ckpt.exists():
        for line in ckpt.read_text(encoding='utf-8').splitlines():
            rec = json.loads(line)
            if rec['run_key'] != run_key:
                raise SystemExit(f'{ckpt.name} was made with different settings; '
                                 'delete it or pass --fresh.')
            done[rec['idx']] = rec
        print(f'resuming: {len(done)}/{len(chosen)} prefixes already finished', flush=True)
        for rec in done.values():
            con.usage.extend(rec['con_usage']); unc.usage.extend(rec['unc_usage'])
            con.calls += rec['con_calls']; unc.calls += rec['unc_calls']
            con.retries += rec['con_retries']; unc.retries += rec['unc_retries']
            con.failures.extend(rec['con_failures'])
            if rec['con_trace'] is not None:
                con.traces.append(rec['con_trace'])
            if rec['tools_disabled']:
                con._tool_support = False

    index, new = 0, 0
    for e in iter_events(split):
        d = engine.observe(e)
        if d.phase == 'wait':
            continue
        here, index = index in chosen, index + 1
        if not here or (index - 1) in done:
            continue
        if max_new and new >= max_new:
            break
        idx = index - 1
        context = {'observation': d.evidence, 'allowed_phase': d.phase,
                   'reflection': engine.states[e.student].reflection,
                   'recent_decisions': list(engine.states[e.student].recent_decisions)}
        c0, u0 = (len(con.usage), con.calls, con.retries, len(con.failures), len(con.traces)), \
                 (len(unc.usage), unc.calls, unc.retries)
        errs, con_rec, unc_rec = [], None, None
        try:
            cd = con.generate(dict_to_decision(d), dict(context, _coach=engine))
            con_rec = {'prompt': cd.prompt, 'evidence': d.evidence,
                       'phase': cd.phase, 'reason': cd.reason}
        except Exception as exc:
            _abort_on_rate_limit(exc, len(done))
            errs.append(f'constrained: {type(exc).__name__}: {exc}')
            con_rec = {'prompt': d.prompt, 'evidence': d.evidence,
                       'phase': d.phase, 'reason': 'deterministic fallback'}
        time.sleep(sleep)
        try:
            ud = unc.generate_unconstrained(dict_to_decision(d), context)
            unc_rec = {'prompt': ud.prompt, 'evidence': d.evidence, 'phase': ud.phase}
        except Exception as exc:
            _abort_on_rate_limit(exc, len(done))
            errs.append(f'unconstrained: {type(exc).__name__}: {exc}')
        time.sleep(sleep)
        rec = {'run_key': run_key, 'idx': idx, 'con_rec': con_rec, 'unc_rec': unc_rec,
               'errors': errs,
               'con_usage': con.usage[c0[0]:], 'con_calls': con.calls - c0[1],
               'con_retries': con.retries - c0[2], 'con_failures': con.failures[c0[3]:],
               'con_trace': con.traces[-1] if len(con.traces) > c0[4] else None,
               'unc_usage': unc.usage[u0[0]:], 'unc_calls': unc.calls - u0[1],
               'unc_retries': unc.retries - u0[2], 'tools_disabled': con._tool_support is False}
        with ckpt.open('a', encoding='utf-8') as w:
            w.write(json.dumps(rec) + '\n')
        done[idx] = rec
        new += 1
        if len(done) % 10 == 0:
            print(f'  {len(done)}/{len(chosen)} done', flush=True)

    if len(done) < len(chosen):
        print(f'\nBATCH FINISHED: {len(done)}/{len(chosen)} prefixes done. Nothing scored yet. '
              'Run the same command again to continue.', flush=True)
        raise SystemExit(0)
    order = sorted(done)
    con_records = [done[i]['con_rec'] for i in order]
    unc_records = [done[i]['unc_rec'] for i in order if done[i]['unc_rec'] is not None]
    errors = [x for i in order for x in done[i]['errors']]

    out = {
        'split': split, 'sampled_prefixes': len(chosen), 'model': con.model,
        'temperature': temperature, 'seed': seed, 'gate_seconds': gate_seconds,
        'min_evidence': min_evidence, 'prompt_version': prompt_version, 'delivered_scaffolds_in_split': total,
        'constrained': grounding.score(con_records),
        'unconstrained': grounding.score(unc_records),
        'efficiency_constrained': con.efficiency(price_in, price_out),
        'efficiency_unconstrained': unc.efficiency(price_in, price_out),
        'errors': errors[:50], 'error_count': len(errors),
    }
    (RESULTS / f'e4_g2_grounding{tag}.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    for name, recs in (('g2_constrained', con_records), ('g2_unconstrained', unc_records)):
        with (LOGS / f'{name}{tag}.jsonl').open('w', encoding='utf-8') as w:
            for r in recs:
                w.write(json.dumps(r) + '\n')
    with (LOGS / f'g2_agent_traces{tag}.jsonl').open('w', encoding='utf-8') as w:
        for t in con.traces:
            w.write(json.dumps(t) + '\n')
    print('\n--- G2 grounding ---')
    print(f"constrained   unsupported rate {out['constrained']['unsupported_rate']} "
          f"({out['constrained']['prompts_with_unsupported_claim']}/{out['constrained']['prompts']})")
    print(f"unconstrained unsupported rate {out['unconstrained']['unsupported_rate']} "
          f"({out['unconstrained']['prompts_with_unsupported_claim']}/{out['unconstrained']['prompts']})")
    print(json.dumps(out['efficiency_constrained'], indent=2))
    print(f"\nwrote {RESULTS / f'e4_g2_grounding{tag}.json'}")


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
    ap.add_argument('--min-evidence', type=int, default=5, dest='min_evidence')
    ap.add_argument('--prompt-version', default='v1', choices=['v1', 'v2'], dest='prompt_version')
    ap.add_argument('--max-new', type=int, default=0, dest='max_new',
                    help='stop after this many new prefixes (batch mode); rerun to continue')
    ap.add_argument('--fresh', action='store_true', help='discard the checkpoint and start over')
    ap.add_argument('--price-in', type=float, dest='price_in')
    ap.add_argument('--price-out', type=float, dest='price_out')
    a = vars(ap.parse_args())
    if a.pop('smoke'):
        smoke(a['model'], a['temperature'], a['seed'], a['prompt_version'])
    else:
        main(**a)
