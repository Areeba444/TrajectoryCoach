import unittest
from coach.core import Event,TrajectoryCoach,Decision
from coach.provider import validate_output

def ev(t,name='run',student='a',exercise='1'):
    return Event(student,'1',exercise,name,float(t),int(t)+2)

class CoachTests(unittest.TestCase):
    def test_observable_triggers_without_diagnosis(self):
        c=TrajectoryCoach(mode='rule')
        self.assertEqual(c.observe(ev(0,'text_insert')).phase,'plan')
        for t in (1,2): self.assertEqual(c.observe(ev(t)).phase,'wait')
        d=c.observe(ev(3)); self.assertEqual(d.phase,'monitor')
        self.assertFalse(d.evidence['outcomes_observed'])
        self.assertNotIn('failed',d.prompt)
        self.assertEqual(c.observe(ev(4,'submit')).phase,'evaluate')

    def test_no_cross_learner_leakage(self):
        c=TrajectoryCoach(mode='rule')
        for e in [ev(0,'text_insert'),ev(1),ev(2)]: c.observe(e)
        self.assertEqual(c.observe(ev(3,student='b')).evidence['runs'],1)

    def test_cooldown_and_response_are_independent(self):
        c=TrajectoryCoach(); c.observe(ev(0,'text_insert'))
        c.reflect('a','I will test an empty list.',1)
        c.observe(ev(10));c.observe(ev(20))
        self.assertEqual(c.observe(ev(30)).reason,'Cooldown active')
        self.assertEqual(c.observe(ev(180)).phase,'monitor')

    def test_prompt_budget(self):
        c=TrajectoryCoach(max_prompts=1)
        c.observe(ev(0,'text_insert'))
        self.assertEqual(c.observe(ev(400,'submit')).reason,'Task/session prompt budget exhausted')

    def test_window_expiry(self):
        c=TrajectoryCoach(mode='rule');c.observe(ev(0,'text_insert'));c.observe(ev(1));c.observe(ev(2))
        d=c.observe(ev(400));self.assertEqual(d.phase,'wait');self.assertEqual(d.evidence['runs'],1)

    def test_chronology(self):
        c=TrajectoryCoach();c.observe(ev(10))
        with self.assertRaises(ValueError):c.observe(ev(9))

    def test_session_reset(self):
        c=TrajectoryCoach();c.observe(ev(0,'text_insert'))
        d=c.observe(ev(1900,'text_insert'))
        self.assertEqual(d.phase,'plan');self.assertEqual(d.evidence['session'],2)

    def test_task_switch_clears_window(self):
        c=TrajectoryCoach(mode='rule');c.observe(ev(0,'text_insert'));c.observe(ev(1))
        d=c.observe(ev(2,exercise='2'));self.assertEqual(d.evidence['runs'],1)

    def test_absence_and_focus_are_not_active_work(self):
        c=TrajectoryCoach();c.observe(ev(0,'focus_lost'));d=c.observe(ev(600,'focus_gained'))
        self.assertEqual(d.evidence['active_seconds_estimate'],0)

    def test_idle_time_is_capped(self):
        c=TrajectoryCoach();c.observe(ev(0,'text_insert'));d=c.observe(ev(600))
        self.assertEqual(d.evidence['active_seconds_estimate'],60)

    def test_invalid_event_and_date(self):
        with self.assertRaises(ValueError):TrajectoryCoach().observe(ev(0,'test_failed'))
        with self.assertRaises(ValueError):Event.from_row(dict(student='1',part='1',exercise='1',eventType='run',timestamp='bad'))

    def test_response_validation(self):
        d=TrajectoryCoach().observe(ev(0,'text_insert'))
        valid=dict(phase='plan',prompt='What will you check?',reason='First edit',evidence_row=2)
        self.assertEqual(validate_output(valid,d).provider,'openai')
        for key,value in [('phase','evaluate'),('evidence_row',99),('prompt','Your code failed')]:
            bad=dict(valid);bad[key]=value
            with self.assertRaises(ValueError):validate_output(bad,d)

    def test_provider_failure_falls_back(self):
        class Broken:
            def generate(self,*args):raise TimeoutError()
        d=TrajectoryCoach(provider=Broken()).observe(ev(0,'text_insert'))
        self.assertEqual(d.phase,'plan');self.assertEqual(d.provider,'fallback:TimeoutError')

    def test_reflection_boundaries(self):
        c=TrajectoryCoach();c.observe(ev(10))
        with self.assertRaises(ValueError):c.reflect('a','',11)
        with self.assertRaises(ValueError):c.reflect('a','test',9)
        c.reflect('a','x'*2000,11);self.assertEqual(len(c.states['a'].reflection),1000)

    def test_equal_timestamp_preserves_order(self):
        c=TrajectoryCoach(mode='rule');c.observe(ev(0,'text_insert'))
        for _ in range(3):d=c.observe(ev(0))
        self.assertEqual(d.phase,'monitor')

    def test_future_events_do_not_change_prior_decision(self):
        c=TrajectoryCoach();d=c.observe(ev(0,'text_insert'));old=dict(d.evidence)
        c.observe(ev(20,'submit'));self.assertEqual(d.evidence,old)

if __name__=='__main__':unittest.main()
