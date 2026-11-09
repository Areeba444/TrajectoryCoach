"""Evidence-constrained generation checker (Gap 2 – G2)."""

FORBIDDEN_PATTERNS = [
    'your code failed',
    'you are stuck',
    'you passed',
    'tests failed',
    'correct answer',
    'wrong answer',
    'your solution',
    'you got it',
    'def ',
    'public class',
    '```',
]

THIN_EVIDENCE_THRESHOLD = 5  # min events in window; below this, scaffold is suppressed


def check_unsupported_claims(prompt: str, evidence: dict) -> list[str]:
    """
    Returns list of violation strings (empty = clean).
    Checks:
      1. Forbidden patterns (case-insensitive)
      2. Claims about outcomes (evidence['outcomes_observed'] is always False)
      3. Code/solution content
    This is a conservative pattern screen, not a semantic verifier.
    """
    violations = []
    lower_prompt = prompt.lower()

    # Check forbidden patterns
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in lower_prompt:
            violations.append(f"Forbidden pattern detected: {pattern!r}")

    # Check outcome claims – outcomes_observed is always False in this system
    outcome_phrases = [
        'test passed', 'test failed', 'your test', 'submission correct',
        'submission failed', 'compile error', 'runtime error',
        'assertion error', 'you are right', 'you are wrong',
    ]
    for phrase in outcome_phrases:
        if phrase.lower() in lower_prompt:
            violations.append(f"Outcome claim detected: {phrase!r}")

    # Check code/solution content (catching patterns not already in FORBIDDEN_PATTERNS)
    code_indicators = ['return ', 'import ', 'class ', 'for ', 'while ', 'if ', '= [', '= {']
    # Only flag these if they appear inside backtick code-like formatting or in combination
    if '```' in prompt:
        violations.append("Code block (```) detected in scaffold")

    return violations


def evidence_floor_met(evidence: dict) -> bool:
    """Return True iff window_events >= THIN_EVIDENCE_THRESHOLD."""
    return evidence.get('window_events', 0) >= THIN_EVIDENCE_THRESHOLD


def validate_scaffold(prompt: str, evidence: dict) -> tuple[bool, list[str]]:
    """Combined check: floor met AND no unsupported claims. Returns (ok, violations)."""
    violations = []
    if not evidence_floor_met(evidence):
        violations.append(
            f"Thin evidence: fewer than {THIN_EVIDENCE_THRESHOLD} events in window"
            f" (got {evidence.get('window_events', 0)})"
        )
    claim_violations = check_unsupported_claims(prompt, evidence)
    violations.extend(claim_violations)
    return (len(violations) == 0, violations)

