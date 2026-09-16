"""Seven pre-registered H1 hypotheses. Pure closed-candle signals, no execution."""
import numpy as np
from gold_signals import ema, atr, rsi


def make_signals(bars, h4, family, variant='control'):
    if family not in ['G1','G2','G3','G4','G5'] or variant not in (['control','confirmation'] if family in ['G2','G4'] else ['control']):
        raise ValueError('Unregistered family/variant')
    n = len(bars)
    output = [None] * n
    if n < 31:
        return output
    times, c = bars['time'], bars['close']
    a, e20 = atr(bars), ema(c, 20)
    slow, fast, ha = ema(h4['close'],200), ema(h4['close'],50), atr(h4)
    hi = np.searchsorted(h4['time']+14400, times+3600, side='right')-1
    groups = np.split(np.arange(n), np.flatnonzero(np.diff(times//86400))+1)
    day_indices = {int(times[g[0]]//86400): g for g in groups}
    ordered = list(day_indices)
    ranges, previous = {}, {}
    for offset, day in enumerate(ordered):
        idx = day_indices[day]
        if family == 'G2':
            group = idx[(times[idx]%86400>=8*3600)&(times[idx]%86400<10*3600)]
            if len(group)==2 and np.all(np.diff(times[group])==3600):
                ranges[day] = (float(max(bars['high'][group])),float(min(bars['low'][group])))
        if family == 'G4' and offset:
            prior = day_indices[ordered[offset-1]]
            if len(prior)==23 and int(times[prior[0]]%86400) in [0,3600] and np.all(np.diff(times[prior])==3600):
                previous[day] = (float(max(bars['high'][prior])),float(min(bars['low'][prior])))
    mean, std = np.full(n,np.nan), np.full(n,np.nan)
    if family=='G3':
        windows = np.lib.stride_tricks.sliding_window_view(c,20)
        mean[19:], std[19:] = windows.mean(axis=1), windows.std(axis=1,ddof=0)
    lower, upper = mean-2.5*std, mean+2.5*std
    strength = rsi(bars) if family=='G5' else None
    last_low = last_high = None
    used_levels, used_ranges = set(), set()
    pending_range = None
    pending_sweeps = {}

    for i in range(30,n):
        b, prior_bar = bars[i], bars[i-1]
        day, seconds = int(times[i]//86400), int(times[i]%86400)
        continuous = times[i]-times[i-1]==3600 and day==times[i-1]//86400
        if not continuous:
            pending_range, pending_sweeps = None, {}
        low_pair = high_pair = None
        if family=='G5':
            pivot = i-3
            if times[i]-times[i-6]==6*3600:
                left,right = bars[pivot-3:pivot],bars[pivot+1:i+1]
                if bars[pivot]['low'] < min(min(left['low']),min(right['low'])):
                    low_pair,last_low = (last_low,pivot),pivot
                if bars[pivot]['high'] > max(max(left['high']),max(right['high'])):
                    high_pair,last_high = (last_high,pivot),pivot
        entry_seconds = int((times[i]+3600)%86400)
        if not (8*3600<=entry_seconds<20*3600) or not continuous or not np.isfinite(a[i]) or a[i]<=0:
            continue
        direction, stop, target, reward, hold, max_per_day = 0,0.,None,2.,8,2
        h = int(hi[i])
        if family in ['G1','G3'] and (h<0 or times[i]+3600-(h4['time'][h]+14400)>14400):
            continue
        if family=='G1':
            if h<202:
                continue
            trend = 1 if h4['close'][h]>slow[h] and fast[h]>slow[h] and fast[h]>fast[h-3] else -1 if h4['close'][h]<slow[h] and fast[h]<slow[h] and fast[h]<fast[h-3] else 0
            if trend==1 and c[i-1]<=e20[i-1] and c[i]>e20[i] and c[i]>b['open']:
                direction=1
            elif trend==-1 and c[i-1]>=e20[i-1] and c[i]<e20[i] and c[i]<b['open']:
                direction=-1
            stop = min(b['low'],prior_bar['low'])-.25*a[i] if direction==1 else max(b['high'],prior_bar['high'])+.25*a[i]
        elif family=='G2':
            max_per_day=1
            if day not in ranges or not (10*3600<=seconds and entry_seconds<14*3600):
                continue
            high,low = ranges[day]
            if pending_range is not None:
                setup = pending_range
                d,edge,band = setup['direction'],setup['edge'],.25*setup['atr']
                if i-setup['index']>2 or d*(c[i]-edge)<=0:
                    pending_range=None
                else:
                    touch = abs((b['low'] if d==1 else b['high'])-edge)<=band
                    if touch and d*(c[i]-b['open'])>0:
                        direction=d
                        pending_range=None
            elif day not in used_ranges and low<=c[i-1]<=high:
                d = 1 if c[i]>high+.1*a[i] else -1 if c[i]<low-.1*a[i] else 0
                if d:
                    used_ranges.add(day)
                    if variant=='control':
                        direction=d
                    else:
                        pending_range={'index':i,'direction':d,'edge':high if d==1 else low,'atr':float(a[i])}
            stop=(high+low)/2
        elif family=='G3':
            if h<52 or abs(fast[h]-fast[h-3])>.25*ha[h]:
                continue
            hold,reward,target = 6,None,float(mean[i])
            if c[i-1]<lower[i-1] and lower[i]<=c[i]<=upper[i] and c[i]>b['open']:
                direction=1
            elif c[i-1]>upper[i-1] and lower[i]<=c[i]<=upper[i] and c[i]<b['open']:
                direction=-1
            stop = min(b['low'],prior_bar['low'])-.25*a[i] if direction==1 else max(b['high'],prior_bar['high'])+.25*a[i]
        elif family=='G4':
            if day not in previous:
                continue
            high,low = previous[day]
            for d,setup in list(pending_sweeps.items()):
                invalid = b['low']<setup['low'] if d==1 else b['high']>setup['high']
                if i-setup['index']>2 or invalid:
                    del pending_sweeps[d]
                elif d*(c[i]-(setup['high'] if d==1 else setup['low']))>0:
                    direction,stop=d,setup['stop']
                    del pending_sweeps[d]
                    break
            if not direction:
                d=0
                if (day,1) not in used_levels and .1*a[i]<=low-b['low']<=a[i] and low<c[i]<=high and c[i]>b['open']:
                    d=1
                elif (day,-1) not in used_levels and .1*a[i]<=b['high']-high<=a[i] and low<=c[i]<high and c[i]<b['open']:
                    d=-1
                if d:
                    used_levels.add((day,d))
                    rejection_stop=b['low']-.25*a[i] if d==1 else b['high']+.25*a[i]
                    if variant=='control':
                        direction,stop=d,rejection_stop
                    else:
                        pending_sweeps[d]={'index':i,'low':float(b['low']),'high':float(b['high']),'stop':float(rejection_stop)}
        elif family=='G5':
            if low_pair and low_pair[0] is not None:
                prior,pivot=low_pair
                if 6<=pivot-prior<=40 and bars[prior]['low']-bars[pivot]['low']>=.1*a[pivot] and strength[pivot]-strength[prior]>=5 and strength[pivot]<45 and c[i]>b['open']:
                    direction,stop=1,bars[pivot]['low']-.25*a[i]
            if not direction and high_pair and high_pair[0] is not None:
                prior,pivot=high_pair
                if 6<=pivot-prior<=40 and bars[pivot]['high']-bars[prior]['high']>=.1*a[pivot] and strength[prior]-strength[pivot]>=5 and strength[pivot]>55 and c[i]<b['open']:
                    direction,stop=-1,bars[pivot]['high']+.25*a[i]
        if not direction:
            continue
        distance=direction*(c[i]-stop)
        if not a[i]<=distance<=3*a[i]:
            continue
        if reward:
            target=float(c[i]+direction*reward*distance)
        if not np.isfinite(target) or direction*(target-c[i])<distance:
            continue
        output[i]={'id':family,'variant':variant,'direction':direction,'stop':float(stop),'target':float(target),
                   'atr':float(a[i]),'holdBars':hold,'maxTradesPerDay':max_per_day,'minRewardR':1,
                   'signalTime':int(times[i]), **({'reward':reward} if reward else {})}
    return output
