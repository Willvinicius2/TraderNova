import gzip, json, tempfile, unittest, sys
from pathlib import Path
from decimal import Decimal
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from n21_book_audit import apply_side, coverage, audit, dt

class BookAuditTests(unittest.TestCase):
    def test_zero_quantity_deletes_level(self):
        b={Decimal('100'):Decimal('2'), Decimal('99'):Decimal('1')}; apply_side(b, [["100","0"]]); self.assertNotIn(Decimal('100'),b)
    def test_snapshot_boundary_proves_unknown_coverage(self):
        c=coverage({Decimal('100.45'):Decimal('1')},{Decimal('101'):Decimal('1')},Decimal('100.5'),Decimal('100.45'))
        self.assertFalse(c['complete'])
    def test_out_of_range_diff_does_not_expand_snapshot_coverage(self):
        bids={Decimal('100.45'):Decimal('1')}; asks={Decimal('101'):Decimal('1')}
        apply_side(bids, [["99","3"]])
        self.assertFalse(coverage(bids,asks,Decimal('100.5'),Decimal('100.45'))['complete'])
    def test_timezone_required(self):
        with self.assertRaises(ValueError): dt('2026-09-30T00:00:00')
    def test_sequence_gap_stops_observations(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.gz'; snap={'lastUpdateId':10,'bids':[['100','2'],['99','1']],'asks':[['101','2']]}
            ev={'received_at':'2026-09-30T00:00:01+00:00','payload':{'E':1790726401000,'U':12,'u':12,'b':[],'a':[]}}
            c={'runId':'r','chunk':0,'connectionId':1,'snapshot':{**snap,'received_at':'2026-09-30T00:00:00+00:00'},'events':[ev]}
            p.write_bytes(gzip.compress(json.dumps(c).encode())); self.assertEqual(audit([p])['stats']['sequence_gaps'],1)
    def test_pre_snapshot_event_not_an_observation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.gz'; snap={'lastUpdateId':10,'bids':[['100','2'],['99','1']],'asks':[['101','2']]}
            ev={'received_at':'2026-09-30T00:00:00+00:00','payload':{'E':1790726400000,'U':11,'u':11,'b':[],'a':[]}}
            c={'runId':'r','chunk':0,'connectionId':1,'snapshot':{**snap,'received_at':'2026-09-30T00:00:01+00:00'},'events':[ev]}
            p.write_bytes(gzip.compress(json.dumps(c).encode())); r=audit([p]); self.assertEqual(r['observations'],[]); self.assertEqual(r['stats']['pre_snapshot'],1)
if __name__=='__main__': unittest.main()

