"""Regras puras de sinal sobre features fornecidas pelo chamador.

Cada feature escalar usa {value,published_at,received_at,feature_end}; timestamps
ISO-8601 devem ter fuso. Históricos usam arrays finitos e history_meta com os mesmos
timestamps. Sem conectores, cálculo de features, fills, execução ou PnL.
"""
from datetime import datetime, timedelta
import math
from statistics import mean, pstdev

def _time(x):
    if not isinstance(x,str): raise ValueError
    t=datetime.fromisoformat(x.replace("Z","+00:00"))
    if t.tzinfo is None or t.utcoffset() is None: raise ValueError
    return t

def _meta(m,limit,strict=False):
    try:
        p,r,e=(_time(m[k]) for k in ("published_at","received_at","feature_end"))
        return r>=p and ((p<limit and r<limit and e<limit) if strict else (p<=limit and r<=limit and e<=limit))
    except (KeyError,TypeError,ValueError,OverflowError): return False

def _feature(d,k,positive=False,limit=None):
    try:
        f=d[k]; v=f["value"]; now=_time(limit or d["decision_at"])
        t=(_time(f["published_at"]),_time(f["received_at"]),_time(f["feature_end"]))
        return (isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
                and (not positive or v>0) and t[1]>=t[0] and all(x<=now for x in t))
    except (KeyError,TypeError,ValueError,OverflowError): return False

def _arr(x,n,nonnegative=False,positive=False):
    return (isinstance(x,(list,tuple)) and len(x)>=n and all(isinstance(v,(int,float)) and not isinstance(v,bool)
            and math.isfinite(v) and (not nonnegative or v>=0) and (not positive or v>0) for v in x))

def _base(d,keys,positive=()):
    try: _time(d["decision_at"])
    except (KeyError,TypeError,ValueError,OverflowError): return False
    return all(_feature(d,k,k in positive) for k in keys)

def _sig(d,family,direction,horizon,stop,entry=None):
    return {"family":family,"direction":direction,"decision_at":d["decision_at"],
            "entry_after":d["decision_at"],"entry_rule":entry or "após decision_at",
            "horizon":horizon,"stop":stop,"validated":False}

def n16_liquidation_reclaim(d):
    """Barras 5min; 30 totais diários do mesmo slot; feed venues completos."""
    keys=("prior_high","prior_low","close","signal_high","signal_low","atr14_prior")
    if not _base(d,keys,keys) or not _meta(d.get("history_meta",{}),_time(d["signal_low"]["feature_end"]),True): return None
    try:
        bar=_time(d["signal_low"]["feature_end"])
        if any(_time(d[k]["feature_end"])>=bar for k in ("prior_high","prior_low","atr14_prior")): return None
        if _time(d["signal_high"]["feature_end"])!=bar or _time(d["close"]["feature_end"])!=bar: return None
        if not (d["signal_high"]["value"]>=d["close"]["value"]>=d["signal_low"]["value"] and d["signal_high"]["value"]>d["signal_low"]["value"]): return None
    except (KeyError,TypeError,ValueError,OverflowError): return None
    try:
        vs=d["venues"]
        if not isinstance(vs,list) or not all(isinstance(v,dict) for v in vs): return None
        if len(vs)<2 or any(not isinstance(v.get("venue_id"),str) or not v["venue_id"] for v in vs) or len({v["venue_id"] for v in vs})!=len(vs): return None
        if any(v.get("feed_complete") is not True or not _meta(v,_time(d["decision_at"])) or _time(v["feature_end"])!=bar or not _arr([v["liq_long_usd"],v["liq_short_usd"]],2,True) for v in vs): return None
        hl,hs=d["history_long"],d["history_short"]
        if not _arr(hl,30,True) or not _arr(hs,30,True): return None
        total_l=sum(v["liq_long_usd"] for v in vs); total_s=sum(v["liq_short_usd"] for v in vs)
        # Nearest-rank empirical p99 across 30 prior daily observations.
        tl=sorted(hl[-30:])[math.ceil(.99*30)-1]; ts=sorted(hs[-30:])[math.ceil(.99*30)-1]
        lo=d["prior_low"]["value"]; hi=d["prior_high"]["value"]; c=d["close"]["value"]
        atr=d["atr14_prior"]["value"]; long_ok=total_l>tl and d["signal_low"]["value"]<lo and lo<c<hi
        short_ok=total_s>ts and d["signal_high"]["value"]>hi and lo<c<hi
        if long_ok==short_ok: return None
        direction="long" if long_ok else "short"; px=d["signal_low"]["value"] if long_ok else d["signal_high"]["value"]
        if abs(c-px)>2*atr: return None
        return _sig(d,"N16",direction,"60 minutos",{"stop_price":px,"atr_guard_distance_max":2*atr})
    except (KeyError,TypeError,ValueError,IndexError): return None

def n17_etf_flow(d):
    if not _base(d,("flow","ema20","close","atr14_prior"),("ema20","close","atr14_prior")): return None
    try:
        h=d["flow_history"]
        if not _arr(h,60) or not _meta(d["history_meta"],_time(d["flow"]["feature_end"]),True): return None
        mu=mean(h[-60:]); sd=pstdev(h[-60:]); z=(d["flow"]["value"]-mu)/sd if sd else 0
        c=d["close"]["value"]; e=d["ema20"]["value"]
        if z>=2 and c>e: direction="long"
        elif z<=-2 and c<e: direction="short"
        else: return None
        return _sig(d,"N17",direction,"120 horas",{"distance":d["atr14_prior"]["value"],"unit":"preço"})
    except (KeyError,TypeError,ValueError,OverflowError): return None

