"""Export closed bars from an already running, isolated MT5 with trading OFF.

Requires an explicit portable terminal/data path. Reads market data only; no
account, position, order, login, credential or trading API calls. The original
terminal and previous study files are never changed by this script.
"""
import argparse,csv,ctypes,datetime as dt,hashlib,json,pathlib,time
from ctypes import wintypes
import MetaTrader5 as mt5

def label(timestamp):return dt.datetime.fromtimestamp(int(timestamp),dt.timezone.utc).isoformat()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--terminal',type=pathlib.Path,required=True)
    parser.add_argument('--data-dir',type=pathlib.Path,required=True)
    parser.add_argument('--output',type=pathlib.Path,required=True)
    parser.add_argument('--pid',type=int,required=True)
    parser.add_argument('--count',type=int,default=1000000)
    args=parser.parse_args()
    if args.count<100000 or args.count>2000000:raise ValueError('Unexpected history size')
    if any(args.output.glob('XAUUSD_*.csv')):raise ValueError('Use a new output directory to preserve existing research')
    if args.terminal.resolve().parent!=args.data_dir.resolve():raise ValueError('Portable terminal path must match isolated data directory')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x1000,False,args.pid)
    if not handle:raise RuntimeError('The explicitly launched isolated process is not running')
    try:
        buffer=ctypes.create_unicode_buffer(32768);length=wintypes.DWORD(len(buffer))
        if not kernel.QueryFullProcessImageNameW(handle,0,buffer,ctypes.byref(length)) or pathlib.Path(buffer.value).resolve()!=args.terminal.resolve():raise RuntimeError('PID belongs to an unexpected executable')
    finally:kernel.CloseHandle(handle)
    # Caller launches the isolated executable with its explicit no-trading config.
    if not mt5.initialize(str(args.terminal),portable=True,timeout=30000):raise RuntimeError(f'MT5 connection failed: {mt5.last_error()}')
    try:
        info=mt5.terminal_info()
        if not info or pathlib.Path(info.data_path).resolve()!=args.data_dir.resolve() or pathlib.Path(info.path).resolve()!=args.data_dir.resolve():raise RuntimeError('Unexpected terminal data directory')
        if info.trade_allowed or info.dlls_allowed:raise RuntimeError('Trading and DLLs must be disabled before market-data export')
        if info.maxbars!=1000000:raise RuntimeError('Expected one-million-bar history limit')
        symbol=mt5.symbol_info('XAUUSD')
        if symbol is None:raise RuntimeError('Exact XAUUSD is unavailable')
        fields=['name','description','digits','point','trade_tick_size','trade_contract_size','trade_tick_value','currency_profit','volume_min','volume_max','volume_step','trade_stops_level','spread','spread_float','swap_mode','swap_long','swap_short','swap_rollover3days','chart_mode']
        metadata={'exportedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'source':'Five Percent Online portable terminal market cache','terminalVersion':mt5.version(),'packageVersion':mt5.__version__,'maxbars':int(info.maxbars),'connected':bool(info.connected),'tradingEnabled':False,'accountData':'not queried','clock':'Native exported broker labels; UTC display does not establish session timezone','symbol':{key:getattr(symbol,key,None) for key in fields},'series':[],'readOnlyCalls':['initialize','terminal_info','symbol_info','version','copy_rates_from_pos','last_error','shutdown']}
        args.output.mkdir(parents=True,exist_ok=True)
        for name,tf in [('M15',mt5.TIMEFRAME_M15),('H1',mt5.TIMEFRAME_H1)]:
            rates=None;attempts=[]
            for attempt in range(4):
                result=mt5.copy_rates_from_pos('XAUUSD',tf,1,min(args.count,int(info.maxbars)-1))
                attempts.append({'attempt':attempt+1,'bars':None if result is None else len(result),'error':mt5.last_error() if result is None else None})
                if result is not None and len(result)>100000:rates=result;break
                print(json.dumps({'timeframe':name,'attempt':attempts[-1]}),flush=True)
                time.sleep(2)
            if rates is None:raise RuntimeError(f'Extended {name} history unavailable: {attempts}')
            rates.sort(order='time')
            file=args.output/f'XAUUSD_{name}.csv'
            with file.open('x',encoding='utf-8',newline='') as stream:
                writer=csv.writer(stream);writer.writerow(list(rates.dtype.names)+['time_mt5_label'])
                for bar in rates:writer.writerow([bar[key].item() for key in rates.dtype.names]+[label(bar['time'])])
            record={'file':file.name,'bars':len(rates),'first':label(rates[0]['time']),'lastClosedBarOpen':label(rates[-1]['time']),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'attempts':attempts}
            metadata['series'].append(record);print(json.dumps(record),flush=True)
        (args.output/'manifest.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    finally:mt5.shutdown()

if __name__=='__main__':main()
