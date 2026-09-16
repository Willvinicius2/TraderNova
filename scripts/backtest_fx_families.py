"""Bounded, reproducible EURUSD H1 research screen; no broker or order calls."""
import argparse,csv,math,json
from pathlib import Path
def load(p):
 r=list(csv.DictReader(open(p))); return [(int(x['time']),float(x['open']),float(x['high']),float(x['low']),float(x['close'])) for x in r]
def ema(a,n):
 out=[None]*len(a); s=sum(a[:n])/n
 for i in range(n-1,len(a)):
  s=s if i==n-1 else a[i]*2/(n+1)+s*(1-2/(n+1));out[i]=s
 return out
def run(bars,fam):
 c=[x[4] for x in bars]; h=[x[2] for x in bars];l=[x[3] for x in bars];o=[x[1] for x in bars];e20=ema(c,20);e50=ema(c,50);e200=ema(c,200); trades=[]; i=205
 while i<len(bars)-2:
  d=0
  if fam=='trend' and e50[i] and c[i]>e200[i] and e50[i]>e50[i-3] and c[i-1]<=e20[i-1] and c[i]>e20[i]: d=1
  if fam=='breakout' and i>24 and c[i]>max(h[i-24:i]) and c[i-1]<=max(h[i-25:i-1]): d=1
  if fam=='reversion' and i>20 and c[i-1]<sum(c[i-20:i-1])/20 and c[i]>sum(c[i-20:i])/20: d=1
  if fam=='rsi' and i>14:
   gains=[max(0,c[j]-c[j-1]) for j in range(i-14,i)];loss=[max(0,c[j-1]-c[j]) for j in range(i-14,i)];rs=sum(gains)/(sum(loss) or 1e-9)
   if 100-100/(1+rs)<35 and c[i]>o[i]: d=1
  if fam=='opening' and i>24:
   day=bars[i][0]//86400; prior=[j for j in range(i-24,i) if bars[j][0]//86400==day]
   if len(prior)>=2 and c[i]>max(h[j] for j in prior[-2:]) and c[i-1]<=max(h[j] for j in prior[-3:-1]): d=1
  if d:
   atr=sum(h[j]-l[j] for j in range(i-14,i))/14; entry=o[i+1]; stop=entry-1.5*atr; target=entry+2*1.5*atr; end=min(i+9,len(bars)-1); exitp=c[end];
   for j in range(i+1,end+1):
    if l[j]<=stop: exitp=stop;end=j;break
    if h[j]>=target: exitp=target;end=j;break
   r=(exitp-entry)/(entry-stop)-0.00012*entry/(entry-stop);trades.append(r);i=end+1
  else:i+=1
 wins=sum(x>0 for x in trades); grossp=sum(x for x in trades if x>0);grossl=-sum(x for x in trades if x<0); eq=peak=dd=0
 for x in trades:eq+=x;peak=max(peak,eq);dd=max(dd,peak-eq)
 return {'trades':len(trades),'netR':round(sum(trades),4),'profitFactor':round(grossp/grossl,3) if grossl else None,'drawdownR':round(dd,4),'positive':sum(trades)>0 and grossp>grossl*1.2 and dd<15}
def main():
 p=argparse.ArgumentParser();p.add_argument('--file',required=True);p.add_argument('--label',required=True);a=p.parse_args();b=load(a.file)
 families=['trend','breakout','reversion','rsi','opening']
 short=[(t,-o,-l,-h,-c) for t,o,h,l,c in b]
 out={'label':a.label,'source':str(a.file),'families':{f:{'long':run(b,f),'short':run(short,f)} for f in families}}
 print(json.dumps(out,indent=2));Path('research').joinpath('fx-screen-'+a.label+'.json').write_text(json.dumps(out,indent=2))
if __name__=='__main__':main()
