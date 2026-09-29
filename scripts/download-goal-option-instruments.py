from __future__ import annotations
import argparse, datetime as dt, gzip, hashlib, json, os, tempfile, urllib.error, urllib.parse, urllib.request
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'research/cache/goal-seven/options-instruments'
MANIFEST = ROOT / 'research/goal-seven/options-instruments-data-manifest.json'
API = 'https://history.deribit.com/api/v2/public/get_instruments'
SYMBOLS = ('BTC', 'ETH')
LIMIT_ONE = 160_000_000
LIMIT_TOTAL = 320_000_000
FIELDS = ('instrument_name','kind','base_currency','quote_currency','settlement_currency','price_index','strike','option_type','creation_timestamp','expiration_timestamp','contract_size')

def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def decimal_string(v):
    if isinstance(v, Decimal): return format(v, 'f')
    if isinstance(v, int) and not isinstance(v,bool): return str(v)
    if isinstance(v,float): return repr(v)
    return None

def result_objects(path):
    dec=json.JSONDecoder(parse_float=Decimal, parse_int=int)
    with path.open('r',encoding='utf-8') as f:
        buf=''; eof=False; started=False
        while True:
            if not eof and len(buf)<65536:
                chunk=f.read(65536)
                if chunk: buf+=chunk
                else: eof=True
            if not started:
                k=buf.find('"result"')
                if k<0:
                    if eof: raise ValueError('JSON result key missing')
                    buf=buf[-32:]; continue
                c=buf.find('[',k)
                if c<0:
                    if eof: raise ValueError('JSON result array missing')
                    buf=buf[k:]; continue
                buf=buf[c+1:]; started=True
            buf=buf.lstrip()
            if buf.startswith(','): buf=buf[1:].lstrip()
            if buf.startswith(']'): return
            if not buf:
                if eof: raise ValueError('truncated result array')
                continue
            try: value,end=dec.raw_decode(buf)
            except json.JSONDecodeError:
                if eof: raise
                chunk=f.read(65536)
                if not chunk: eof=True
                else: buf+=chunk
                continue
            if not isinstance(value,dict):
                raise ValueError('result contains non-object; aborting normalization')
            yield value
            buf=buf[end:]

