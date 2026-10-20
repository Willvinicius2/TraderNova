"""Protocol v4 data: Binance spot 1h archives (checksum verified) and HistData M1 -> H1.

Public archives only; no credentials, paid API or orders. Gaps are recorded, never filled.
Usage: python scripts/download-history-v4.py [--market crypto|fx]
"""
import argparse, concurrent.futures, csv, datetime as dt, hashlib, importlib.util, io, json, pathlib, subprocess, sys, zipfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTOCOL = json.loads((ROOT/'research/v4-protocol.json').read_text())
def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/file); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
def months(first, end):
    cursor, out = dt.date.fromisoformat(first), []
    while cursor < dt.date.fromisoformat(end):
        out.append(cursor.strftime('%Y-%m')); cursor = (cursor.replace(day=28)+dt.timedelta(days=4)).replace(day=1)
    return out

def crypto():
    history = load('history', 'download-history.py'); spec = PROTOCOL['markets']['crypto']
    dest = ROOT/'research/cache/v4/crypto'; dest.mkdir(parents=True, exist_ok=True)
    jobs = [(s, '1h', m) for s in spec['symbols'] for m in months(*spec['download'][s])]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: archives = list(pool.map(history.download, jobs))
    manifest = {'source': spec['source'], 'protocolSha256': hashlib.sha256((ROOT/'research/v4-protocol.json').read_bytes()).hexdigest(), 'retrievedAt': dt.datetime.now(dt.timezone.utc).isoformat(), 'archives': archives, 'series': []}
    for symbol in spec['symbols']:
        bars = []
        for month in months(*spec['download'][symbol]):
            name = f'{symbol}-1h-{month}'
            with zipfile.ZipFile(history.CACHE/(name+'.zip')) as z, z.open(name+'.csv') as stream:
                for row in csv.reader(io.TextIOWrapper(stream)):
                    stamp = int(row[0]); stamp = stamp//1000 if stamp >= 100_000_000_000_000 else stamp
                    bars.append(dict(zip(['time','open','high','low','close','volume'], [stamp]+[float(v) for v in row[1:6]])))
        if any(b['time'] % 3600000 or (i and b['time'] <= bars[i-1]['time']) for i, b in enumerate(bars)): raise ValueError(f'{symbol}: unordered or misaligned source')
        gaps = [{'after': bars[i-1]['time'], 'before': b['time'], 'missingHours': (b['time']-bars[i-1]['time'])//3600000-1} for i, b in enumerate(bars) if i and b['time']-bars[i-1]['time'] != 3600000]
        content = json.dumps(bars, separators=(',',':')).encode(); filename = f'{symbol}-1h.json'; (dest/filename).write_bytes(content)
        manifest['series'].append({'symbol': symbol, 'file': filename, 'bars': len(bars), 'first': bars[0]['time'], 'last': bars[-1]['time'], 'sha256': hashlib.sha256(content).hexdigest(), 'gaps': gaps})
        print(f'{symbol}: {len(bars)} hourly candles, {len(gaps)} recorded source gaps', flush=True)
    (dest/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

def fx():
    histdata = load('histdata', 'download_histdata.py'); spec = PROTOCOL['markets']['fx']
    raw = ROOT/'research/cache/histdata-raw'; raw.mkdir(parents=True, exist_ok=True)
    for symbol in spec['symbols']:
        first, end = spec['download'][symbol]; last_year = dt.date.fromisoformat(end).year
        periods = [(y, None) for y in range(dt.date.fromisoformat(first).year, last_year)]+[(last_year, m) for m in range(1, dt.date.fromisoformat(end).month)]
        files = [raw/histdata.download(symbol, y, m, raw)['file'] for y, m in periods]
        out = ROOT/f'research/cache/v4/fx/{symbol}'
        subprocess.run([sys.executable, str(ROOT/'scripts/import_histdata.py'), '--source', *map(str, files), '--symbol', symbol, '--output', str(out), '--end', end], check=True)
        print(f'{symbol}: {len(files)} HistData archives imported', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--market', choices=['crypto', 'fx']); args = parser.parse_args()
    if args.market in (None, 'crypto'): crypto()
    if args.market in (None, 'fx'): fx()
