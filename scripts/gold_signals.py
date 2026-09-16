"""Fixed research hypotheses on closed broker candles; no MT5 or order calls."""
import csv
import numpy as np

DTYPE=[('time','i8'),('open','f8'),('high','f8'),('low','f8'),('close','f8'),('spread','i8')]

def read_bars(path):
    with open(path,encoding='utf-8',newline='') as f:
        return np.array([tuple(int(r[k]) if kind=='i8' else float(r[k]) for k,kind in DTYPE) for r in csv.DictReader(f)],dtype=DTYPE)

def ema(values,period):
    out=np.full(len(values),np.nan)
    if len(values)>=period:
        out[period-1]=np.mean(values[:period]);alpha=2/(period+1)
        for i in range(period,len(values)):out[i]=alpha*values[i]+(1-alpha)*out[i-1]
    return out

def wilder(values,period):
    out=np.full(len(values),np.nan)
    if len(values)>=period:
        out[period-1]=np.mean(values[:period])
        for i in range(period,len(values)):out[i]=(out[i-1]*(period-1)+values[i])/period
    return out

def atr(bars):
    prev=np.r_[bars['close'][0],bars['close'][:-1]]
    return wilder(np.maximum(bars['high']-bars['low'],np.maximum(abs(bars['high']-prev),abs(bars['low']-prev))),14)

def rsi(bars):
    delta=np.diff(bars['close']);gain=wilder(np.maximum(delta,0),14);loss=wilder(np.maximum(-delta,0),14)
    values=np.full(len(delta),np.nan)
    for i in range(13,len(delta)):
        values[i]=50 if gain[i]==0 and loss[i]==0 else 100 if loss[i]==0 else 100-100/(1+gain[i]/loss[i])
    return np.r_[np.nan,values]

