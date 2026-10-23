# r5-volume — Rodada 5, bloco 5 (fluxo de volume, TV52–TV55)

Ativo BTCUSD (volume só do Bitstamp), protocolo lab-v3. Nenhuma das quatro passou. Como todas abriram a validação, o protocolo não permite refinar nenhuma.
Os indicadores originais não têm regra de trade nem stop. A regra de entrada segue a FILA e a fonte. O stop de proteção é k×ATR14 e a saída é no sinal oposto.

## TV52 Klinger Volume Oscillator — REPROVADA_VALIDACAO
- Fonte: Pine de everget (github.com/everget/tradingview-pinescript-indicators, volume/klinger_volume_oscillator.pine) e StockCharts ChartSchool (Klinger).
- Regra: KVO = EMA34 − EMA55 do volume force. Compra quando o KVO cruza acima do sinal EMA(sig). Com side=both, vende no cruzamento para baixo. O filtro opcional EMA100 é a tendência que Klinger sugeria.
- Grade: sig 8/13/21, filtro none/ema100, k 2/3/4, side long/both, em H1/H4/D1 (108 combinações).
- Escolhida: D1, sig 21, ema100, k 2, both.
  - Dev: 101 trades, +66,7R, PF 3,90, DD 1,95%, +47R sem a maior operação.
  - Val: 30 trades, +1,5R, PF 1,152 (o mínimo é 1,15; os números arredondados escondem a diferença). Sem a maior operação fica em −1,2R. No custo stress fica em +0,9R.
- Leitura: a vantagem sumiu em 2021–22. Fica no zero a zero, e o PF bater no limite não muda isso.

## TV53 Chaikin Money Flow (CMF [Yield]) — REPROVADA_VALIDACAO
- Fonte: StockCharts ChartSchool (CMF, zona de ±0,05) e Pine "CMF [Yield]" (github.com/f13end/tradingview-custom-indicators). Usei o mf cru, sem a ALMA de exibição.
- Regra: CMF(n) = Σ(MFV)/Σ(vol). Compra quando cruza acima de +th e vende quando cruza abaixo de −th. A saída é no sinal oposto ou no zero.
- Grade: n 10/20/30, th 0/0,05/0,10, saída opposite/zero, k 2/3, side, em H1/H4/D1 (216 combinações).
- Escolhida: H4, n 30, th 0,10, opposite, k 2, só compra.
  - Dev: 78 trades, +256R, PF 6,27, DD 3%.
  - Val: 62 trades, −19,7R, PF 0,61, DD 12,3%.
- Leitura: a combinação escolhida só compra e ganhou surfando a alta. Quebrou na queda de 2022.

## TV54 Ease of Movement (Arms) — REPROVADA_RESERVA
- Fonte: TradingView Help Center (Ease of Movement, 43000502256), StockCharts (EMV) e o port do indicador embutido (deepentropy, standard/ease-of-movement.ts).
- Regra: EMV = Δhl2·(H−L)/vol, com EOM = SMA(n). Compra quando cruza acima de 0 e vende quando cruza abaixo. O filtro opcional SMA200 só deixa operar a favor da tendência.
- Grade: n 7/14/28, filtro none/sma200, k 2/3/4, side, em H1/H4/D1 (108 combinações).
- Escolhida: D1, n 28, sma200, k 2, both.
  - Dev: 58 trades, +97R, PF 8,24, DD 2%.
  - Val: 32 trades, +3,6R, PF 1,37. Sem a maior operação fica em +0,7R. Passou.
  - Reserva: 53 trades, +0,4R, PF 1,02, −5,8R sem a maior operação, −1,25R no custo stress. Reprovou.
- Leitura: foi a que chegou mais longe, mas a vantagem cai de fase em fase até zero. Não há sinal útil.

## TV55 Negative Volume Index (Fosback) — REPROVADA_VALIDACAO
- Fonte: Pine de everget (volume/negative_volume_index.pine), StockCharts (NVI) e Wikipedia (Fosback, média de 255).
- Regra: o NVI só muda nos candles com volume menor que o anterior. Compra quando o NVI cruza acima da sua EMA(sig) e vende quando cruza abaixo.
- Grade: sig 100/255/400, k 2/3/4, side, em H1/H4/D1 (54 combinações).
- Escolhida: H4, sig 400, k 2, só compra.
  - Dev: 64 trades, +754R, PF 32,7. Quase tudo vem de uma única operação de 2017 a 2018 (cerca de 666R com stop de 2 ATR no H4).
  - Val: 41 trades, −10,4R, PF 0,44.
- Leitura: é a alta de 2017 vista por um stop curto. Não tem vantagem própria.
- **Problema no calibrate.py:** esta combinação só passou no critério de 4 de 5 anos por causa de uma falha na contagem, descrita abaixo. Ela tem R negativo em 2016, nenhuma saída em 2017 e R positivo em 2018, 2019, 2020 e no "2021". Contada certo, teria reprovado no desenvolvimento.

## Possível falha no calibrate.py (não editei)
`anosPositivos` agrupa as operações pelo ano de **saída**. Uma posição fechada pelo fim do período (`fim_periodo`, na abertura de 2021-01-01) cai num 6º ano, "2021", que entra na contagem de anos positivos. Por isso os resultados mostram "6 de 5". Além disso, uma operação longa que atravessa vários anos conta como um só ano. Sugestão: limitar a contagem aos anos 2016–2020, juntando 2021 a 2020, e/ou distribuir o R pelo ano marcado a mercado.
