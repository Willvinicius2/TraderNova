# r6-regime — rodada 6, bloco 10 (TV72–TV75), BTCUSD, protocolo lab-v3

Todas sem stop no original: stop de proteção k×ATR14. Decisão no fechamento, entrada na abertura seguinte. Nenhum refinamento feito: TV73 e TV75 reprovaram na validação (o protocolo proíbe reajuste), TV72 e TV74 saíram CANDIDATA.

## TV72 Change-Point Detection (CUSUM) — LuxAlgo
- Fonte: luxalgo.com/library/indicator/change-point-detection-cusum ; código: port fiel do Pine em deepentropy `change-point-detection.ts`. Não repinta.
- Regra: CUSUM do z-score dos log-retornos (SMA/desvio de L candles); compra quando sPos > h, vende (both) quando sNeg < −h; sai/inverte na mudança oposta.
- Grade: L {30,50,100} × h {3,4,5} × slack {0,25;0,5;0,75} × stop {2,3} ATR × lado {long,both} × H1/H4/D1 = 324.
- Escolhida: H4, L=30, h=3, slack=0,5, stop 2 ATR, **só compra**. DSR 0,66.
- Dev: 71 trades, +153,5R, PF 5,07, DD 5,5R (2,8%), 5/5 anos. Val: 27, +13,1R, PF 1,79, DD 9,9R (4,95%), sem a maior +1,37R (stress +11,7R). Reserva: 61, +100,3R, PF 3,36, DD 7,9R.
- Placebo (entradas embaralhadas, mesma saída): mediana dev +114,8R PF 3,30; val +1,1R PF 1,06; reserva +44,8R PF 1,95 (o real fica acima em 18–20 de 20 sorteios).
- Teste cruzado H4: EURUSD reprova nas 3 fases (dev −2,0R, val −10,1R, reserva +0,1R). USDJPY: dev −9,7R (reprova), val +10,3R (sem a maior ≤ 0), reserva +8,5R (passa).
- Leitura: CANDIDATA, mas só compra, e o placebo leva a maior parte do resultado no dev e na reserva. Boa parte da vantagem vem de estar comprado na alta do BTC e de sair na mudança para baixo. A validação depende da maior operação (sem ela, +1,4R). Não generaliza para câmbio.

## TV73 Random Walk Index — Poulos / everget
- Fonte: Pine de everget `oscillators/random_walk_index.pine` ; tradingsim.com/blog/random-walk-index.
- Regra: RWIhigh = (H − L[n])/(ATR(n)·√n), RWIlow espelhado; compra quando RWIhigh cruza acima do RWIlow com RWIhigh > thr, vende no espelho; sai no cruzamento oposto.
- Grade: n {10,14,20,30} × thr {0,8;1,0;1,2} × stop {2,3} × lado × 3 TF = 144.
- Escolhida: H1, n=20, thr=0,8, stop 3 ATR, both. DSR 0,001 (aviso).
- Dev: 142 trades, +26,9R, PF 1,64, DD 5,7R, 4/5 anos. Val: 38, +3,0R, PF 1,21, sem a maior −2,4R, stress −0,1R → **REPROVADA_VALIDACAO**.
- Leitura: vantagem pequena no dev e DSR quase zero, então era provável sorte na seleção. Sumiu em 2021–22.

## TV74 Relative Volatility Index (refinado 1995) — Dorsey / everget
- Fonte: Pine de everget `oscillators/relative_volatility_index.pine` ; luxalgo.com/library/concept/relative-volatility-index.
- Regra: RVI = média do RVI(máxima) e RVI(mínima) (desvio 10, EMA 14); compra no cruzamento acima de lvl (opcional: acima da EMA de tendência), vende abaixo de 100−lvl; sai no cruzamento de 50.
- Grade: lvl {50,55,60} × tendência {0,100,200} × stop {2,3} × lado × 3 TF = 108.
- Escolhida: H4, lvl=60, sem filtro de tendência, stop 2 ATR, **só compra**. DSR 0,999.
- Dev: 353 trades, +155,9R, PF 2,44, DD 7,1R, 5/5 anos. Val: 140, +7,9R, PF 1,169 (no limite de 1,15), DD 13,3R (6,6%), sem a maior +2,7R, stress +0,6R. Reserva: 282, +58,3R, PF 1,53, DD 18,1R (9,0%), stress +34,7R (DD no stress 14,4%, acima de 10%; o motor só confere DD no custo base).
- Placebo: mediana dev +89,9R PF 1,58; val −14,8R PF 0,78; reserva +38,7R PF 1,31 (o real fica acima em 18–20 de 20).
- Teste cruzado H4: EURUSD reprova nas 3 fases (dev −9,9R; val +1,7R PF 1,03; reserva +3,3R PF 1,05). USDJPY: dev +19,1R PF 1,16 (passa), val +5,8R PF 1,10 (reprova), reserva −4,0R (reprova).
- Leitura: CANDIDATA no limite, só compra. Na validação passa no limite (PF 1,17, stress quase zero). Ganha do placebo, mas o placebo também lucra muito no dev e na reserva (viés de alta). Fraca fora do BTC.

## TV75 Polarized Fractal Efficiency — Hannula
- Fonte: definição de Hannula (TASC jan/1994) via luxalgo.com/library/concept/polarized-fractal-efficiency e agenatrader. Pine não clonado. Variante em variação % (em dólares o termo n² some no preço do BTC).
- Regra: PFE(n) suavizado por EMA(m); compra no cruzamento acima de +thr, vende abaixo de −thr; sai no cruzamento de 0.
- Grade: n {10,14,20} × m {5,8} × thr {0,25,50} × stop {2,3} × lado × 3 TF = 216.
- Escolhida: H4, n=14, m=8, thr=50, stop 2 ATR, só compra. DSR 0,997.
- Dev: 240 trades, +147,6R, PF 2,56, DD 5,7R, 5/5 anos. Val: 86, −27,0R, PF 0,51, DD 32,9R (16,5%) → **REPROVADA_VALIDACAO**.
- Leitura: bom no dev só por surfar a alta; quebrou forte em 2021–22.