def make_signals(bars,h1,family,preset):
    n=len(bars);output=[None]*n;c=bars['close'];a=atr(bars);e20=ema(c,20);e50=ema(c,50)
    slow=ema(h1['close'],200);fast=ema(h1['close'],50);ha=atr(h1)
    # Only H1 bars whose nominal close is known at the M15 signal close.
    hi=np.searchsorted(h1['time']+3600,bars['time']+900,side='right')-1
    days=bars['time']//86400;day_indices={int(d):np.flatnonzero(days==d) for d in np.unique(days)}
    ordered=sorted(day_indices);previous_day={ordered[i]:ordered[i-1] for i in range(1,len(ordered))}
    ranges={};previous={}
    if family=='G2':
        for day,idx in day_indices.items():
            group=idx[(bars['time'][idx]%86400>=8*3600)&(bars['time'][idx]%86400<8*3600+preset*60)]
            if len(group)==preset//15 and np.all(np.diff(bars['time'][group])==900):ranges[day]=(float(max(bars['high'][group])),float(min(bars['low'][group])))
    if family=='G4':
        for day,prior in previous_day.items():
            idx=day_indices[prior]
            # Only complete observed 23-hour sessions. Short holiday sessions
            # and unexplained intraday gaps cannot define a trusted daily edge.
            complete=len(idx)==92 and int(bars['time'][idx[0]]%86400) in [0,3600] and np.all(np.diff(bars['time'][idx])==900)
            if complete:previous[day]=(float(max(bars['high'][idx])),float(min(bars['low'][idx])))
    mean=np.full(n,np.nan);std=np.full(n,np.nan)
    if family=='G3':
        for i in range(19,n):mean[i]=np.mean(c[i-19:i+1]);std[i]=np.std(c[i-19:i+1],ddof=0)
    lower=mean-preset*std;upper=mean+preset*std
    strength=rsi(bars) if family=='G5' else None
    last_low=None;last_high=None;used_levels=set()
    for i in range(30,n):
        b=bars[i];day=int(days[i]);seconds=int(b['time']%86400);h=int(hi[i]);direction=0;stop=0;target=None;hold=16;reward=2;max_per_day=2
        # Pivots are learned at confirmation even outside permitted entry hours.
        low_pair=high_pair=None
        if family=='G5' and i>=2*preset:
            pivot=i-preset;left=bars[pivot-preset:pivot];right=bars[pivot+1:i+1]
            if b['time']-bars[i-2*preset]['time']==2*preset*900:
                if bars[pivot]['low']<min(min(left['low']),min(right['low'])):
                    low_pair=(last_low,pivot);last_low=pivot
                if bars[pivot]['high']>max(max(left['high']),max(right['high'])):
                    high_pair=(last_high,pivot);last_high=pivot
        entry_seconds=int((b['time']+900)%86400)
        if not (8*3600<=entry_seconds<20*3600) or b['time']-bars[i-1]['time']!=900 or not np.isfinite(a[i]) or a[i]<=0:continue
        if family=='G1':
            if h<202 or b['time']+900-(h1['time'][h]+3600)>3600:continue
            trend=1 if h1['close'][h]>slow[h] and fast[h]>slow[h] and fast[h]>fast[h-3] else -1 if h1['close'][h]<slow[h] and fast[h]<slow[h] and fast[h]<fast[h-3] else 0
            reference=e20 if preset==20 else e50
            if trend==1 and c[i-1]<=reference[i-1] and c[i]>reference[i] and c[i]>b['open']:direction=1
            if trend==-1 and c[i-1]>=reference[i-1] and c[i]<reference[i] and c[i]<b['open']:direction=-1
            stop=min(b['low'],bars[i-1]['low'])-.25*a[i] if direction==1 else max(b['high'],bars[i-1]['high'])+.25*a[i]
        elif family=='G2':
            if day not in ranges or not (8*3600+preset*60<=seconds<12*3600-900):continue
            high,low=ranges[day];hold=12;max_per_day=1
            if low<=c[i-1]<=high:
                if c[i]>high+.1*a[i]:direction=1
                elif c[i]<low-.1*a[i]:direction=-1
            stop=(high+low)/2
        elif family=='G3':
            if h<52 or b['time']+900-(h1['time'][h]+3600)>3600 or abs(fast[h]-fast[h-3])>.25*ha[h]:continue
            hold=8;reward=None;target=mean[i]
            if c[i-1]<lower[i-1] and lower[i]<=c[i]<=upper[i] and c[i]>b['open']:direction=1
            if c[i-1]>upper[i-1] and lower[i]<=c[i]<=upper[i] and c[i]<b['open']:direction=-1
            stop=min(b['low'],bars[i-1]['low'])-.25*a[i] if direction==1 else max(b['high'],bars[i-1]['high'])+.25*a[i]
        elif family=='G4':
            if day not in previous:continue
            high,low=previous[day]
            if preset*a[i]<=low-b['low']<=a[i] and c[i]>low and c[i]>b['open'] and (day,1) not in used_levels:direction=1
            elif preset*a[i]<=b['high']-high<=a[i] and c[i]<high and c[i]<b['open'] and (day,-1) not in used_levels:direction=-1
            stop=b['low']-.25*a[i] if direction==1 else b['high']+.25*a[i]
        elif family=='G5':
            if low_pair and low_pair[0] is not None:
                prior,pivot=low_pair
                if 6<=pivot-prior<=40 and bars[prior]['low']-bars[pivot]['low']>=.1*a[pivot] and strength[pivot]-strength[prior]>=5 and strength[pivot]<45 and c[i]>b['open']:
                    direction=1;stop=bars[pivot]['low']-.25*a[i]
            if not direction and high_pair and high_pair[0] is not None:
                prior,pivot=high_pair
                if 6<=pivot-prior<=40 and bars[pivot]['high']-bars[prior]['high']>=.1*a[pivot] and strength[prior]-strength[pivot]>=5 and strength[pivot]>55 and c[i]<b['open']:
                    direction=-1;stop=bars[pivot]['high']+.25*a[i]
        if not direction:continue
        distance=direction*(c[i]-stop)
        if not a[i]<=distance<=3*a[i]:continue
        target=c[i]+direction*reward*distance if reward else target
        if direction*(target-c[i])<distance:continue
        if family=='G4':used_levels.add((day,direction))
        output[i]={'id':family,'preset':preset,'direction':direction,'stop':float(stop),'target':float(target),'atr':float(a[i]),'holdBars':hold,'minRewardR':1,'maxTradesPerDay':max_per_day,'signalTime':int(b['time']),**({'reward':reward} if reward else {})}
    return output
