# Rodada 3 — r3-lazybear (scripts populares da comunidade TradingView)

Ativo BTCUSD, protocolo lab-v2. TradingView não abre aqui; regras tiradas de resumos (WebSearch) e de portes públicos do Pine. Nenhum dos scripts originais tem stop: usei k×ATR14 de proteção. Todas as quatro passaram no desenvolvimento e reprovaram na validação, por isso não houve refinamento (o protocolo proíbe reajustar depois de ver a validação). A reserva não foi aberta.

## TV24_vix_fix: CM Williams Vix Fix (ChrisMoody)
- Fonte: tradingview.com/script/og7JPrRA (resumos via WebSearch), luxalgo.com/library (cópia do script). Padrões do Pine: pd=22, bbl=20, mult=2, lb=50, ph=0,85.
- Regra: wvf=(máx. fech. 22 - mínima)/máx. fech.×100; barra verde = wvf ≥ BB superior ou ≥ 0,85×máx(wvf,50). Só compra, no início ('spike') ou no fim ('fade') da sequência verde; saída por tempo (5/10/20 candles); stop k×ATR.
- Calibrado: gatilho, tempo de saída, k (H4, D1; 36 combinações).
- Escolhido D1 fade, 20 candles, k=2. Dev: 54 trades, +35,6R, PF 2,83, DD 5,9R. Val: 21 trades, −2,5R, PF 0,75, DD 4,4R.
- Veredito: REPROVADA_VALIDACAO. Comprar depois do pânico funcionou no mercado de alta de 2016–2020 e não no período de 2021–2022.

## TV25_waddah_attar: Waddah Attar Explosion (LazyBear)
- Fonte: tradingview.com/script/iu3kKWDI (notas do autor via WebSearch); porte MQL5 do mesmo script.
- Regra: t1=(MACD−MACD[1])×sensibilidade (EMA20/40); explosão = largura BB(20,2); zona morta = RMA(TR,100)×dz. Entra quando a barra verde (vermelha) passa a ficar acima da explosão e da zona morta; sai quando cai abaixo da explosão.
- Calibrado: sensibilidade 75/150/300, zona morta 2,0/3,7, k, lado (H1/H4/D1; 72 combinações).
- Escolhido H4 sens=150, dz=3,7, k=2, só compra. Dev: 586 trades, +99,2R, PF 1,74, DD 7,1R. Val: 269 trades, −31,4R, PF 0,62, DD 35,1R (17,6% da conta).
- Veredito: REPROVADA_VALIDACAO. É seguidor de tendência curto que só ganhou no mercado de alta, e caiu forte quando o mercado ficou lateral ou em queda.

## TV26_impulse_macd: Impulse MACD (LazyBear)
- Fonte: tradingview.com/script/qt6xLfLi; fórmulas conferidas no porte freqtrade (github remiotore/freqtrade, ImpulseMACD.py) e no ProRealCode.
- Regra: canal SMMA(máx., n)/SMMA(mín., n), ZLEMA(hlc3, n); md = distância da ZLEMA para fora do canal. 'zero': entra quando md sai de 0, sai quando volta a 0; 'signal': cruzamento md × SMA(md,9).
- Calibrado: n 21/34/55, gatilho, k, lado (H1/H4/D1; 72 combinações).
- Escolhido H4 n=34, gatilho zero, k=3, só compra. Dev: 72 trades, +136,3R, PF 5,05, DD 5,2R. Val: 29 trades, −4,5R, PF 0,78, DD 12,6R.
- Veredito: REPROVADA_VALIDACAO. O lucro no desenvolvimento veio de poucas tendências longas de alta do BTC, e o efeito não se repetiu em 2021–2022.

## TV27_vfi: Volume Flow Indicator (LazyBear / Katsanos)
- Fonte: tradingview.com/script/MhlDpfdS; TASC Traders' Tips jun/2004 (Katsanos); ProRealCode. Pine: coef 0,2, vcoef 2,5, sinal EMA 5.
- Regra: fluxo de volume com corte de volatilidade e teto de volume; 'zero': VFI cruza 0 (regra de Katsanos); 'signal': VFI cruza a EMA5. Sai no cruzamento oposto.
- Calibrado: n 65/130/200, gatilho, k, lado (H1/H4/D1; 72 combinações).
- Escolhido D1 n=130, gatilho zero, k=2, compra e venda. Dev: 32 trades, +394R, PF 30,6, DD 6,0R, mas sem a maior operação só +33,5R (uma operação de 2017 gerou cerca de 360R); DSR 0,55. Val: 15 trades, +2,4R, PF 1,53, mas sem a maior operação dá −1,6R, e o mínimo exigido no D1 é 10 trades. A reprovação veio pela regra "positivo sem a maior operação".
- Veredito: REPROVADA_VALIDACAO. O resultado depende de uma única tendência e não tem vantagem de verdade.
