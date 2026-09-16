"""Bounded anonymous public-form acquisition. No account, paid API or retries."""
import argparse,datetime as dt,hashlib,io,json,re,time,urllib.parse,urllib.request,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE='https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes'
LIMIT=20_000_000

def write(path,value):path.write_text(json.dumps(value,indent=2),encoding='utf-8')

def download(symbol,year,month,folder):
    period=str(year)+(f'{month:02}' if month else '')
    name=f'HISTDATA_COM_ASCII_{symbol}_M1_{period}.zip'
    target,record=folder/name,folder/(name+'.json')
    if target.exists():
        if not record.exists():raise ValueError(f'Existing ZIP lacks provenance: {target}')
        metadata=json.loads(record.read_text(encoding='utf-8'))
        if hashlib.sha256(target.read_bytes()).hexdigest()!=metadata['sha256']:raise ValueError('Cached ZIP hash changed')
        return metadata
    page=f'{BASE}/{symbol.lower()}/{year}'+(f'/{month}' if month else '')
    with urllib.request.urlopen(page,timeout=30) as response:
        html=response.read(2_000_001)
    if len(html)>2_000_000:raise ValueError('Oversized download form')
    form=re.search(r'<form id="file_down".*?</form>',html.decode('utf-8'),re.S)
    if form is None:raise ValueError(f'No public download form: {page}')
    fields=dict(re.findall(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"',form.group(0)))
    expected={'date':str(year),'platform':'ASCII','timeframe':'M1','fxpair':symbol}
    if not fields.get('tk') or any(fields.get(key)!=value for key,value in expected.items()) or fields.get('datemonth')!=period:
        raise ValueError(f'Public form does not match requested period {symbol}/{period}; stopped')
    action=urllib.parse.urljoin(page,re.search(r'action="([^"]+)"',form.group(0)).group(1))
    if action!='https://www.histdata.com/get.php':raise ValueError('Unexpected download endpoint')
    request=urllib.request.Request(action,data=urllib.parse.urlencode(fields).encode(),headers={'Referer':page})
    with urllib.request.urlopen(request,timeout=60) as response:
        content=response.read(LIMIT+1);status=response.status
    if len(content)>LIMIT or not zipfile.is_zipfile(io.BytesIO(content)):raise ValueError('Expected bounded ZIP response')
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        members=archive.namelist()
        if f'DAT_ASCII_{symbol}_M1_{period}.csv' not in members:raise ValueError('ZIP member does not match requested archive')
        if sum(item.file_size for item in archive.infolist())>100_000_000:raise ValueError('Unexpected decompressed size')
        if archive.testzip() is not None:raise ValueError('ZIP integrity check failed')
    metadata={'provider':'HistData','symbol':symbol,'period':period,'downloadPage':page,'endpoint':action,
              'httpStatus':status,'fetchedAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'file':name,'members':members}
    # Tokens from the public form are not persisted or logged.
    with target.open('xb') as stream:stream.write(content)
    write(record,metadata)
    time.sleep(1)
    return metadata

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'research/cache/histdata-raw');args=parser.parse_args()
    protocol_path=ROOT/'research/external-data-v1-protocol.json'
    protocol=json.loads(protocol_path.read_text(encoding='utf-8'));digest=hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    assert protocol['symbols']==['EURUSD','NSXUSD'] and protocol['annualYears']==list(range(2010,2026))
    assert protocol['monthlyYear']==2026 and protocol['months']==list(range(1,9))
    args.output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for symbol in protocol['symbols']:
        periods=[(year,None) for year in protocol['annualYears']]+[(protocol['monthlyYear'],month) for month in protocol['months']]
        for year,month in periods:
            row=download(symbol,year,month,args.output);rows.append(row)
            write(args.output/'manifest.json',{'protocolHash':digest,'complete':False,'files':rows})
            print(json.dumps({'symbol':symbol,'period':row['period'],'bytes':row['bytes'],'downloadedOrVerified':len(rows)}),flush=True)
    assert hashlib.sha256(protocol_path.read_bytes()).hexdigest()==digest,'Acquisition protocol changed'
    write(args.output/'manifest.json',{'protocolHash':digest,'complete':True,'files':rows})
