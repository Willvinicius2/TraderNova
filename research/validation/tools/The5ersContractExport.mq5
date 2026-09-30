// Read-only MT5 contract/tick snapshot exporter. No trading, account IDs, balance or history.
#property strict
#property script_show_inputs

input string InpSymbols="BTCUSD,ETHUSD,SOLUSD,XAUUSD,NAS100,EURUSD,USDJPY";
input string InpFilePrefix="the5ers_contracts";

string CsvEscape(const string value)
{
   string out=value;
   StringReplace(out,"\"","\"\"");
   return "\""+out+"\"";
}

string BoolText(const bool value) { return value ? "true" : "false"; }

void ReadDouble(const string symbol, const ENUM_SYMBOL_INFO_DOUBLE prop, double &value, string &missing)
{
   if(!SymbolInfoDouble(symbol,prop,value)) { value=0; missing+=EnumToString(prop)+";"; }
}
void ReadInteger(const string symbol, const ENUM_SYMBOL_INFO_INTEGER prop, long &value, string &missing)
{
   if(!SymbolInfoInteger(symbol,prop,value)) { value=0; missing+=EnumToString(prop)+";"; }
}
bool ReadString(const string symbol, const ENUM_SYMBOL_INFO_STRING prop, string &value, string &missing)
{
   if(!SymbolInfoString(symbol,prop,value)) { value=""; missing+=EnumToString(prop)+";"; return false; }
   return true;
}

