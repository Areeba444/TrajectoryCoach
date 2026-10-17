import unittest,json,os
from unittest.mock import patch
from io import BytesIO
from coach.provider import OpenAIProvider
from coach.core import TrajectoryCoach,Event
from examples import instructor_solutions as s

class ContractTests(unittest.TestCase):
    def test_task_boundaries(self):
        self.assertEqual(s.qualifying_sales([4,-2,7,4],4),15)
        self.assertEqual(s.qualifying_sales([],0),0)
        self.assertEqual(s.qualifying_sales([-3,-1],-2),-1)
        self.assertIsNone(s.safe_average([]));self.assertEqual(s.safe_average([0]),0)
        self.assertEqual(s.safe_average([2,4]),3)
        self.assertEqual(s.within_window([3,1,3,5],1,3),[3,1,3])
        self.assertEqual(s.category_counts(['AI','ai','AI']),{'AI':2,'ai':1})
        self.assertEqual(s.approved_minutes([(30,True),(20,True),(50,False)],30),30)
        self.assertEqual(s.first_qualifying([0,-1,3],0),0)
        self.assertIsNone(s.first_qualifying([1,2],5))

    def test_responses_transport_contract(self):
        response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text',
            'text':json.dumps(dict(phase='plan',prompt='What example will you test?',reason='First edit',evidence_row=2))}]}],
            'usage':{'input_tokens':10,'output_tokens':10}}
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-only','OPENAI_MODEL':'test-model'}):
            provider=OpenAIProvider(max_calls=1)
        c=TrajectoryCoach(provider=provider)
        with patch('urllib.request.urlopen',return_value=BytesIO(json.dumps(response).encode())) as call:
            d=c.observe(Event('a','1','1','text_insert',0,2))
            self.assertEqual(d.provider,'openai')
            req=call.call_args.args[0];body=json.loads(req.data)
            self.assertFalse(body['store']);self.assertTrue(body['text']['format']['strict'])
            self.assertEqual(req.full_url,'https://api.openai.com/v1/responses')
            self.assertNotIn('passed',body['input'])
        with self.assertRaises(RuntimeError):provider.generate(d,{})

    def test_refusal_is_rejected(self):
        response={'status':'completed','output':[{'content':[{'type':'refusal','refusal':'No'}]}]}
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-only','OPENAI_MODEL':'test-model'}):p=OpenAIProvider()
        d=TrajectoryCoach().observe(Event('a','1','1','text_insert',0,2))
        with patch('urllib.request.urlopen',return_value=BytesIO(json.dumps(response).encode())):
            with self.assertRaises(ValueError):p.generate(d,{})

    def test_missing_credentials_fail_before_network(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError):OpenAIProvider()

if __name__=='__main__':unittest.main()
