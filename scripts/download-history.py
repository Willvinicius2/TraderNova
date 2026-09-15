"""Public Binance monthly archives, checksum verified. No credentials or paid API."""
import calendar, concurrent.futures, csv, datetime as dt, hashlib, io, json, pathlib, time, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTOCOL = json.loads((ROOT / 'research/protocol.json').read_text())
CACHE = ROOT / 'research/cache'
CACHE.mkdir(parents=True, exist_ok=True)
BASE = 'https://data.binance.vision/data/spot/monthly/klines'

def fetch(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'TraderNova-research/1.0'}), timeout=45) as r:
                return r.read()
        except Exception:
            if attempt == 2: raise
            time.sleep(1 + attempt)

def download(job):
    symbol, interval, month = job
    name = f'{symbol}-{interval}-{month}.zip'
    url = f'{BASE}/{symbol}/{interval}/{name}'
    path = CACHE / name
    checksum_path = CACHE / (name + '.CHECKSUM')
    expected = (checksum_path.read_bytes() if checksum_path.exists() else fetch(url + '.CHECKSUM'))
    digest = expected.decode().split()[0]
    blob = path.read_bytes() if path.exists() else fetch(url)
    actual = hashlib.sha256(blob).hexdigest()
    if len(digest) != 64 or actual != digest: raise ValueError(f'Checksum mismatch: {name}')
    path.write_bytes(blob)
    checksum_path.write_bytes(expected)
    return {'url': url, 'sha256': actual, 'bytes': len(blob), 'symbol': symbol, 'interval': interval, 'month': month}

def main():
    start = dt.date.fromisoformat(PROTOCOL['from'])
    start = (start - dt.timedelta(days=1)).replace(day=1)
    end = dt.date.fromisoformat(PROTOCOL['toExclusive'])
    months = []
    while start < end:
        months.append(start.strftime('%Y-%m'))
        start = (start.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    jobs = [(s, '1h' if m == 60 else f'{m}m', month) for s in PROTOCOL['symbols'] for m in PROTOCOL['intervals'] for month in months]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        entries = list(pool.map(download, jobs))
    manifest = {'source': 'Binance public spot archives', 'retrievedAt': dt.datetime.now(dt.timezone.utc).isoformat(), 'protocolSha256': hashlib.sha256((ROOT/'research/protocol.json').read_bytes()).hexdigest(), 'archives': entries, 'series': []}
    for symbol in PROTOCOL['symbols']:
        for minutes in PROTOCOL['intervals']:
            interval = '1h' if minutes == 60 else f'{minutes}m'
            bars = []
            for month in months:
                name = f'{symbol}-{interval}-{month}'
                with zipfile.ZipFile(CACHE / (name + '.zip')) as z:
                    with z.open(name + '.csv') as raw:
                        for row in csv.reader(io.TextIOWrapper(raw)):
                            stamp = int(row[0])
                            stamp = stamp // 1000 if stamp >= 100_000_000_000_000 else stamp
                            bars.append(dict(zip(['time','open','high','low','close','volume'], [stamp]+[float(v) for v in row[1:6]])))
            for i,b in enumerate(bars):
                if b['time'] % (minutes*60000) or (i and b['time']-bars[i-1]['time'] != minutes*60000):
                    raise ValueError(f'Gap/alignment failure: {symbol} {interval} index {i}')
            if bars[0]['time'] != int(dt.datetime.fromisoformat(months[0]+'-01').replace(tzinfo=dt.timezone.utc).timestamp()*1000) or bars[-1]['time'] + minutes*60000 != int(dt.datetime.combine(end,dt.time(),dt.timezone.utc).timestamp()*1000):
                raise ValueError('Coverage mismatch')
            out = json.dumps(bars, separators=(',',':')).encode()
            filename = f'{symbol}-{interval}.json'
            (CACHE / filename).write_bytes(out)
            manifest['series'].append({'symbol':symbol,'interval':minutes,'file':filename,'bars':len(bars),'first':bars[0]['time'],'toExclusive':bars[-1]['time']+minutes*60000,'sha256':hashlib.sha256(out).hexdigest()})
            print(f'{symbol} {interval}: {len(bars)} contiguous candles', flush=True)
    (CACHE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Verified {len(entries)} archives; manifest complete.',flush=True)

if __name__ == '__main__': main()
