# r7-candle-volume (rodada 7, lab-v4, BTCUSD)

Bloco 14 da FILA_TRADINGVIEW: candle, volume e Renko. As 4 estratégias passaram no desenvolvimento e todas reprovaram na validação (2021–2022). Como a validação já tinha sido aberta, o protocolo não permite refinar nenhuma delas. A reserva não foi aberta.

## TV88 Full Candle [Alorse]
- Fonte: Pine original em github.com/Alorse/pinescript-strategies (`strategies/other/Full Candle.pine`). A página da StockSharp (doc.stocksharp.com, 0424_Full_Candle) descreve a mesma regra.
- Regra: vela de alta cuja sombra superior é no máximo shadow% do range e que fecha acima da EMA(lenA) dá compra. A venda é o espelho. A compra sai na primeira vela de alta que fecha acima de entrada × (1 + exitpct%). O sinal oposto inverte a posição. O Pine usa exitpct = 0,2%; a grade também testou 1% e 2%, porque 0,2% fica abaixo do custo de ida e volta. O Pine não tem stop ligado, então usei stop de 2,5×ATR14. O preço de entrada é acompanhado por uma simulação local igual à do motor; conferi que todas as saídas por sinal ficaram acima do alvo.
- Calibrado: lenA, shadow, exitpct e side. Foram 216 combinações.
- Escolhida: H4 com lenA=20, shadow=10, exitpct=2 e só compra. Veredito: **REPROVADA_VALIDACAO**.
- Desenvolvimento: 371 trades, +59,1R, PF 1,50, DD 9,5R (4,8%), 4 de 5 anos positivos, DSR 0,90.
- Validação: 155 trades, -2,6R, PF 0,96. No custo stress, -8,7R e PF 0,86.
- Interpretação: a regra acerta muito (70%) mas ganha pouco por operação, e a vantagem do desenvolvimento era a alta do BTC com o filtro de EMA. Em 2021–22 a vantagem sumiu.

## TV89 Highest Volume Bar Range (tradeswithashish)
- Fonte: tradingview.com/script/KJB8dEnc. O Pine está em f13end/tradingview-custom-indicators (`strategies/Volume Bar Breakout and Breakdown`).
- Regra: a faixa é a máxima e a mínima do candle de maior volume entre os últimos lookback. A compra vem quando o fechamento rompe a máxima da faixa com volume acima da SMA20, volume acima do candle anterior e fechamento na metade de cima do candle. A venda é o espelho. O original é um indicador sem saída: aqui a posição sai no sinal oposto ou num alvo opcional (target_r), com stop k×ATR14.
- Calibrado: lookback, target_r, k e side. Foram 144 combinações.
- Escolhida: H4 com lookback=150, sem alvo, k=1,5 e só compra. Veredito: **REPROVADA_VALIDACAO**.
- Desenvolvimento: 63 trades, +238R, PF 5,75, DD 12,5R (6,2%), 4 de 5 anos positivos. O DSR foi 0,51, no limite, e sem a maior operação sobram +122R.
- Validação: 25 trades, -11,6R, PF 0,49. No custo stress, -13,4R.
- Interpretação: o resultado dependia de poucas operações longas surfando as altas de 2017 e 2019–20. É o padrão "só compra com poucos trades" da lição da rodada 5, e reprovou como esperado.

## TV90 Open Close Cross R5.1 NoRepaint (JustUncleL)
- Fonte: tradingview.com/script/9wda3yUw (estratégia) e BLY1wfiD (alertas). O port está em deepentropy `open-close-cross.ts`.
- Regra: a mesma média é aplicada ao fechamento e à abertura. A compra vem quando a média do fechamento cruza acima da média da abertura; a venda vem no cruzamento abaixo e a posição inverte. O original roda num tempo gráfico maior (×6) com o candle anterior já fechado. Aqui, como no port, o multiplicador virou período efetivo no próprio tempo gráfico (len = 8×mult), sem candle em formação. O script tem SL/TP desligados, então usei stop k×ATR14.
- Calibrado: tipo de média (SMA, EMA, DEMA, SMMA, ZEMA), len, k e side. Foram 240 combinações.
- Escolhida: D1 com SMA de 32, k=2 e os dois lados. Veredito: **REPROVADA_VALIDACAO**.
- Desenvolvimento: 118 trades, +121R, PF 4,79, DD 5,8R (2,9%), 5 de 5 anos positivos, DSR 0,91.
- Validação: 52 trades, -2,1R, PF 0,86. No custo stress, -3,2R.
- Interpretação: num BTC 24/7, SMA(fech) − SMA(abert) ≈ (fech − abert de 32 candles atrás)/32. Na prática a regra é momento de série temporal (parente do L04 TSMOM e do TV39). O desenvolvimento foi excelente e não se repetiu em 2021–22.

## TV91 Renko ATR overlay (LonesomeTheBlue)
- Fonte: tradingview.com/script/rZs7YdMI-Renko-Candles-Overlay, com espelho em luxalgo.com/library. O port está em deepentropy `renko-candles-overlay.ts`.
- Regra: os tijolos Renko têm o tamanho do ATR arredondado (2 dígitos significativos) dividido por div e são calculados só com fechamentos de candles já fechados, sem repintura. A tendência vira com 2 tamanhos contra. A compra vem na virada para alta (nbrick=1) ou no 2º tijolo de alta (nbrick=2); a venda é o espelho, e a posição sai na virada oposta. Stop k×ATR14.
- Calibrado: div (4, 2, 1), atrlen, nbrick, k e side. Foram 144 combinações.
- Escolhida: H4 com tijolo de 1 ATR14, nbrick=2, k=3 e só compra. Veredito: **REPROVADA_VALIDACAO**.
- Desenvolvimento: 115 trades, +123R, PF 3,98, DD 5,8R (2,9%), 5 de 5 anos positivos, DSR 0,985.
- Validação: 49 trades, -3,1R, PF 0,87. No custo stress, -4,7R e DD 10,8R (5,4%).
- Interpretação: é seguidor de tendência por distância fixa (parente do L01). Só compra, ganhou em 2016–20 e perdeu pouco, mas perdeu, em 2021–22.

## Observações
- Nenhum bug encontrado no motor.
- Em todas as quatro, a melhor combinação do desenvolvimento foi "só compra" ou equivalente a momento, apesar do critério de 4 de 5 anos. Isso confirma a lição: o lab-v4 deixa passar no desenvolvimento estratégias que ganham por estar compradas na alta de 2016–2020.
