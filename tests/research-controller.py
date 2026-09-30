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
  (p/'candidates.json').write_text(json.dumps({'candidates':[{'id':'A','family':'mechanism-a','status':'ready_for_development'},{'id':'B','family':'mechanism-b','status':'awaiting_data'}]}))
  for k in ['rule','data','costs','engine']:(self.root/k).write_text(k)
  self.q={'weekly_used':24,'quota_observed_at':m.now().isoformat()}
  self.inputs={k:k for k in ['rule','data','costs','engine']}
 def tearDown(self):self.tmp.cleanup()
 def begin(self):return m.operate(self.root,'begin',candidate='A',**self.q,**self.inputs)
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
 def test_repeated_evidence_and_history_do_not_stop_research(self):
  start=m.now()
  for i in range(8):
   t=start+timedelta(days=i)
   with patch.object(m,'now',return_value=t):m.operate(self.root,'round',weekly_used=1,quota_observed_at=t.isoformat(),evidence='data')
  t=start+timedelta(days=8)
  with patch.object(m,'now',return_value=t):
   self.assertTrue(m.operate(self.root,'preflight',weekly_used=1,quota_observed_at=t.isoformat())['ready'])
   m.operate(self.root,'round',weekly_used=1,quota_observed_at=t.isoformat(),evidence='data')
   with self.assertRaisesRegex(m.Blocked,'already recorded today'):
    m.operate(self.root,'round',weekly_used=1,quota_observed_at=t.isoformat(),evidence='data')

 def test_round_daily_duplicate_and_attempt_daily_cap_remain(self):
  t=m.now()
  with patch.object(m,'now',return_value=t):
   m.operate(self.root,'round',weekly_used=1,quota_observed_at=t.isoformat(),evidence='data')
   with self.assertRaises(m.Blocked):m.operate(self.root,'round',weekly_used=1,quota_observed_at=t.isoformat(),evidence='data')
   for i in range(2):
    (self.root/'rule').write_text('rule-'+str(i))
    ident=self.begin()['active']
    m.operate(self.root,'finish',attempt_id=ident,outcome='blocked',weekly_used=1)
   with self.assertRaisesRegex(m.Blocked,'Daily attempt ceiling'):
    self.begin()

if __name__=='__main__':unittest.main()
