import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from goal_five_signals import n16_liquidation_reclaim,n17_etf_flow,n18_exchange_deposit,n19_cross_venue,n20_cpi_surprise

def ts(t): return t if isinstance(t,str) else t.isoformat()
NOW=datetime(2026,1,2,12,tzinfo=timezone.utc)
def f(v,end=NOW,pub=None):
    pub=pub or end
    return {"value":v,"published_at":ts(pub),"received_at":ts(pub),"feature_end":ts(end)}
def meta(end): return {"published_at":ts(end-timedelta(seconds=2)),"received_at":ts(end-timedelta(seconds=1)),"feature_end":ts(end)}

class Tests(unittest.TestCase):
    def snap(self,t):
        return {"published_at":ts(t),"received_at":ts(t),"feature_end":ts(t),"cheap_quote_at":ts(t),"rich_quote_at":ts(t),"cheap_ask":100,"rich_bid":101,"entry_cost_pct":.1,"exit_cost_pct":.1,"carry_cost_pct":.1,
                "quantity":1,"cheap_depth":2,"rich_depth":2,"cheap_venue":"a","rich_venue":"b","shortAvailable":True,"carryCostsKnown":True}

    def test_five_synthetic_signals(self):
        bar=NOW-timedelta(minutes=5)
        venues=[{"venue_id":x,"feed_complete":True,"liq_long_usd":100,"liq_short_usd":0,**meta(bar)} for x in ("a","b")]
        d16={"decision_at":ts(NOW),"prior_high":f(110,bar-timedelta(minutes=5)),"prior_low":f(90,bar-timedelta(minutes=5)),"close":f(95,bar),"signal_high":f(105,bar),"signal_low":f(89,bar),"atr14_prior":f(3,bar-timedelta(minutes=5)),"venues":venues,"history_long":[1]*30,"history_short":[1]*30,"history_meta":meta(bar-timedelta(minutes=1))}
        d17={"decision_at":ts(NOW),"flow":f(10),"ema20":f(90),"close":f(100),"atr14_prior":f(2),"flow_history":[-1,1]*30,"history_meta":meta(NOW-timedelta(days=1))}
        d18={"decision_at":ts(NOW),"deposit":f(10),"close":f(80),"atr14_prior":f(2),"deposit_history":[0,1]*182+[0],"history_meta":meta(NOW-timedelta(days=1)),"prior_lows":f([90]*20,NOW-timedelta(days=1))}
        d19={"decision_at":ts(NOW),"snapshots":[self.snap(NOW-timedelta(seconds=61)),self.snap(NOW-timedelta(milliseconds=500))]}
        rel=NOW-timedelta(minutes=5)
        d20={"decision_at":ts(NOW),"release_at":ts(rel),"consensus_archived_at":ts(rel-timedelta(seconds=10)),"actual":f(3,NOW,rel),"consensus":f(0,rel-timedelta(seconds=5),rel-timedelta(seconds=10)),"consensus_meta":meta(rel-timedelta(seconds=5)),"pre_high":f(1.1,rel),"pre_low":f(1.0,rel),"close":f(.99,NOW),"atr14_prior":f(.01,rel-timedelta(minutes=5)),"surprise_history":[-1,1]*30,"history_meta":meta(rel-timedelta(minutes=1))}
        got=[n16_liquidation_reclaim(d16),n17_etf_flow(d17),n18_exchange_deposit(d18),n19_cross_venue(d19),n20_cpi_surprise(d20)]
        self.assertTrue(all(x and x["validated"] is False and x["decision_at"]==x["entry_after"] for x in got))
        self.assertEqual(got[4]["direction"],"short EURUSD")

    def test_quality_cost_history_and_future_rejections(self):
        d={"decision_at":ts(NOW),"flow":f(10),"ema20":f(1),"close":f(2),"atr14_prior":f(1),"flow_history":[-1,1]*30,"history_meta":meta(NOW-timedelta(days=1))}
        self.assertIsNotNone(n17_etf_flow(d))
        d["flow"]=f(True); self.assertIsNone(n17_etf_flow(d))
        d["flow"]=f(10,"2026-01-02T12:00:01+00:00"); self.assertIsNone(n17_etf_flow(d))
        d["flow"]=f(10); d["history_meta"]=meta(NOW); self.assertIsNone(n17_etf_flow(d))
        self.assertIsNone(n17_etf_flow({"decision_at":"2026-01-02T12:00:00","flow":f(10),"ema20":f(1),"close":f(2),"atr14_prior":f(1),"flow_history":[-1,1]*30,"history_meta":meta(NOW)}))
        bad=self.snap(NOW-timedelta(seconds=61)); bad["entry_cost_pct"]=-.1
        self.assertIsNone(n19_cross_venue({"decision_at":ts(NOW),"snapshots":[bad,self.snap(NOW-timedelta(milliseconds=500))]}))

    def test_n16_overlap_rejected_and_n19_requires_real_two_snapshots(self):
        bar=NOW-timedelta(minutes=5); venues=[{"venue_id":x,"feed_complete":True,"liq_long_usd":100,"liq_short_usd":100,**meta(bar)} for x in ("a","b")]
        d={"decision_at":ts(NOW),"prior_high":f(100,bar-timedelta(minutes=5)),"prior_low":f(90,bar-timedelta(minutes=5)),"close":f(95,bar),"signal_high":f(101,bar),"signal_low":f(89,bar),"atr14_prior":f(10,bar-timedelta(minutes=5)),"venues":venues,"history_long":[1]*30,"history_short":[1]*30,"history_meta":meta(bar-timedelta(minutes=1))}
        self.assertIsNone(n16_liquidation_reclaim(d))
        x=self.snap(NOW-timedelta(seconds=61)); y=self.snap(NOW-timedelta(milliseconds=500)); y["cheap_venue"]="c"
        self.assertIsNone(n19_cross_venue({"decision_at":ts(NOW),"snapshots":[x,y]}))

if __name__=="__main__": unittest.main()
