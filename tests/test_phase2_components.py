import unittest, random
from coach.baselines import OnDemandCoach, BASE_PAPER_RATE, _poisson, PAUSE_GATE
from coach.core import Event
from coach import grounding
from coach.stats import spearman, rank, pearson
from coach.simulator import run_study
from coach.dataset import load_splits


def ev(t, kind='text_insert', student='a'):
    return Event(student, '1', '1', kind, float(t), int(t) + 2)


class BaselineTests(unittest.TestCase):
    def test_rate_matches_the_base_paper(self):
        self.assertAlmostEqual(BASE_PAPER_RATE, 725 / (102 * 14), places=9)

    def test_poisson_mean_is_close_to_the_rate(self):
        rng = random.Random(0)
        draws = [_poisson(rng, 0.5) for _ in range(20000)]
        self.assertAlmostEqual(sum(draws) / len(draws), 0.5, delta=0.03)

    def test_same_seed_gives_the_same_requests(self):
        groups = {('a', '1', '1'): [ev(t * 30) for t in range(60)]}
        a = OnDemandCoach(seed=7).run(groups)
        b = OnDemandCoach(seed=7).run(groups)
        self.assertEqual([d.evidence['source_row'] for d in a],
                         [d.evidence['source_row'] for d in b])

    def test_pause_model_requests_land_in_pauses(self):
        events = [ev(0), ev(1), ev(2), ev(500), ev(501)]
        groups = {('a', '1', '1'): events}
        for seed in range(12):
            for d in OnDemandCoach(request_model='pause', seed=seed).run(groups):
                prior = [e.time for e in events if e.time < d.evidence['time']]
                if prior:
                    self.assertGreaterEqual(d.evidence['time'] - max(prior), 0.0)

    def test_unknown_request_model_is_rejected(self):
        with self.assertRaises(ValueError):
            OnDemandCoach(request_model='magic')


class GroundingTests(unittest.TestCase):
    evidence = {'runs': 4, 'edits': 37, 'submissions': 0, 'window_events': 52,
                'window_seconds': 300, 'session': 1, 'active_seconds_estimate': 600,
                'source_row': 991}

    def test_a_grounded_prompt_is_clean(self):
        text = ('The recent window contains 4 runs. What hypothesis are you checking, '
                'and what result would support it?')
        self.assertEqual(grounding.check(text, self.evidence), [])

    def test_outcome_and_affect_claims_are_caught(self):
        kinds = {i['kind'] for i in
                 grounding.check('You seem stuck and your tests failed.', self.evidence)}
        self.assertEqual(kinds, {'affect', 'outcome'})

    def test_invented_counts_are_caught(self):
        kinds = [i['kind'] for i in grounding.check('You ran it 97 times.', self.evidence)]
        self.assertIn('quantity', kinds)

    def test_counts_present_in_the_evidence_are_allowed(self):
        self.assertEqual(grounding.check('37 edits and 52 events.', self.evidence), [])

    def test_code_is_caught(self):
        kinds = [i['kind'] for i in
                 grounding.check('Try: def solve(x): return x', self.evidence)]
        self.assertIn('solution', kinds)

    def test_score_aggregates_over_prompts(self):
        rows = [{'prompt': 'What edge case will you check?', 'evidence': self.evidence},
                {'prompt': 'Your code is wrong.', 'evidence': self.evidence}]
        out = grounding.score(rows)
        self.assertEqual(out['prompts'], 2)
        self.assertEqual(out['prompts_with_unsupported_claim'], 1)
        self.assertEqual(out['unsupported_rate'], 0.5)


class StatsTests(unittest.TestCase):
    def test_perfect_monotone_relation(self):
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [40, 30, 20, 10]), -1.0)

    def test_ties_share_a_rank(self):
        self.assertEqual(rank([5, 5, 9]), [1.5, 1.5, 3.0])

    def test_constant_input_has_no_correlation(self):
        self.assertIsNone(pearson([1, 1, 1], [1, 2, 3]))


class SimulatorTests(unittest.TestCase):
    def test_reproducible_for_a_seed(self):
        self.assertEqual(run_study(n_learners=20, seed=3),
                         run_study(n_learners=20, seed=3))

    def test_scores_stay_inside_the_rubric_range(self):
        for row in run_study(n_learners=60, seed=1):
            self.assertTrue(0.0 <= row['transfer_score'] <= 4.0)
            self.assertTrue(0.0 <= row['assisted_completion'] <= 1.0)
            self.assertTrue(0.0 <= row['latent_skill_after'] <= 1.0)

    def test_unassisted_learners_gain_nothing(self):
        for row in run_study(n_learners=40, condition='unassisted', seed=2):
            self.assertEqual(row['skill_gain'], 0.0)


class SplitTests(unittest.TestCase):
    def test_dev_and_test_are_disjoint_and_complete(self):
        s = load_splits()
        self.assertEqual(set(s['dev']) & set(s['test']), set())
        self.assertEqual(len(s['dev']) + len(s['test']), 24)
        self.assertEqual(s['dev_events'] + s['test_events'], s['total_events'])


if __name__ == '__main__':
    unittest.main()