void OnStart()
{
   string stamp=TimeToString(TimeGMT(),TIME_DATE|TIME_SECONDS);
   StringReplace(stamp,".","");
   StringReplace(stamp,":","");
   StringReplace(stamp," ","T");
   string csv_name=InpFilePrefix+"_"+stamp+"Z.csv";
   string meta_name=InpFilePrefix+"_"+stamp+"Z_metadata.txt";
   int file=FileOpen(csv_name,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',',CP_UTF8);
   if(file==INVALID_HANDLE)
   {
      Print("CSV open failed: ",GetLastError());
      return;
   }
   FileWrite(file,"requested_symbol","selected","status","description","base_currency","profit_currency","margin_currency",
      "contract_size","digits","point","tick_size","tick_value","tick_value_profit","tick_value_loss",
      "volume_min","volume_step","volume_max","volume_limit","stops_level_points","freeze_level_points",
      "trade_calc_mode","trade_mode","chart_mode","swap_mode","swap_long","swap_short","swap_rollover3days",
      "bid","ask","last","tick_volume","tick_time_msc","tick_time_server_unverified","spread_price","spread_points",
      "commission","commission_status","unavailable_fields");

   string requested[];
   int count=StringSplit(InpSymbols,',',requested);
   for(int i=0;i<count;i++)
   {
      string symbol=requested[i];
      StringTrimLeft(symbol); StringTrimRight(symbol);
      if(symbol=="") continue;
      bool selected=SymbolSelect(symbol,true);
      long trade_mode=0,chart_mode=0,calc_mode=0,swap_mode=0,stops=0,freeze=0,rollover3=0;
      long digits=0;
      double contract=0,point=0,tick_size=0,tick_value=0,tick_profit=0,tick_loss=0;
      double vmin=0,vstep=0,vmax=0,vlimit=0,swap_long=0,swap_short=0;
      string missing="";
      string description="",base="",profit="",margin="";
      bool exists=ReadString(symbol,SYMBOL_DESCRIPTION,description,missing);
      MqlTick tick; ZeroMemory(tick);
      bool tick_ok=exists && SymbolInfoTick(symbol,tick);
      if(exists)
      {
         ReadString(symbol,SYMBOL_CURRENCY_BASE,base,missing);
         ReadString(symbol,SYMBOL_CURRENCY_PROFIT,profit,missing);
         ReadString(symbol,SYMBOL_CURRENCY_MARGIN,margin,missing);
         ReadInteger(symbol,SYMBOL_DIGITS,digits,missing);
         ReadInteger(symbol,SYMBOL_TRADE_MODE,trade_mode,missing);
         ReadInteger(symbol,SYMBOL_CHART_MODE,chart_mode,missing);
         ReadInteger(symbol,SYMBOL_TRADE_CALC_MODE,calc_mode,missing);
         ReadInteger(symbol,SYMBOL_SWAP_MODE,swap_mode,missing);
         ReadInteger(symbol,SYMBOL_TRADE_STOPS_LEVEL,stops,missing);
         ReadInteger(symbol,SYMBOL_TRADE_FREEZE_LEVEL,freeze,missing);
         ReadInteger(symbol,SYMBOL_SWAP_ROLLOVER3DAYS,rollover3,missing);
         ReadDouble(symbol,SYMBOL_TRADE_CONTRACT_SIZE,contract,missing);
         ReadDouble(symbol,SYMBOL_POINT,point,missing);
         ReadDouble(symbol,SYMBOL_TRADE_TICK_SIZE,tick_size,missing);
         ReadDouble(symbol,SYMBOL_TRADE_TICK_VALUE,tick_value,missing);
         ReadDouble(symbol,SYMBOL_TRADE_TICK_VALUE_PROFIT,tick_profit,missing);
         ReadDouble(symbol,SYMBOL_TRADE_TICK_VALUE_LOSS,tick_loss,missing);
         ReadDouble(symbol,SYMBOL_VOLUME_MIN,vmin,missing);
         ReadDouble(symbol,SYMBOL_VOLUME_STEP,vstep,missing);
         ReadDouble(symbol,SYMBOL_VOLUME_MAX,vmax,missing);
         ReadDouble(symbol,SYMBOL_VOLUME_LIMIT,vlimit,missing);
         ReadDouble(symbol,SYMBOL_SWAP_LONG,swap_long,missing);
         ReadDouble(symbol,SYMBOL_SWAP_SHORT,swap_short,missing);
      }
      string status=!exists ? "missing_on_server" : (!tick_ok ? "symbol_found_no_current_tick" : "ok");
      datetime tick_time=(datetime)tick.time;
      double spread=tick_ok ? tick.ask-tick.bid : 0.0;
      double spread_points=(tick_ok && point>0.0) ? spread/point : 0.0;
      if(missing!="" && exists) status="properties_incomplete";
      FileWrite(file,CsvEscape(symbol),BoolText(selected),status,CsvEscape(description),base,profit,margin,
         DoubleToString(contract,8),(string)digits,DoubleToString(point,10),DoubleToString(tick_size,10),
         DoubleToString(tick_value,8),DoubleToString(tick_profit,8),DoubleToString(tick_loss,8),
         DoubleToString(vmin,8),DoubleToString(vstep,8),DoubleToString(vmax,8),DoubleToString(vlimit,8),
         (string)stops,(string)freeze,(string)calc_mode,(string)trade_mode,(string)chart_mode,(string)swap_mode,
         DoubleToString(swap_long,8),DoubleToString(swap_short,8),(string)rollover3,
         DoubleToString(tick.bid,(int)digits),DoubleToString(tick.ask,(int)digits),DoubleToString(tick.last,(int)digits),
         (string)tick.volume,(string)tick.time_msc,TimeToString(tick_time,TIME_DATE|TIME_SECONDS),
         DoubleToString(spread,(int)digits),DoubleToString(spread_points,2),"unknown_requires_broker_confirmation","unknown",CsvEscape(missing));
   }
   FileClose(file);

   int meta=FileOpen(meta_name,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(meta==INVALID_HANDLE)
   {
      Print("CSV saved; metadata open failed: ",GetLastError());
      return;
   }
   FileWriteString(meta,"capture_utc="+TimeToString(TimeGMT(),TIME_DATE|TIME_SECONDS)+"Z\r\n");
   FileWriteString(meta,"capture_local_terminal="+TimeToString(TimeLocal(),TIME_DATE|TIME_SECONDS)+"\r\n");
   FileWriteString(meta,"trade_server_time="+TimeToString(TimeTradeServer(),TIME_DATE|TIME_SECONDS)+"\r\n");
   FileWriteString(meta,"tick_clock_source=tick.time_msc (per-symbol in CSV)\r\n");
   FileWriteString(meta,"account_server="+AccountInfoString(ACCOUNT_SERVER)+"\r\n");
   FileWriteString(meta,"account_login=not_collected\r\n");
   FileWriteString(meta,"account_balance=not_collected\r\n");
   FileWriteString(meta,"commission=unknown_requires_broker_confirmation; no assumption of zero\r\n");
   FileWriteString(meta,"utcClockApproved=false\r\n");
   FileWriteString(meta,"read_only=true; no orders, positions, deal history or account balance queried\r\n");
   FileWriteString(meta,"files_directory=Terminal Common Files\r\n");
   FileClose(meta);
   Print("Read-only contract snapshot written to Common Files: ",csv_name," and ",meta_name);
}
