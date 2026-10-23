# r9-dados — terceiro tipo de ativo (ouro e Nasdaq 100)

Agente de dados, 23/10/2026. Nada foi calibrado nem testado nestes ativos; protocol.json NÃO foi editado.

## Resultado

| Ativo | Fonte | Período gravado | H1 / H4 / D1 | Manifesto |
|---|---|---|---|---|
| NAS100 | HistData NSXUSD M1 (CFD do Nasdaq-100), via github.com/hizawye/better-backtest @ c95db5a | 14/11/2010 – 13/02/2026 | 90.368 / 24.265 / 3.952 | dados/manifest_NAS100.json |
| XAUUSD | XAU/USD M1 de servidor MetaTrader (Kaggle/HF ZombitX64), via 3 repositórios parshant65-lang | 03/01/2010 – 21/03/2025 | 89.136 / 24.158 / 3.939 | dados/manifest_XAUUSD.json |

Arquivos em research/cache/lab/{NAS100,XAUUSD}_{H1,H4,D1}.csv.gz (time UTC, open, high, low, close, volume). Não fiz M15.
PAXGUSDT (Binance) não foi necessário: o ouro abriu com 15 anos.

## Cuidados com o fuso (o mais importante)
- **NAS100**: a HistData diz "EST fixo, sem horário de verão", mas os payrolls (08:30 NY) caíam 60 min atrasados em todo verão dos EUA com +5h fixo. A fonte segue o relógio de Nova York com horário de verão; convertido com tz America/New_York. Depois da correção payroll e abertura 09:30 caem no minuto certo.
- **XAUUSD**: o espelho chama de UTC, mas é hora do servidor MT = NY + 7h (UTC+2/+3). Corrigido; payroll cai no minuto 0. Validado contra Dukascopy 2011 (FX-Data): diferença mediana -0,35 USD (≈ bid vs mid), correlação horária 0,973 sem defasagem.

## Problemas conhecidos dos dados
- NAS100: sem volume (volume gravado = minutos com cotação no candle). Falta a semana 20–24/02/2017. De 20/02/2023 a ~31/07/2023 só 16–17 horas por dia (faltam horas fora do pregão) — cai na reserva proposta. Preço tipo índice à vista (bate com o NDX), não futuro: sem rolagem, mas CFD cobra financiamento overnight que o motor não modela.
- XAUUSD: corretora desconhecida e cadeia de cópias (Kaggle → HF → GitHub); fonte primária Dukascopy só existe aqui para 2011–jun/2018. A fonte tem buracos grandes de 24/03/2025 em diante, por isso o corte em 21/03/2025.

## Proposta para protocol.json (o coordenador aplica)

