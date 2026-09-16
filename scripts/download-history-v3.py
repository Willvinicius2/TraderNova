"""Extend hourly research back to 2022; preserve the v1/v2 cache and public data."""
import importlib.util, pathlib, concurrent.futures, datetime as dt, zipfile, csv, io, json, hashlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('history',ROOT/'scripts/download-history.py')
history=importlib.util.module_from_spec(spec);spec.loader.exec_module(history)
DEST=ROOT/'research/cache/v3';DEST.mkdir(parents=True,exist_ok=True)
months=[];cursor=dt.date(2021,12,1)
while cursor<dt.date(2026,9,1):
 months.append(cursor.strftime('%Y-%m'));cursor=(cursor.replace(day=28)+dt.timedelta(days=4)).replace(day=1)
jobs=[(s,'1h',m) for s in ['BTCUSDT','ETHUSDT','SOLUSDT'] for m in months]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: archives=list(pool.map(history.download,jobs))
manifest={'source':'Binance Spot monthly archives','retrievedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'archives':archives,'series':[]}
for symbol in ['BTCUSDT','ETHUSDT','SOLUSDT']:
 bars=[]
 for month in months:
  name=f'{symbol}-1h-{month}'
  with zipfile.ZipFile(history.CACHE/(name+'.zip')) as z:
   with z.open(name+'.csv') as stream:
    for row in csv.reader(io.TextIOWrapper(stream)):
     stamp=int(row[0]);stamp=stamp//1000 if stamp>=100_000_000_000_000 else stamp
     bars.append(dict(zip(['time','open','high','low','close','volume'],[stamp]+[float(v) for v in row[1:6]])))
 gaps=[{'after':bars[i-1]['time'],'before':b['time']} for i,b in enumerate(bars) if i and b['time']-bars[i-1]['time']!=3600000]
 if gaps: print(f'{symbol}: source gaps recorded, no interpolation: {gaps}',flush=True)
 assert bars[0]['time']==int(dt.datetime(2021,12,1,tzinfo=dt.timezone.utc).timestamp()*1000)
 assert bars[-1]['time']+3600000==int(dt.datetime(2026,9,1,tzinfo=dt.timezone.utc).timestamp()*1000)
 content=json.dumps(bars,separators=(',',':')).encode();filename=f'{symbol}-1h.json';(DEST/filename).write_bytes(content)
 manifest['series'].append({'symbol':symbol,'interval':60,'file':filename,'bars':len(bars),'first':bars[0]['time'],'toExclusive':bars[-1]['time']+3600000,'sha256':hashlib.sha256(content).hexdigest(),'gaps':gaps})
 print(f'{symbol}: {len(bars)} verified hourly candles; {len(gaps)} source gaps',flush=True)
(DEST/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(f'{len(archives)} monthly archives verified.',flush=True)
