"""G2: does a generated scaffold stay inside what the trajectory actually shows?

The IDE log records keystrokes, runs, focus changes and submissions. It never
records whether code compiled, whether tests passed, what the bug was, or how
the learner felt. Any statement about those is unsupported by the evidence the
agent was given, however fluent it sounds.

A prompt is counted as unsupported if it contains at least one of:

outcome      a claim about correctness, failure, errors or progress
affect       a claim about the learner's emotional or cognitive state
quantity     a number presented as an observed count that no evidence field
             supports
solution     code, or a direct instruction of what to write

The checker is deterministic and conservative: it looks for claims that are
definitely outside the evidence, so it under-counts rather than over-counts.
It is a screen, not a semantic verifier, and a human sample is still rated.
"""
import re

OUTCOME = re.compile(r'\b(fail(?:s|ed|ing|ure)?|error(?:s)?|bug(?:s|gy)?|wrong|incorrect|'
                     r'broken|crash(?:ed|ing)?|passed|passing|correct(?:ly)?|works?|working|'
                     r'succeed(?:ed|s)?|success(?:ful)?|mistake(?:s)?|defect(?:s)?|'
                     r'exception|traceback|syntax)\b', re.I)
AFFECT = re.compile(r'\b(stuck|struggl\w*|frustrat\w*|confus\w*|lost|giving up|give up|'
                    r'overwhelm\w*|anxious|panick\w*|tired|discourag\w*|guess(?:ing)?|'
                    r'random(?:ly)?|careless|rush\w*)\b', re.I)
SOLUTION = re.compile(r'(```|\bdef\s+\w+|\breturn\s+\w|\bimport\s+\w|\bfor\s+\w+\s+in\b|'
                      r'\bif\s+\w+\s*[=<>!]|print\s*\(|\bpublic\s+class\b)', re.I)
NUMBER = re.compile(r'\b\d+\b')

# Numbers that are allowed to appear without matching a count, because they are
# part of ordinary phrasing rather than a claim about the observed trajectory.
HARMLESS = {0, 1, 2, 3}

COUNT_FIELDS = ('runs', 'edits', 'submissions', 'window_events', 'window_seconds',
                'session', 'active_seconds_estimate', 'source_row')


def _supported_numbers(evidence):
    allowed = set(HARMLESS)
    for field in COUNT_FIELDS:
        v = evidence.get(field)
        if isinstance(v, (int, float)):
            allowed.add(int(v))
            allowed.add(int(v // 60))  # the same duration expressed in minutes
    return allowed


def check(prompt, evidence):
    """Return the unsupported claims found in one generated scaffold."""
    issues = []
    for kind, pattern in (('outcome', OUTCOME), ('affect', AFFECT), ('solution', SOLUTION)):
        for m in pattern.finditer(prompt or ''):
            issues.append({'kind': kind, 'span': m.group(0)})
    allowed = _supported_numbers(evidence or {})
    for m in NUMBER.finditer(prompt or ''):
        if int(m.group(0)) not in allowed:
            issues.append({'kind': 'quantity', 'span': m.group(0)})
    return issues


def score(records):
    """Aggregate over many generated scaffolds.

    records: iterable of {'prompt': str, 'evidence': dict}
    """
    total, flagged, by_kind, claims = 0, 0, {}, 0
    details = []
    for r in records:
        total += 1
        issues = check(r.get('prompt', ''), r.get('evidence', {}))
        claims += len(issues)
        if issues:
            flagged += 1
            for i in issues:
                by_kind[i['kind']] = by_kind.get(i['kind'], 0) + 1
            details.append({'prompt': r.get('prompt', ''), 'issues': issues,
                            'student': (r.get('evidence') or {}).get('student')})
    return {'prompts': total,
            'prompts_with_unsupported_claim': flagged,
            'unsupported_rate': round(flagged / total, 4) if total else None,
            'unsupported_claims_total': claims,
            'claims_per_prompt': round(claims / total, 4) if total else None,
            'by_kind': by_kind,
            'examples': details[:25]}