```json
"XAUUSD": {
  "source": "XAU/USD 1 minuto de servidor MetaTrader (dataset Kaggle/Hugging Face ZombitX64 2004–2025) espelhado em github.com/parshant65-lang/Gold-XAUUSD-1m-{2010-2014,2015-2019,2020-2025}-Historical-Data (commits no manifesto), hora do servidor (NY+7h) convertida para UTC e reamostrada. Validado contra Dukascopy 2011. Manifesto: research/lab/dados/manifest_XAUUSD.json.",
  "costSide": {"base": 0.00012, "stress": 0.00025},
  "costNote": "Base 0,012% por lado (≈0,15 USD com ouro a 1.250, ≈0,30 a 2.500; ida e volta ≈0,3–0,6 USD): meio spread ECN (spread Dukascopy mediano 0,42 USD em 2011) + comissão + slippage. Stress 0,025% por lado (≈0,6–1,2 USD ida e volta), perto de conta standard. Preço da fonte ≈ bid, então o spread inteiro precisa caber no custo. Swap overnight não modelado.",
  "periods": {
    "warmup": ["2010-01-04", "2011-01-01"],
    "development": ["2011-01-01", "2018-01-01"],
    "validation": ["2018-01-01", "2021-01-01"],
    "reserve": ["2021-01-01", "2025-03-22"]
  },
  "note": "Desenvolvimento 2011–2017: topo de 2011, crash de 2013 e baixa até 2015 e lateralidade; validação 2018–2020: retomada e alta de 2019–2020 até o recorde de ago/2020; reserva 2021–mar/2025: lateral até 2023 e alta forte 2024–25. Fonte de corretora desconhecida (ver manifesto)."
},
"NAS100": {
  "source": "HistData NSXUSD 1 minuto (CFD do Nasdaq-100, bid) via github.com/hizawye/better-backtest commit c95db5a (JSON mensais, SHA-256 dos ZIPs no manifesto), relógio de Nova York convertido para UTC e reamostrado. Manifesto: research/lab/dados/manifest_NAS100.json.",
  "costSide": {"base": 0.0001, "stress": 0.0002},
  "costNote": "Base 0,01% por lado (≈1,5 ponto com o índice a 15.000; ida e volta ≈3 pontos com 1–2 pontos de spread de CFD + slippage). Stress 0,02% por lado. Em 2011–2013 (índice 2.300–3.500) 1 ponto de spread pesa 0,03–0,04%, então o base subestima o início do desenvolvimento e o stress fica perto do real. Financiamento overnight do CFD (~5–8% a.a.) não modelado: penaliza operações de vários dias.",
  "periods": {
    "warmup": ["2010-11-15", "2012-01-01"],
    "development": ["2012-01-01", "2019-01-01"],
    "validation": ["2019-01-01", "2022-01-01"],
    "reserve": ["2022-01-01", "2026-02-14"]
  },
  "note": "Desenvolvimento 2012–2018: alta longa com correções de 2015–16 e queda de dez/2018; validação 2019–2021: covid e alta forte; reserva 2022–fev/2026: baixa de 2022, IA 2023–24, tombo das tarifas em abr/2025. Reserva tem 5 meses de 2023 com horas faltando (ver manifesto)."
}
```

As duas séries cruzam no tempo com BTC/EURUSD/USDJPY: os testes são independentes no ativo, não no tempo.

## O que tentei
- **Abriu**: git clone/raw.githubusercontent.com, busca de código/repos do GitHub (MCP), PyPI, npm.
- **Bloqueado** (curl 000): datafeed.dukascopy.com, stooq, Yahoo Finance, histdata.com, FRED, data.nasdaq.com, Hugging Face, Kaggle, Alpha Vantage, FMP, api.binance.com; codeload.github.com 403.
- **FX-Data**: XAUUSD-DS (Dukascopy) tem ramos 2011–2018 (~7,5 anos) — usado só para validar 2011 (o processamento leva vários minutos por mês; parei depois de 2011). XAGUSD 2010–2018. Não existe índice (USA100IDXUSD/NAS100 não existem no FX-Data).
- **philipperemy/FX-1-Minute-Data**: nenhum dado no histórico do git (só scripts).
- **HistData XAUUSD em repositórios**: Craig-Pang/QuantXAU (2021–2025), Paaktingc/forex_bot (2023–mai/2026), Techris93/xauusd e darkforest-x/fable-trading (só checksums/metadados, sem os ZIPs). Ninguém com 2009–2026 completo.
- getdata-finance/xauusd-* são amostras (produto pago). FeziweMelvin/XAUUSD-Gold-Price só diário.
- Alternativa reserva para ouro: Binance PAXGUSDT 1h (desde 2020) pelo espelho S3 — não usada.

## Reproduzir
Scripts usados (scratchpad, não versionados): nas_m1.py (JSON → M1 UTC via America/New_York), gold_m1.py + gold_fix.py (CSV diários → M1, hora −7h → NY → UTC), resample.py (H1/H4/D1, mesmas regras do data.py), check_nfp.py (minuto do pico no payroll). Se for para valer, vale levar essas funções para data.py (--histdata-nas / --mtgold).
