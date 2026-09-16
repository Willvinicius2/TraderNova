import sys,unittest,datetime as dt
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from import_histdata import parse_line,aggregate,FIELDS

class HistDataTests(unittest.TestCase):
    def test_fixed_est_in_winter_and_summer(self):
        for day in ['20240115','20240715']:
            record=parse_line(f'{day} 100000;1;1.2;.9;1.1;0')
            utc=dt.datetime.fromtimestamp(record[0],dt.timezone.utc)
            self.assertEqual(utc.hour,15)
    def test_ohlc_and_unknown_spread(self):
        record=parse_line('20240115 100000;1;1.2;.9;1.1;0')
        self.assertEqual(record[1:],(1.,1.2,.9,1.1,0))
        for row in ['20240115 100001;1;1.2;.9;1.1;0','20240115 100000;1;.8;.9;1.1;0','20240115 100000;1;nan;.9;1.1;0']:
            with self.assertRaises(ValueError):parse_line(row)
    def test_aggregation_preserves_extremes_and_drops_incomplete(self):
        start=parse_line('20240115 100000;1;1.2;.9;1.1;0')[0]
        minutes=np.array([(start+i*60,1+i/1000,1.2+i/1000,.9+i/1000,1.1+i/1000,0) for i in range(120)],dtype=FIELDS)
        complete,quality=aggregate(minutes,60)
        self.assertEqual(quality,{'groups':2,'complete':2,'incomplete':0})
        self.assertEqual(complete['open'][0],1.)
        self.assertEqual(complete['high'][0],1.259)
        self.assertEqual(complete['low'][0],.9)
        self.assertAlmostEqual(complete['close'][0],1.159)
        damaged=np.delete(minutes,20)
        filtered,quality=aggregate(damaged,60)
        self.assertEqual(quality['incomplete'],1)
        self.assertEqual(list(filtered['time']),[start+3600])
        with self.assertRaises(ValueError):aggregate(np.r_[minutes[:10],minutes[9:]],60)

if __name__=='__main__':unittest.main(verbosity=2)
