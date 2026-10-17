import unittest
from coach.core import Event, TrajectoryCoach
from coach.tools import ToolBox, ToolError, tool_specs


def ev(t, name='run', student='a', exercise='1'):
    return Event(student, '1', exercise, name, float(t), int(t) + 2)


def make():
    c = TrajectoryCoach(mode='adaptive')
    c.observe(ev(0, 'text_insert'))
    c.observe(ev(10))
    c.observe(ev(20))
    return c


class ToolTests(unittest.TestCase):
    def test_summary_matches_engine_and_has_no_outcomes(self):
        box = ToolBox(make())
        s = box.call('get_trajectory_summary', student='a')
        self.assertEqual((s['runs'], s['edits']), (2, 1))
        self.assertFalse(s['outcomes_observed'])

    def test_prior_interventions_and_limit_validation(self):
        box = ToolBox(make())
        r = box.call('get_prior_interventions', student='a', limit=1)
        self.assertEqual(len(r['recent']), 1)
        self.assertEqual(r['recent'][0]['phase'], 'plan')
        with self.assertRaises(ToolError):
            box.call('get_prior_interventions', student='a', limit=99)

    def test_reflection_is_returned_as_data(self):
        c = make()
        c.reflect('a', 'I will test an empty list.', 21)
        r = ToolBox(c).call('get_learner_reflection', student='a')
        self.assertEqual(r['reflection'], 'I will test an empty list.')

    def test_evidence_row_check(self):
        box = ToolBox(make())
        self.assertTrue(box.call('check_evidence_row', student='a', source_row=12)['in_window'])
        self.assertFalse(box.call('check_evidence_row', student='a', source_row=999)['in_window'])

    def test_unknown_tool_learner_and_arguments_are_rejected(self):
        box = ToolBox(make())
        with self.assertRaises(ToolError): box.call('run_student_code', student='a')
        with self.assertRaises(ToolError): box.call('get_trajectory_summary', student='zzz')
        with self.assertRaises(ToolError): box.call('get_trajectory_summary', student='a', code='x')

    def test_call_budget(self):
        box = ToolBox(make(), max_calls=2)
        box.call('get_trajectory_summary', student='a')
        box.call('get_trajectory_summary', student='a')
        with self.assertRaises(ToolError): box.call('get_trajectory_summary', student='a')
        self.assertEqual(len(box.log), 2)

    def test_tools_do_not_change_engine_state(self):
        c = make(); before = (c.states['a'].task_prompts, len(c.states['a'].history))
        box = ToolBox(c)
        for n in ('get_trajectory_summary', 'get_prior_interventions', 'get_learner_reflection'):
            box.call(n, student='a')
        self.assertEqual(before, (c.states['a'].task_prompts, len(c.states['a'].history)))

    def test_specs_list_every_tool(self):
        self.assertEqual({s['name'] for s in tool_specs()},
                         {'get_trajectory_summary', 'get_prior_interventions',
                          'get_learner_reflection', 'check_evidence_row'})


if __name__ == '__main__':
    unittest.main()
