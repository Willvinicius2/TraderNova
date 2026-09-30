"""Read-only causal L2 adapter and N21 coverage audit; stdlib only."""
import argparse, gzip, hashlib, json
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path

BAND = Decimal('0.999')
MAX_CHUNK = 2 * 1024 * 1024

def dt(s):
    value = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('timestamp missing timezone offset')
    return value

def dec(x):
    if isinstance(x, bool): raise ValueError('bool numeric')
    d = Decimal(str(x))
    if not d.is_finite(): raise ValueError('nonfinite')
    return d

def levels(raw):
    out = {}
    for row in raw:
        p, q = dec(row[0]), dec(row[1])
        if p <= 0 or q < 0: raise ValueError('negative/invalid level')
        if q: out[p] = q
        else: out.pop(p, None)
    return out

def apply_side(book, updates):
    for row in updates:
        p, q = dec(row[0]), dec(row[1])
        if p <= 0 or q < 0: raise ValueError('negative/invalid update')
        if q == 0: book.pop(p, None)
        else: book[p] = q

def coverage(bids, asks, mid, snapshot_bid_lower_bound):
    if not bids or not asks: return {'complete':False,'reason':'empty_side','depth':None}
    if snapshot_bid_lower_bound > mid * BAND:
        return {'complete':False,'reason':'snapshot_bid_boundary_inside_band','depth':None}
    return {'complete':True,'reason':None,'depth':sum((q for p,q in bids.items() if mid*BAND <= p <= mid), Decimal(0))}

def audit(paths):
    if len(paths)>5: raise ValueError('max five chunks')
    chunks=[]; hashes=[]; total=0; seen_hash=set(); seen_names=set()
    for p in paths:
        with p.open('rb') as f:
            raw=f.read(10*1024*1024-total+1)
        total+=len(raw)
        if total>10*1024*1024: raise ValueError('compressed input cap exceeded')
        sha=hashlib.sha256(raw).hexdigest()
        if sha in seen_hash or p.name in seen_names: raise ValueError('duplicate input hash or filename')
        seen_hash.add(sha); seen_names.add(p.name)
        hashes.append({'file':p.name,'sha256':sha,'bytes':len(raw)})
        with gzip.GzipFile(fileobj=__import__('io').BytesIO(raw)) as gz:
            data=gz.read(MAX_CHUNK+1)
        if len(data)>MAX_CHUNK: raise ValueError('decompressed chunk exceeds 2 MiB')
        chunks.append(json.loads(data))
    runs={c.get('runId') for c in chunks}
    if len(runs)!=1: raise ValueError('chunks span runs')
    indices=[c.get('chunk') for c in chunks]
    if len(set(indices))!=len(indices): raise ValueError('duplicate chunk index')
    chunks.sort(key=lambda c:c['chunk'])
    events=[]; snaps=[]; run=next(iter(runs)); conn=None
    for c in chunks:
        if c.get('connectionId') is not None:
            if conn is not None and c['connectionId']!=conn: raise ValueError('chunks span connections')
            conn=c['connectionId']
        if c.get('snapshot'): snaps.append(c['snapshot'])
        events.extend(c.get('events', []))
    if len(snaps)!=1: raise ValueError('expected exactly one unambiguous snapshot')
    snap=snaps[0]; snap_at=dt(snap['received_at'])
    bids=levels(snap['bids']); asks=levels(snap['asks']); snapshot_bid_lower_bound=min(bids) if bids else None
    if snapshot_bid_lower_bound is None: raise ValueError('snapshot has no known bids')
    cursor=snap['lastUpdateId']
    if not isinstance(cursor,int) or isinstance(cursor,bool) or cursor<0: raise ValueError('invalid snapshot sequence')
    observations=[]
    stats={'clock_future':0,'clock_stale':0,'clock_missing':0,'invalid_book':0,'crossed':0,'pre_snapshot':0,'sequence_gaps':0,'duplicates':0}
    ages=[]; first=[]; stopped=False
    for wrapped in events:
        if stopped: break
        payload=wrapped.get('payload',wrapped)
        try: received=dt(wrapped['received_at'])
        except (KeyError,TypeError,ValueError): stats['clock_missing']+=1; stopped=True; continue
        U,u=payload.get('U'),payload.get('u')
        if not isinstance(U,int) or isinstance(U,bool) or not isinstance(u,int) or isinstance(u,bool) or U<0 or u<U:
            stats['invalid_book']+=1; stopped=True; continue
        if u<=cursor: stats['duplicates']+=1; continue
        if U>cursor+1: stats['sequence_gaps']+=1; stopped=True; continue
        if not isinstance(payload.get('E'),int) or isinstance(payload.get('E'),bool):
            stats['clock_missing']+=1; stopped=True; continue
        try: event_at=datetime.fromtimestamp(payload['E']/1000,tz=timezone.utc)
        except (ValueError,OverflowError,OSError): stats['clock_missing']+=1; stopped=True; continue
        age=(received.astimezone(timezone.utc)-event_at).total_seconds(); ages.append(age)
        if len(first)<5: first.append({'received_at':received.isoformat(),'event_time_ms':payload['E'],'age_s':age})
        try:
            # Validate complete event before mutating either side; malformed input ends this connection.
            bupdates=payload.get('b',payload.get('bids')); aupdates=payload.get('a',payload.get('asks'))
            if not isinstance(bupdates,list) or not isinstance(aupdates,list): raise ValueError('missing update arrays')
            nb,na=bids.copy(),asks.copy(); apply_side(nb,bupdates); apply_side(na,aupdates)
        except (ValueError,KeyError,InvalidOperation,TypeError): stats['invalid_book']+=1; stopped=True; continue
        bids,asks,cursor=nb,na,u
        if age<0: stats['clock_future']+=1; continue
        if age>1: stats['clock_stale']+=1; continue
        if received<snap_at: stats['pre_snapshot']+=1; continue
        if not bids or not asks: stats['invalid_book']+=1; stopped=True; continue
        bid,ask=max(bids),min(asks)
        if bid>=ask: stats['crossed']+=1; stopped=True; continue
        mid=(bid+ask)/2; cov=coverage(bids,asks,mid,snapshot_bid_lower_bound)
        observations.append({'received_at':received.isoformat(),'event_time_ms':payload['E'],'event_age_s':age,'sequence':{'U':U,'u':u},'top_bid':[str(bid),str(bids[bid])],'top_ask':[str(ask),str(asks[ask])],'mid':str(mid),'band_10bp_bid_coverage':{'complete':cov['complete'],'reason':cov['reason'],'depth':str(cov['depth']) if cov['depth'] is not None else None},'runId':run,'connectionId':conn})
    return {'schema':'n21-book-audit-v1','runId':run,'connectionId':conn,'input_sha256':hashes,'chunks':len(chunks),'compressed_bytes':total,'observations':observations,'stats':stats,'event_age_s':{'min':min(ages) if ages else None,'max':max(ages) if ages else None,'first_samples':first},'validated':False}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('files',nargs='+'); ap.add_argument('--output'); a=ap.parse_args()
    result=audit([Path(x) for x in a.files]); text=json.dumps(result,indent=2)
    if a.output: Path(a.output).write_text(text+'\n',encoding='utf-8')
    else: print(text)
if __name__=='__main__': main()
