import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from datetime import timedelta
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('controller',Path(__file__).resolve().parents[1]/'scripts/research_controller.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  p=self.root/'research/validation';p.mkdir(parents=True)
  (p/'candidates.json').write_text(json.dumps({'candidates':[{'id':'A','family':'mechanism-a','status':'ready_for_development'},{'id':'B','family':'mechanism-b','status':'awaiting_data'},{'id':'C','family':'mechanism-c','status':'ready_for_development'},{'id':'D','family':'mechanism-d','status':'ready_for_development'}]}))
  for k in ['rule','data','costs','engine']:(self.root/k).write_text(k)
  self.q={'weekly_used':24,'quota_observed_at':m.now().isoformat()}
  self.inputs={k:k for k in ['rule','data','costs','engine']}
 def tearDown(self):self.tmp.cleanup()
 def begin(self,candidate='A'):return m.operate(self.root,'begin',candidate=candidate,**self.q,**self.inputs)
 def test_quota_stop_and_missing_data(self):
  for value in [35,float('nan'),-1,True]:
   with self.assertRaises(m.Blocked):m.operate(self.root,'preflight',weekly_used=value,quota_observed_at=m.now().isoformat())
  with self.assertRaises(m.Blocked):m.operate(self.root,'preflight',weekly_used=1,quota_observed_at=(m.now()-timedelta(minutes=6)).isoformat())
  with self.assertRaises(m.Blocked):m.operate(self.root,'begin',candidate='B',**self.q,**self.inputs)
  (self.root/'research/cache/validation/STOP').touch()
  with self.assertRaises(m.Blocked):self.begin()
 def test_lock_never_signals_windows_process(self):
  cache=self.root/'research/cache/validation';cache.mkdir(parents=True)
  lock=cache/'controller.lock';lock.write_text(str(os.getpid()))
  with patch.object(os,'kill',side_effect=AssertionError('Never send a signal to probe a Windows PID')):
   with self.assertRaises(m.Blocked):m.operate(self.root,'status')
  self.assertTrue(lock.exists())
 def test_continuous_capture_prevents_development_overlap(self):
  cache=self.root/'research/cache/validation';cache.mkdir(parents=True)
  lock=cache/'depth-worker.lock';lock.write_text('owner metadata')
  with self.assertRaisesRegex(m.Blocked,'Continuous capture is active'):self.begin()
  self.assertIsNone(m.operate(self.root,'status')['active'])
 def test_concurrency_duplicate_and_no_approval(self):
  state=self.begin();ident=state['active']
  with self.assertRaises(m.Blocked):self.begin()
  with self.assertRaises(m.Blocked):m.operate(self.root,'finish',attempt_id=ident,outcome='approved',weekly_used=24)
  m.operate(self.root,'finish',attempt_id=ident,outcome='rejected',weekly_used=24)
  with self.assertRaises(m.Blocked):self.begin()
  self.assertEqual(m.operate(self.root,'status')['validatedCount'],0)
 def test_paths_timeout_delta_and_daily_cap(self):
  with self.assertRaises(m.Blocked):m.file_hash(self.root,'../outside')
  with self.assertRaises(m.Blocked):m.file_hash(self.root,'absent')
  ident=self.begin()['active'];future=m.now()+timedelta(seconds=181)
  with patch.object(m,'now',return_value=future):m.operate(self.root,'finish',attempt_id=ident,outcome='candidate',weekly_used=26)
  history=m.read(self.root/'research/cache/validation/controller-state.json')
  self.assertEqual(history['attempts'][0]['outcome'],'blocked')
  with self.assertRaises(m.Blocked):m.operate(self.root,'preflight',**self.q)
 def test_history_does_not_stop_research_with_new_evidence(self):
  start=m.now()
  for i in range(8):
   t=start+timedelta(days=i)
   evidence='data' if i==0 else 'engine'
   with patch.object(m,'now',return_value=t):
    if i:
     (self.root/'engine').write_text('new evidence '+str(i))
     evidence='engine'
    m.operate(self.root,'round',weekly_used=1,quota_observed_at=t.isoformat(),evidence=evidence)
  t=start+timedelta(days=8)
  with patch.object(m,'now',return_value=t):
   self.assertTrue(m.operate(self.root,'preflight',weekly_used=1,quota_observed_at=t.isoformat())['ready'])
   (self.root/'data').write_text('latest capture')
   m.operate(self.root,'round',weekly_used=1,quota_observed_at=t.isoformat(),evidence='data')
   with self.assertRaisesRegex(m.Blocked,'Identical research evidence'):
    m.operate(self.root,'round',weekly_used=1,quota_observed_at=t.isoformat(),evidence='data')

 def test_multiple_rounds_same_day_new_evidence_and_duplicate_blocked(self):
  t=m.now()
  with patch.object(m,'now',return_value=t):
   m.operate(self.root,'round',weekly_used=1,quota_observed_at=t.isoformat(),evidence='data')
   (self.root/'engine').write_text('new capture')
   m.operate(self.root,'round',weekly_used=1,quota_observed_at=t.isoformat(),evidence='engine')
   with self.assertRaisesRegex(m.Blocked,'Identical research evidence'):
    m.operate(self.root,'round',weekly_used=1,quota_observed_at=t.isoformat(),evidence='data')
   state=m.read(self.root/'research/cache/validation/controller-state.json')
   self.assertEqual(len(state['rounds']),2)
   self.assertNotEqual(state['rounds'][0]['evidenceHash'],state['rounds'][1]['evidenceHash'])

 def test_three_distinct_attempts_same_day_after_blocked(self):
  t=m.now()
  with patch.object(m,'now',return_value=t):
   for candidate in ('A','C','D'):
    (self.root/'rule').write_text('rule-'+candidate)
    ident=self.begin(candidate)['active']
    m.operate(self.root,'finish',attempt_id=ident,outcome='blocked',weekly_used=1)
   state=m.read(self.root/'research/cache/validation/controller-state.json')
   self.assertEqual(len(state['attempts']),3)
   self.assertEqual({a['mechanism'] for a in state['attempts']},{'mechanism-a','mechanism-c','mechanism-d'})
   self.assertEqual(len({a['hashes']['rule'] for a in state['attempts']}),3)
   self.assertTrue(m.operate(self.root,'preflight',**self.q)['ready'])

if __name__=='__main__':unittest.main()