def main():
    ap=argparse.ArgumentParser(description='Fetch only official Deribit option instrument catalogs; no trades/prices/performance.')
    ap.add_argument('--verify',action='store_true',help='local checksum and normalized-file verification only')
    args=ap.parse_args()
    if args.verify:
        m=json.loads(MANIFEST.read_text(encoding='utf-8'))
        for r in m['responses']:
            raw=ROOT/r['rawGzipPath']; norm=ROOT/r['normalizedPath']
            if sha_file(raw)!=r['gzipSha256']: raise SystemExit('raw gzip SHA mismatch: '+r['symbol'])
            if sha_file(norm)!=r['normalizedSha256']: raise SystemExit('normalized SHA mismatch: '+r['symbol'])
            with gzip.open(raw,'rb') as g:
                h=hashlib.sha256()
                for b in iter(lambda:g.read(1024*1024),b''): h.update(b)
            if h.hexdigest()!=r['rawSha256']: raise SystemExit('raw SHA mismatch: '+r['symbol'])
        print('verified',len(m['responses']),'responses')
        return
    CACHE.mkdir(parents=True,exist_ok=True)
    if MANIFEST.exists() or any(CACHE.iterdir()): raise SystemExit('immutable destination exists; refusing overwrite')
    responses=[]; total=0
    for symbol in SYMBOLS:
        params={'currency':symbol,'kind':'option','expired':'true','include_old':'true'}
        url=API+'?'+urllib.parse.urlencode(params)
        started=utc(); req=urllib.request.Request(url,headers={'User-Agent':'TraderNova-N13-instrument-metadata/1.0','Accept-Encoding':'identity'})
        raw_tmp=CACHE/(symbol+'.response.tmp'); gz_tmp=CACHE/(symbol+'.response.json.gz.tmp')
        status=None; headers={}; err=None; size=0; sha=hashlib.sha256()
        try:
            resp=urllib.request.urlopen(req,timeout=60)
        except urllib.error.HTTPError as e:
            resp=e; err=f'HTTP {e.code}'
        try:
            status=resp.status; headers=dict(resp.headers.items())
            content_len=headers.get('Content-Length')
            if content_len and int(content_len)>LIMIT_ONE: raise RuntimeError(f'Content-Length {content_len} exceeds per-response cap')
            with raw_tmp.open('xb') as rawf, gz_tmp.open('xb') as gzf, gzip.GzipFile(fileobj=gzf,mode='wb',mtime=0) as gz:
                while True:
                    chunk=resp.read(1024*1024)
                    if not chunk: break
                    size+=len(chunk)
                    if size>LIMIT_ONE or total+size>LIMIT_TOTAL: raise RuntimeError('response byte cap exceeded; stopped')
                    sha.update(chunk); rawf.write(chunk); gz.write(chunk)
        finally:
            resp.close()
        received=utc(); total+=size
        raw_sha=sha.hexdigest()
        if status!=200: raise RuntimeError(f'{symbol}: API returned HTTP {status}; body preserved in temporary file')
        normalized_tmp=CACHE/(symbol+'.normalized.json.tmp')
        counts={'records':0,'fieldAvailability':{k:0 for k in FIELDS},'missingInstrumentName':0,'duplicateInstrumentNames':0,'invalidTimestamps':0,'invalidNumericFields':{k:0 for k in ('strike','contract_size')},'nullFields':{k:0 for k in FIELDS}}
        seen={}; first=[]
        with normalized_tmp.open('x',encoding='utf-8',newline='\n') as out:
            out.write('[\n'); comma=''
            for obj in result_objects(raw_tmp):
                counts['records']+=1
                for k in FIELDS:
                    if k in obj and obj[k] is not None: counts['fieldAvailability'][k]+=1
                    else: counts['nullFields'][k]+=1
                name=obj.get('instrument_name')
                if not isinstance(name,str) or not name: counts['missingInstrumentName']+=1
                else: seen[name]=seen.get(name,0)+1
                for k in ('creation_timestamp','expiration_timestamp'):
                    v=obj.get(k)
                    if v is not None and (isinstance(v,bool) or not isinstance(v,int)): counts['invalidTimestamps']+=1
                row={k:obj.get(k) for k in FIELDS}
                for k in ('strike','contract_size'):
                    row[k]=decimal_string(obj.get(k))
                    if obj.get(k) is not None and row[k] is None: counts['invalidNumericFields'][k]+=1
                out.write(comma+json.dumps(row,ensure_ascii=False,separators=(',',':'))); comma=',\n'
            out.write('\n]\n')
        counts['duplicateInstrumentNames']=sum(n-1 for n in seen.values() if n>1)
        counts['uniqueInstrumentNames']=len(seen)
        raw_final=CACHE/(symbol+'.response.json.gz'); norm_final=CACHE/(symbol+'.normalized.json')
        os.replace(gz_tmp,raw_final); os.replace(normalized_tmp,norm_final); raw_tmp.unlink()
        responses.append({'symbol':symbol,'url':url,'requestStartedUtc':started,'receivedUtc':received,'httpStatus':status,'responseHeaders':headers,'contentLengthHeader':content_len,'downloadedBytes':size,'rawSha256':raw_sha,'gzipSha256':sha_file(raw_final),'rawGzipPath':raw_final.relative_to(ROOT).as_posix(),'normalizedPath':norm_final.relative_to(ROOT).as_posix(),'normalizedSha256':sha_file(norm_final),'normalizedRows':counts['records'],'quality':counts})
        print(json.dumps({'symbol':symbol,'status':status,'bytes':size,'records':counts['records'],'rawSha256':raw_sha,'gzipSha256':sha_file(raw_final),'quality':counts},separators=(',',':')))
    manifest={'id':'N13-deribit-option-instruments-v1','createdAtUtc':utc(),'source':API,'scope':{'currencies':list(SYMBOLS),'kind':'option','expired':True,'include_old':True,'purpose':'metadata only; no trades/prices/performance'},'limits':{'maxGetCount':3,'actualGetCount':len(responses),'maxBytesPerResponse':LIMIT_ONE,'maxTotalBytes':LIMIT_TOTAL,'actualBytes':total},'normalization':{'allRecordsPreserved':True,'duplicateNamesDropped':False,'isActiveFilterApplied':False,'fieldOrder':list(FIELDS),'decimalFieldsAsStrings':['strike','contract_size'],'timestamps':'epoch milliseconds as returned; raw source response retained'},'responses':responses}
    temp=MANIFEST.with_suffix('.json.tmp'); temp.parent.mkdir(parents=True,exist_ok=True); temp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); os.replace(temp,MANIFEST)
if __name__=='__main__': main()

