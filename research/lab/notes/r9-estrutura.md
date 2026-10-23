# Rodada 9 — agente r9-estrutura

Ativo BTCUSD, protocolo lab-v4. As três abriram a validação e reprovaram nela. Por isso nenhuma foi refinada: o protocolo proíbe reajustar depois de ver a validação. A causalidade foi conferida (sinais calculados em dados cortados = sinais calculados na série completa).

## L49_fvg_orderblock — ICT Fair Value Gap
- Fontes: LuxAlgo, conceito Fair Value Gap; NinjaTrader, blog sobre FVG; porte do Pine "ICT FVG Buy/Sell Signals" (deepentropy/lightweight-charts-indicators); ICT (Huddleston).
- Regra: o FVG só existe no fechamento do 3º candle (mínima[i] > máxima[i-2], candle do meio com corpo >= disp×ATR). A entrada vem quando um candle posterior toca o gap e fecha acima do CE (meio do gap). O stop fica na mínima do candle 1 (order block) - 0,1 ATR, com alvo fixo em R. Venda no espelho. Filtro opcional EMA200.
- Calibrado: disp, wait, target_r, trend, side (324 combinações).
- Escolha: H4, disp 1,5, wait 20, alvo 3R, EMA200, só compra. DSR 0,85.
- Desenvolvimento: 69 trades, +42,4R, PF 2,00, DD 2,6%, 4 de 5 anos positivos.
- Validação: 17 trades, -1,75R, PF 0,87 (stress -2,5R). **REPROVADA_VALIDACAO**.
- Interpretação: o desenvolvimento escolheu "só compra acima da EMA200", ou seja, surfar a alta de 2016–2020. Em 2021–22 o gap não teve vantagem.

## L50_kumo_breakout — Ichimoku Kumo breakout
- Fontes: OANDA, guia de estratégias Ichimoku; LuxAlgo, sinais Ichimoku; Hosoda.
- Regra: o fechamento cruza a nuvem (deslocada, causal), com Chikou confirmando. Com future=yes, exige também a nuvem futura a favor. Saída na Kijun ou de volta à nuvem, stop k×ATR. Não é duplicata do L03: o gatilho do L03 é o cruzamento Tenkan/Kijun, aqui é o rompimento da nuvem.
- Calibrado: s, future, exit, k, side (144 combinações).
- Escolha: H4, s=3, future=no, saída na nuvem, k=3, both. DSR 0,97.
- Desenvolvimento: 73 trades, +230R, PF 7,1, DD 2,9%, 4 de 5 anos positivos.
- Validação: 36 trades, +9,8R, PF 1,49 (stress +8,4R), DD 3,8%. Reprovou porque o resultado fica negativo sem a maior operação (-0,25R). **REPROVADA_VALIDACAO**.
- Interpretação: é um seguidor de tendência lento, que no BTC 2016–2020 tem números enormes. Em 2021–22 o lucro depende de uma única operação. Foi a mais perto de passar das três.

## L51_atr_squeeze_breakout — Canal ATR após contração da BandWidth
- Fontes: StockCharts ChartSchool, Bollinger BandWidth; LuxAlgo, ATR Bands; Bollinger, "The Squeeze".
- Regra: percentil da BandWidth (20, 2) numa janela causal de cerca de 6 meses <= pct em algum dos últimos 5 candles. O gatilho é o fechamento cruzar SMA20 ± k×ATR20. Saída na SMA20 ou por stop móvel de 3 ATR, stop inicial stop_k×ATR. Diferente do L09 (BB dentro do Keltner + momentum) e do L12 (EMA±ATR sem filtro de contração).
- Calibrado: pct, k, stop_k, exit, side (216 combinações).
- Escolha: H4, pct 30, k 2, stop 2, saída na média, both. DSR 1,0.
- Desenvolvimento: 149 trades, +161R, PF 3,86, DD 2,4%, 5 de 5 anos positivos.
- Validação: 72 trades, -1,76R, PF 0,96 (stress -6,2R). **REPROVADA_VALIDACAO**.
- Interpretação: mais um caso da lição da rodada 5. A vantagem grande no desenvolvimento, mesmo com DSR 1,0, sumiu em 2021–22.