def n18_exchange_deposit(d):
    if not _base(d,("deposit","close","atr14_prior"),("deposit","close","atr14_prior")): return None
    try:
        h=d["deposit_history"]; lf=d["prior_lows"]
        if not _arr(h,365,True) or not _meta(d["history_meta"],_time(d["deposit"]["feature_end"]),True): return None
        if not isinstance(lf,dict) or not _meta(lf,_time(d["decision_at"])): return None
        lows=lf["value"]
        if not _arr(lows,20,positive=True) or not _meta(lf,_time(d["deposit"]["feature_end"]),True): return None
        mu=mean(h[-365:]); sd=pstdev(h[-365:]); z=(d["deposit"]["value"]-mu)/sd if sd else 0
        if z>=2 and d["close"]["value"]<min(lows[-20:]):
            return _sig(d,"N18","short","72 horas",{"distance":d["atr14_prior"]["value"],"unit":"preço"})
    except (KeyError,TypeError,ValueError,OverflowError): pass
    return None

def n19_cross_venue(d):
    """Spread executável de livros; curto só se disponibilidade/carry/depth provados."""
    try:
        _time(d["decision_at"]); ss=d["snapshots"]
        if not isinstance(ss,list) or len(ss)!=2 or not all(isinstance(s,dict) for s in ss): return None
        parsed=[]
        for s in ss:
            for k in ("cheap_ask","rich_bid","entry_cost_pct","exit_cost_pct","carry_cost_pct","quantity","cheap_depth","rich_depth"):
                if not isinstance(s.get(k),(int,float)) or isinstance(s[k],bool) or not math.isfinite(s[k]): return None
            if any(s[k]<0 for k in ("entry_cost_pct","exit_cost_pct","carry_cost_pct")) or min(s["cheap_ask"],s["rich_bid"],s["quantity"],s["cheap_depth"],s["rich_depth"])<=0: return None
            if s["shortAvailable"] is not True or s["carryCostsKnown"] is not True: return None
            if s["cheap_depth"]<s["quantity"] or s["rich_depth"]<s["quantity"]: return None
            if not _meta(s,_time(d["decision_at"])): return None
            tc,tr=_time(s["cheap_quote_at"]),_time(s["rich_quote_at"]); snap_end=_time(s["feature_end"])
            if abs((tc-tr).total_seconds())>1 or max(tc,tr)>snap_end or min((snap_end-tc).total_seconds(),(snap_end-tr).total_seconds())<0 or max((snap_end-tc).total_seconds(),(snap_end-tr).total_seconds())>1: return None
            parsed.append((_time(s["feature_end"]),s,(s["rich_bid"]-s["cheap_ask"])/s["cheap_ask"]*100-s["entry_cost_pct"]-s["exit_cost_pct"]-s["carry_cost_pct"]))
        parsed.sort(key=lambda x:x[0]); (t1,a,_),(t2,b,spread)=parsed
        if (t2-t1).total_seconds()<60 or (_time(d["decision_at"])-t2).total_seconds()>1: return None
        if not all(isinstance(b[k],str) and b[k] for k in ("cheap_venue","rich_venue")): return None
        if a["cheap_venue"]!=b["cheap_venue"] or a["rich_venue"]!=b["rich_venue"] or a["quantity"]!=b["quantity"] or a["cheap_venue"]==a["rich_venue"]: return None
        # Require each observation's own net spread threshold.
        if any(x[2]<.30 for x in parsed): return None
        return {"family":"N19","direction":"long_cheap_short_rich","decision_at":d["decision_at"],"entry_after":d["decision_at"],
                "legs":[{"venue":b["cheap_venue"],"side":"long","price":b["cheap_ask"],"quantity":b["quantity"]},{"venue":b["rich_venue"],"side":"short","price":b["rich_bid"],"quantity":b["quantity"]}],
                "horizon":"15 minutos","stop_net_spread_pct":2*spread,"validated":False}
    except (KeyError,TypeError,ValueError,OverflowError): return None

def n20_cpi_surprise(d):
    try: release=_time(d["release_at"])
    except (KeyError,TypeError,ValueError,OverflowError): return None
    keys=("actual","consensus","pre_high","pre_low","close","atr14_prior")
    if not _base(d,keys,("pre_high","pre_low","close","atr14_prior")) or not _feature(d,"atr14_prior",True,d.get("release_at")): return None
    try:
        cons=d["consensus"]
        if not _meta(d["consensus_meta"],release,True) or not _meta(d["history_meta"],release,True): return None
        if _time(d["consensus_archived_at"])>=release or _time(d["actual"]["published_at"])<release: return None
        if _time(d["decision_at"])<release or _time(d["close"]["feature_end"])!=release+timedelta(minutes=5): return None
        if _time(d["pre_high"]["feature_end"])>release or _time(d["pre_low"]["feature_end"])>release: return None
        elapsed=(_time(d["decision_at"])-release).total_seconds()
        if elapsed<300 or elapsed>=600: return None
        h=d["surprise_history"]
        if not _arr(h,60) or _time(cons["published_at"])>=release or _time(cons["received_at"])>=release or _time(d["consensus_meta"]["feature_end"])>=release: return None
        mu=mean(h[-60:]); sd=pstdev(h[-60:]); z=(d["actual"]["value"]-cons["value"]-mu)/sd if sd else 0
        c=d["close"]["value"]; hi=d["pre_high"]["value"]; lo=d["pre_low"]["value"]
        if z>=1 and c<lo: direction="short EURUSD"
        elif z<=-1 and c>hi: direction="long EURUSD"
        else: return None
        return _sig(d,"N20",direction,"4 horas",{"distance":d["atr14_prior"]["value"],"unit":"preço"},"após fechamento da barra 5min pós-release")
    except (KeyError,TypeError,ValueError,OverflowError): return None
