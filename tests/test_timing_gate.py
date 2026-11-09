import unittest
from coach.core import Event, TrajectoryCoach


def ev(t, kind='text_insert', student='a', exercise='1'):
    return Event(student, '1', exercise, kind, float(t), int(t) + 2)


class TimingGateTests(unittest.TestCase):
    def test_gate_off_reproduces_phase1(self):
        a = TrajectoryCoach(mode='adaptive')
        b = TrajectoryCoach(mode='adaptive', gate_seconds=0)
        seq = [ev(0, 'text_insert'), ev(1), ev(2), ev(3), ev(400, 'submit')]
        self.assertEqual([a.observe(e).phase for e in seq],
                         [b.observe(e).phase for e in list(seq)])

    def test_scaffold_is_held_until_the_learner_pauses(self):
        c = TrajectoryCoach(mode='adaptive', gate_seconds=20)
        self.assertEqual(c.observe(ev(0, 'text_insert')).phase, 'wait')
        self.assertEqual(c.gate_stats['held'], 1)
        self.assertEqual(c.observe(ev(5, 'text_insert')).phase, 'wait')
        d = c.observe(ev(100, 'text_insert'))
        self.assertEqual(d.phase, 'plan')
        self.assertTrue(d.evidence['gated'])

    def test_release_time_sits_inside_the_pause(self):
        c = TrajectoryCoach(mode='adaptive', gate_seconds=20)
        c.observe(ev(10, 'text_insert'))
        d = c.observe(ev(200, 'text_insert'))
        self.assertEqual(d.evidence['time'], 30.0)       # last event + gate
        self.assertEqual(d.evidence['delivery_delay'], 20.0)

    def test_held_scaffold_expires_after_the_horizon(self):
        c = TrajectoryCoach(mode='adaptive', gate_seconds=20, gate_horizon=30)
        c.observe(ev(0, 'text_insert'))
        for t in range(1, 40, 2):                         # never pauses
            c.observe(ev(t, 'text_insert'))
        self.assertEqual(c.gate_stats['dropped'], 1)

    def test_superseded_scaffolds_are_counted(self):
        c = TrajectoryCoach(mode='adaptive', gate_seconds=20, min_evidence=0)
        c.observe(ev(0, 'text_insert'))                   # plan held
        for t in (1, 2, 3):
            c.observe(ev(t, 'run'))                       # monitor replaces it
        self.assertGreaterEqual(c.gate_stats['superseded'], 1)

    def test_evidence_floor_blocks_a_thin_window(self):
        c = TrajectoryCoach(mode='rule', min_evidence=5)
        d = c.observe(ev(0, 'text_insert'))
        self.assertEqual(d.phase, 'wait')
        self.assertIn('evidence floor', d.reason)

    def test_evidence_floor_allows_a_full_window(self):
        c = TrajectoryCoach(mode='rule', min_evidence=3)
        for t in range(4):
            c.observe(ev(t, 'text_insert'))
        self.assertEqual(c.observe(ev(5, 'submit')).phase, 'evaluate')

    def test_invalid_gate_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            TrajectoryCoach(gate_seconds=-1)
        with self.assertRaises(ValueError):
            TrajectoryCoach(gate_horizon=0)
        with self.assertRaises(ValueError):
            TrajectoryCoach(min_evidence=-1)


if __name__ == '__main__':
    unittest.main()
