# Agente padroes: notas (BTCUSD, protocolo lab-v1)

Observação: Investopedia, StockCharts e TradingView não abriram via WebFetch neste ambiente. As fontes citadas vieram da busca web (XTB, LuxAlgo, MetaTrader 5 Help, StockSharp, Unger Academy, mql5) e dos livros dos autores.

## L13_heikin_ashi: tendência Heikin Ashi
- Fonte: Valcu (TASC 2004); xtb.com/en/education/heikin-ashi; luxalgo.com; doc.stocksharp.com (Heikin Ashi Consecutive).
- Regra: n velas HA de alta sem sombra inferior → compra (espelho na venda); sai na 1ª vela HA de cor oposta; stop k*ATR14. Execução a preço real.
- Grade: n 1–4, k 1,5/2,5/3,5, side; H1/H4/D1 (72 combinações).
- Veredito: **REPROVADA_VALIDACAO**. Escolha D1 n=1 k=1,5 só compra.
  Dev 136 trades, +81,4R, PF 3,34, DD 4,3R | Val 55 trades, −5,2R, PF 0,75, DD 9,8R (stress −6,6R). DSR 0,002.
- Interpretação: no desenvolvimento (2016–2020, alta forte do BTC) qualquer regra comprada de tendência parece ótima; na validação 2021–2022 virou prejuízo.

## L14_alligator_fractal: Alligator + fractal (Bill Williams)
- Fonte: Williams, Trading Chaos/New Trading Dimensions; metatrader5.com (Alligator: SMMA mediana 13/8/5, deslocamentos 8/5/3); nepafx.yolasite.com/fractals.php; doc.stocksharp.com (2077 Bill Williams).
- Regra: fechamento rompe o último fractal de alta que está acima dos dentes → compra (espelho na venda); opcional Alligator alinhado; sai ao fechar do outro lado de lábios/dentes/mandíbula; stop k*ATR14.
- Grade: align, linha de saída, k 2/3, side; H1/H4/D1 (72).
- Veredito: **REPROVADA_VALIDACAO**. Escolha H4 sem alinhamento, saída pela mandíbula, k=2, só compra.
  Dev 181 trades, +206,6R, PF 3,85, DD 8,2R | Val 82 trades, −8,6R, PF 0,80, DD 18,2R (stress −13,1R). DSR 0,0.
- Interpretação: o resultado brilhante no desenvolvimento era o bull market de 2016–2020; a validação desmentiu.

## L15_floor_pivots: pivôs clássicos diários
- Fonte: daytradingtoolkit.com (pivot point day trading); doc.stocksharp.com (Pivot Point Reversal); c.mql5.com pivot_trading.pdf; stockdoctor.
- Regra original: P/R1/S1/R2/S2 do dia UTC anterior. Rejeição: toca S1 e fecha acima com corpo de alta, alvo P (espelho em R1). Rompimento: fecha acima de R1, alvo R2 (espelho em S1/S2). Stop k*ATR, saída por tempo.
- Grade: modo, k, hold 12/24/48h, side; M15/H1/H4 (144). **REPROVADA_DESENVOLVIMENTO** (melhor: M15 rompimento comprado, 731 trades, +12,3R, PF 1,04, vizinhos PF 0,88; a rejeição foi negativa).
- Refinamento r1 (L15_floor_pivots_r1, só olhando o desenvolvimento): só rompimento, filtro EMA(L), saída quando o fechamento volta para o outro lado do P, alvo R2 opcional. 216 combinações.
  **REPROVADA_VALIDACAO**. Escolha H4 L=200, sem alvo, k=1,5, hold 96h, só compra.
  Dev 211 trades, +136,5R, PF 2,66, DD 6,5R | Val 76 trades, −1,4R, PF 0,96, DD 9,1R (stress −6,4R). DSR 0,028.
- Interpretação: a rejeição nos pivôs não teve vantagem no BTC. O rompimento com filtro de tendência só funcionou no período de alta e ficou no zero a zero na validação. Não pode ser reajustado.

## L16_engulfing_trend: engolfo a favor da tendência
- Fonte: Nison (definição); TradingView "Optimized Engulfing Strategy" (filtro de média, stop além do padrão, alvo em R); Unger Academy (teste de engolfo).
- Regra: engolfo de corpo (corpo ≥ minbody*ATR) com fechamento acima da SMA(L) → compra (espelho na venda); stop além da mínima/máxima dos 2 candles (mín. 0,5 ATR); alvo tr*R; saída após 20 candles.
- Grade: L 100/200, minbody 0/0,5, tr 1,5/2/3, side; H1/H4/D1 (72).
- Veredito: **REPROVADA_VALIDACAO**. Escolha D1 L=100, minbody 0, alvo 3R, só compra.
  Dev 58 trades, +47,0R, PF 2,66, DD 5,3R | Val 16 trades, +1,4R, PF 1,135 (abaixo de 1,15), DD 4,9R (stress +0,8R). DSR 0,26.
- Interpretação: foi a que menos piorou fora da amostra, mas ficou abaixo do mínimo e com pouquíssimas operações. É ruído e não serve como sinal.

## Padrão geral
As escolhas de todas foram "só compra" e vieram de 2016–2020, quando o BTC subiu muito. Com isso, a calibração tende a premiar exposição comprada, não a regra em si. Os DSR muito baixos confirmam que a escolha provavelmente foi sorte.
