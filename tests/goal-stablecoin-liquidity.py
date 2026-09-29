"""N15 synthetic-only checks; no historical strategy values."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('stable',ROOT/'scripts/run-goal-stablecoin-liquidity.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class StableTests(unittest.TestCase):
    def rows(self):
        return [{'time':i*m.DAY,'usdt_supply':str(100+i),'usdc_supply':'100',
                 'usdt_price':'1','usdc_price':'1','received_at':(i+1)*m.DAY} for i in range(8)]

    def test_rule_direction_timing_peg_and_supply(self):
        rows=self.rows(); signals=m.generate(rows)
        self.assertEqual(len(signals),1)
        signal=signals[10*m.DAY]
        self.assertEqual(signal['direction'],1)
        self.assertEqual(signal['signal_close_time'],10*m.DAY+m.HOUR)
        self.assertEqual(signal['feature_end'],8*m.DAY)
        self.assertEqual((signal['stop_pct'],signal['hold_hours']),(.03,72))
        self.assertFalse(m.generate([{**r,'usdt_supply':'100'} for r in rows]))
        self.assertFalse(m.generate(rows[:-1]+[{**rows[-1],'usdc_price':'.98'}]))
        for edge in ('.99','1.01'):
            self.assertTrue(m.generate(rows[:-1]+[{**rows[-1],'usdc_price':edge}]))

    def test_missing_duplicate_late_and_future(self):
        rows=self.rows(); before=m.generate(rows)
        self.assertFalse(m.generate(rows[:3]+rows[4:]))
        self.assertFalse(m.generate([{k:v for k,v in r.items() if k!='received_at'} for r in rows]))
        self.assertFalse(m.generate([{**rows[0],'received_at':3*m.DAY+1}]+rows[1:]))
        with self.assertRaises(ValueError): m.generate(rows+[rows[0]])
        after=m.generate(rows+[{**rows[-1],'time':8*m.DAY,'usdt_supply':'1000000','received_at':9*m.DAY}])
        self.assertEqual({t:r for t,r in after.items() if t in before},before)

    def test_both_source_assets_required_and_reconciled(self):
        data={'data':[{'asset':a,'time':datetime.fromtimestamp(t,timezone.utc).isoformat(),
                       'SplyCur':'100.25','PriceUSD':'1'}
                      for a in ('usdt','usdc') for t in range(m.SOURCE_START,m.END,m.DAY)]}
        rows=m.normalize(data)
        self.assertEqual(len(rows),(m.END-m.SOURCE_START)//m.DAY)
        self.assertEqual(rows[0]['usdc_supply'],'100.25')
        for altered in ({'data':data['data'][:-1]}, {'data':data['data']+[data['data'][0]]},
                        {**data,'next_page_url':'unfetched'}):
            with self.assertRaises(ValueError): m.normalize(altered)

    def test_sample_gate_prevents_pnl(self):
        with patch.object(m,'inputs',return_value=([],{},{},{},{})), \
                patch.object(m,'hashes',return_value={}), patch.object(m.io,'sha',return_value='frozen'), \
                patch.object(m.io,'read',side_effect=[{'hashes':{},'marketAudit':{}},{}]), \
                patch.object(m,'simulate') as simulate:
            with self.assertRaisesRegex(ValueError,'sample'): m.run('development')
            simulate.assert_not_called()


if __name__=='__main__': unittest.main()
