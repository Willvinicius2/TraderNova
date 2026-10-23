# Rodada 3 – r3-filtros (filtros/médias da comunidade TradingView)

Ativo BTCUSD, protocolo lab-v2. Desenvolvimento 2016–2020, validação 2021–2022, reserva 2023–2026.
As 4 estratégias passaram no desenvolvimento e **reprovaram na validação**. Por isso a reserva não foi aberta e nenhum refinamento foi feito, porque o protocolo proíbe reajustar depois de ver a validação.
Fizemos um teste de ausência de olhar o futuro: os sinais calculados com os dados cortados em 4 pontos são idênticos aos sinais calculados com a série completa.

## TV28_coral_trend – Coral Trend (LazyBear)
- **Fonte:** script do TradingView (qyUwc2Al e a versão pine-v4 AzQo1gRi). O código Pine foi conferido em cópias de terceiros (Tradovate, AFL da MarketCalls) por meio de resumos de busca, porque o TradingView não abre aqui.
- **Regra:** a linha bfr vem de 6 EMAs em cascata (filtro T3 de Tillson). Compra quando a cor vira verde (bfr sobe) e vende quando vira vermelha. O Pine não tem stop, então usamos k×ATR14 como stop de proteção.
- **Grade:** sm {13,21,34,55}, cd {0,2;0,4;0,6}, k {2,3}, lado; tempos gráficos H1/H4/D1, total de 144.
- **Escolhida:** H4, sm=34, cd=0,2, k=2, só compra.
- **Desenvolvimento:** 125 trades, +214R, PF 4,19, DD 7,7R (3,9%).
- **Validação:** 54 trades, −14,3R, PF 0,64, DD 16,0R (8,0%), stress −17,3R.
- **Veredito:** REPROVADA_VALIDACAO.
- **Interpretação:** seguiu a alta de 2016–2020 e perdeu no vaivém de 2021–2022, como Supertrend, Hull e Range Filter.

## TV29_half_trend – HalfTrend (everget)
- **Fonte:** Pine original do autor, em github.com/everget/tradingview-pinescript-indicators (trailing_stops/halftrend.pine).
- **Regra:** compra no sinal Buy (trend 1→0) e vende no Sell, e sai no sinal oposto. channelDeviation só desenha o canal e não muda os sinais, por isso ficou fora da grade. Stop de proteção k×ATR14.
- **Grade:** amplitude {2,3,5,8,13,21}, k {2,3,4}, lado; total de 108.
- **Escolhida:** H4, amplitude=5, k=2, só compra.
- **Desenvolvimento:** 127 trades, +189R, PF 3,89, DD 6,8R (3,4%).
- **Validação:** 59 trades, −14,9R, PF 0,62, DD 17,0R (8,5%), stress −17,9R.
- **Veredito:** REPROVADA_VALIDACAO.
- **Interpretação:** é mais uma virada de tendência que dependeu do mercado de alta.

## TV30_gaussian_channel – Gaussian Channel (DonovanWall)
- **Fonte:** script WpVY7GKW e a "Gaussian Channel Strategy" (erJi1tWf). As fórmulas de beta, alpha e bandas foram conferidas em resumos de busca e no port MQL5.
- **Implementação:** o filtro de N polos foi implementado como N EMAs em cascata com o mesmo alpha, o que é matematicamente igual à recursão f_filt9x. Usamos fonte hlc3 e deixamos os modos lag/fast desligados.
- **Regra (das estratégias públicas):**
  - Compra quando o filtro sobe e o fechamento fica acima da banda alta.
  - Sai quando o fechamento volta abaixo da banda alta ou quando o filtro cai.
  - Venda no espelho.
  - Stop = distância até a banda oposta, com mínimo de 1 ATR.
- **Grade:** polos {2,4,6}, período {72,144,216,288}, mult {1;1,414;2}, lado; total de 216.
- **Escolhida:** H4, polos=2, período=216, mult=1,0, só compra.
- **Desenvolvimento:** 181 trades, +146R, PF 4,26, DD 4,1R (2,1%).
- **Validação:** 70 trades, −6,7R, PF 0,70, DD 10,4R (5,2%), stress −9,3R.
- **Veredito:** REPROVADA_VALIDACAO.

## TV31_mcginley – McGinley Dynamic (virada da inclinação)
- **Fonte:** Pine do everget (movings/mcginley_dynamic.pine) e Investopedia.
- **Regra:** MD = MD[1] + (C−MD[1])/(K·N·(C/MD[1])^4). Compra quando a inclinação vira para cima e vende quando vira para baixo. Stop de proteção k×ATR14.
- **Detalhe de implementação:** a razão C/MD[1] foi limitada a [0,5; 2] para estabilidade numérica.
- **Grade:** N {10,14,21,34,55}, K {0,6;1}, k {2,3}, lado; total de 120.
- **Escolhida:** D1, N=34, K=0,6, k=2, compra e venda.
- **Desenvolvimento:** 84 trades, +107R, PF 6,36, DD 3,9R (1,9%).
- **Validação:** 51 trades, −4,5R, PF 0,73, DD 7,5R (3,7%), stress −5,5R.
- **Veredito:** REPROVADA_VALIDACAO.

**Leitura geral:** o desenvolvimento de 2016–2020 favorece qualquer seguidor de tendência no BTC, com PF entre 4 e 6. Na validação, todos esses seguidores perdem. O DSR alto do desenvolvimento não protege contra essa mudança de regime.
