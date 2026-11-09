"""Tests for coach.grounding – evidence floor and unsupported claim detection."""
import unittest
from coach.grounding import (
    check_unsupported_claims, evidence_floor_met, validate_scaffold,
    FORBIDDEN_PATTERNS, THIN_EVIDENCE_THRESHOLD,
)


def _evidence(window_events=10, outcomes_observed=False):
    return {
        'window_events': window_events,
        'outcomes_observed': outcomes_observed,
        'student': 'test',
        'source_row': 1,
    }


class TestGrounding(unittest.TestCase):

    def test_clean_scaffold_passes(self):
        """A clean metacognitive prompt with no forbidden patterns passes."""
        prompt = 'What hypothesis are you currently testing?'
        evidence = _evidence(window_events=10)
        ok, violations = validate_scaffold(prompt, evidence)
        self.assertTrue(ok)
        self.assertEqual(violations, [])

    def test_forbidden_pattern_rejected(self):
        """A prompt containing a forbidden pattern is flagged."""
        prompt = 'Your code failed. Try again.'
        evidence = _evidence(window_events=10)
        violations = check_unsupported_claims(prompt, evidence)
        self.assertTrue(len(violations) > 0)
        self.assertTrue(any('your code failed' in v.lower() for v in violations))

    def test_thin_evidence_suppressed(self):
        """Scaffold is suppressed when window_events < THIN_EVIDENCE_THRESHOLD."""
        prompt = 'What goal are you pursuing?'
        evidence = _evidence(window_events=THIN_EVIDENCE_THRESHOLD - 1)
        ok, violations = validate_scaffold(prompt, evidence)
        self.assertFalse(ok)
        self.assertTrue(any('thin evidence' in v.lower() for v in violations))

    def test_outcome_claim_rejected(self):
        """A prompt mentioning test outcomes is flagged."""
        prompt = 'Your test passed! Well done.'
        evidence = _evidence(window_events=10)
        violations = check_unsupported_claims(prompt, evidence)
        self.assertTrue(len(violations) > 0)

    def test_code_in_scaffold_rejected(self):
        """A prompt containing a code block is flagged."""
        prompt = 'Here is a hint:\n```python\ndef solve(): pass\n```'
        evidence = _evidence(window_events=10)
        violations = check_unsupported_claims(prompt, evidence)
        self.assertTrue(len(violations) > 0)
        self.assertTrue(any('```' in v or 'code' in v.lower() for v in violations))

    def test_evidence_floor_threshold(self):
        """evidence_floor_met returns True at exactly THIN_EVIDENCE_THRESHOLD events."""
        self.assertFalse(evidence_floor_met(_evidence(THIN_EVIDENCE_THRESHOLD - 1)))
        self.assertTrue(evidence_floor_met(_evidence(THIN_EVIDENCE_THRESHOLD)))
        self.assertTrue(evidence_floor_met(_evidence(THIN_EVIDENCE_THRESHOLD + 5)))

    def test_all_forbidden_patterns_detected(self):
        """Every pattern in FORBIDDEN_PATTERNS is caught."""
        evidence = _evidence(window_events=10)
        for pattern in FORBIDDEN_PATTERNS:
            # Put in a context that makes it a full sentence
            prompt = f'Note: {pattern} in this context.'
            violations = check_unsupported_claims(prompt, evidence)
            # The pattern itself or a code block check should be flagged
            # (some patterns like ``` might have extra handling)
            if pattern == '```':
                # For ``` the prompt must actually contain ``` to trigger
                violations2 = check_unsupported_claims(f'```code```', evidence)
                self.assertTrue(len(violations2) > 0, f'Pattern {pattern!r} not caught')
            else:
                self.assertTrue(len(violations) > 0, f'Pattern {pattern!r} not caught')

    def test_validate_scaffold_combined(self):
        """validate_scaffold requires both floor and clean content."""
        good_prompt = 'What is your next step?'
        bad_prompt = 'You are stuck. ```python def f(): pass```'

        # Good prompt, enough evidence
        ok, v = validate_scaffold(good_prompt, _evidence(10))
        self.assertTrue(ok)
        self.assertEqual(v, [])

        # Good prompt, thin evidence
        ok, v = validate_scaffold(good_prompt, _evidence(2))
        self.assertFalse(ok)

        # Bad prompt, enough evidence
        ok, v = validate_scaffold(bad_prompt, _evidence(10))
        self.assertFalse(ok)

        # Bad prompt, thin evidence — multiple violations
        ok, v = validate_scaffold(bad_prompt, _evidence(2))
        self.assertFalse(ok)
        self.assertTrue(len(v) >= 2)


if __name__ == '__main__':
    unittest.main()

