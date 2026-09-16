"""Strict local HistData ASCII M1 -> complete UTC M15/H1/H4 candles.

Official format: Bid OHLC; timestamp EST (UTC-5) without DST. This parser never
adds missing minutes, invents volume, or treats the feed as the user's broker.
Raw ZIP files stay local. Each output manifest records every input SHA256.
"""
import argparse,csv,datetime as dt,hashlib,io,json,re,zipfile
from pathlib import Path
import numpy as np

FIELDS=[('time','i8'),('open','f8'),('high','f8'),('low','f8'),('close','f8'),('spread','i8')]
SOURCE_ZONE=dt.timezone(dt.timedelta(hours=-5))
FORMAT_URL='https://www.histdata.com/f-a-q/data-files-detailed-specification/'

def parse_line(line):
    columns=line.strip().split(';')
    if len(columns)!=6 or not re.fullmatch(r'\d{8} \d{6}',columns[0]):
        raise ValueError('Unexpected HistData ASCII M1 record')
    local=dt.datetime.strptime(columns[0],'%Y%m%d %H%M%S').replace(tzinfo=SOURCE_ZONE)
    if local.second:
        raise ValueError('M1 timestamp is not minute-aligned')
    values=[float(value) for value in columns[1:]]
    o,h,l,c,v=values
    if not np.all(np.isfinite(values)) or l<=0 or l>min(o,c) or h<max(o,c) or v<0:
        raise ValueError('Invalid OHLC or volume')
    # Missing spread is explicitly zero in the transport schema, not free fills.
    return (int(local.timestamp()),o,h,l,c,0)

def read_archives(paths,symbol):
    records=[];provenance=[];last=None
    for path in paths:
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        count=0
        with zipfile.ZipFile(path) as archive:
            members=[name for name in archive.namelist() if re.fullmatch(rf'(?:.*/)?DAT_ASCII_{re.escape(symbol)}_M1_\d{{4}}(?:\d{{2}})?.csv',name,re.I)]
            if len(members)!=1:
                raise ValueError(f'Expected one exact {symbol} M1 CSV in {path.name}; got {members}')
            # Stream directly from the ZIP. Never extract archive paths.
            with archive.open(members[0]) as stream:
                for line in io.TextIOWrapper(stream,encoding='utf-8-sig'):
                    if not line.strip():continue
                    record=parse_line(line)
                    if last is not None and record[0]<=last:
                        raise ValueError(f'Duplicate, overlapping or unordered source at {record[0]} in {path.name}')
                    records.append(record);last=record[0];count+=1
        provenance.append({'file':path.name,'sha256':digest,'minuteBars':count})
    if not records:raise ValueError('No M1 records')
    return np.array(records,dtype=FIELDS),provenance

def aggregate(minutes,period):
    if period not in [15,60,240]:raise ValueError('Supported periods: M15/H1/H4')
    if not len(minutes):return np.array([],dtype=FIELDS),{'groups':0,'complete':0,'incomplete':0}
    seconds=period*60;times=minutes['time']
    if np.any(np.diff(times)<=0) or np.any(times%60):raise ValueError('Unordered/non-minute source')
    buckets=times//seconds
    boundaries=np.r_[0,np.flatnonzero(np.diff(buckets))+1,len(minutes)]
    output=[];incomplete=0
    for first,end in zip(boundaries[:-1],boundaries[1:]):
        group=minutes[first:end];start=int(buckets[first])*seconds
        if len(group)!=period or group['time'][0]!=start or group['time'][-1]!=start+seconds-60 or np.any(np.diff(group['time'])!=60):
            incomplete+=1;continue
        output.append((start,float(group['open'][0]),float(max(group['high'])),float(min(group['low'])),float(group['close'][-1]),0))
    return np.array(output,dtype=FIELDS),{'groups':len(boundaries)-1,'complete':len(output),'incomplete':incomplete}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,nargs='+',required=True)
    parser.add_argument('--symbol',choices=['EURUSD','USDJPY','NSXUSD'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--end',default='2026-09-01',help='Exclusive UTC boundary; later data is excluded')
    args=parser.parse_args()
    end=int(dt.datetime.fromisoformat(args.end).replace(tzinfo=dt.timezone.utc).timestamp())
    paths=sorted(args.source,key=lambda path:path.name)
    minutes,sources=read_archives(paths,args.symbol)
    minutes=minutes[minutes['time']<end]
    if not len(minutes):raise ValueError('No source minutes before cutoff')
    args.output.mkdir(parents=True,exist_ok=True)
    manifest={'symbol':args.symbol,'provider':'HistData','formatUrl':FORMAT_URL,'price':'Bid OHLC',
              'sourceTimezone':'Fixed EST UTC-05:00, without daylight-saving changes','outputTimezone':'UTC',
              'spread':'Not supplied by M1; output spread=0 is missing data, never a zero-cost assumption',
              'volume':'Not used; no traded volume inferred','sourceFiles':sources,'endExclusive':args.end,
              'minuteBars':len(minutes),'minuteGaps':int(sum(np.diff(minutes['time'])!=60)),
              'firstMinute':int(minutes['time'][0]),'lastMinute':int(minutes['time'][-1]),'series':{},
              'limitations':['External indicative feed, not The5ers executable quotes',
                             'Incomplete target candles are excluded; absent minutes are never filled',
                             'Session/weekend gaps and unexplained gaps require separate examination']}
    for label,period in [('M15',15),('H1',60),('H4',240)]:
        bars,quality=aggregate(minutes,period)
        target=args.output/f'{args.symbol}_{label}.csv'
        buffer=io.StringIO(newline='');writer=csv.writer(buffer);writer.writerow([name for name,_ in FIELDS])
        writer.writerows(tuple(value.item() for value in row) for row in bars)
        raw=buffer.getvalue().encode('utf-8')
        if target.exists() and target.read_bytes()!=raw:raise ValueError(f'Output exists with different data: {target}')
        if not target.exists():target.write_bytes(raw)
        manifest['series'][label]={**quality,'file':target.name,'sha256':hashlib.sha256(raw).hexdigest(),
                                   'first':int(bars['time'][0]) if len(bars) else None,
                                   'last':int(bars['time'][-1]) if len(bars) else None}
    target=args.output/'manifest.json';raw=json.dumps(manifest,indent=2).encode('utf-8')
    if target.exists() and target.read_bytes()!=raw:raise ValueError('Existing manifest differs')
    if not target.exists():target.write_bytes(raw)
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
