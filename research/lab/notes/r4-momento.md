# r4-momento — rodada 4, bloco 2 (TV40–TV43), BTCUSD, protocolo lab-v2

Todas as quatro passaram com folga no desenvolvimento (2016–2020) e reprovaram na validação (2021–2022). Como a validação já foi aberta, o protocolo não deixa refinar. Nenhuma tem stop no original: usei stop de proteção k×ATR(14). Todas são indicadores sem repintura.

## TV40_tsi — True Strength Index (Blau / everget)
- Fonte: Pine do everget (github.com/everget/tradingview-pinescript-indicators, commit 8385cc4, oscillators/tsi_true_strength_index.pine); script TradingView "True Strength Index with Zones/Alerts"; StockCharts ChartSchool.
- Regra: TSI = 100·EMA(EMA(Δ,longo),curto)/EMA(EMA(|Δ|,longo),curto), sinal = EMA(TSI). Compra quando o TSI cruza acima do sinal e vende quando cruza abaixo (com filtro opcional: compra só abaixo de 0). Sai no cruzamento oposto.
- Grade: longo 13/25/40, curto 7/13, sinal 7/13, zona 0/1, k 2/3, lado; H1/H4/D1 (288).
- Escolhido: H4, 40/7/13, sem zona, k=2, só compra. DSR 0,81.
- Dev: 396 trades, +160,5R, PF 2,12, DD 4,8%. Val: 170 trades, −17,3R, PF 0,77, DD 12,1% (stress −26,2R). **REPROVADA_VALIDACAO**.
- Leitura: cruzamento de momento seguiu bem a alta de 2016–2020, mas perdeu dinheiro de forma consistente em 2021–22.

## TV41_ttf — Trend Trigger Factor (Pee / LazyBear / everget)
- Fonte: script do LazyBear (tradingview.com/script/wSMZKu7B) com as regras do autor; Pine do everget (oscillators/trend_trigger_factor.pine).
- Regra: BP = HH(n) − LL(n)[n], SP = HH(n)[n] − LL(n), TTF = 200·(BP−SP)/(BP+SP). Compra quando cruza acima de +nível e vende quando cruza abaixo de −nível. Entre os níveis mantém a posição.
- Grade: n 10/15/20/30, nível 75/100/125, k 2/3/4, lado; H1/H4/D1 (216).
- Escolhido: H4, n=10, nível 125, k=3, só compra. DSR 0,999.
- Dev: 85 trades, +191,0R, PF 6,26, DD 2,6%. Val: 43 trades, −6,9R, PF 0,72, DD 5,5% (stress −8,3R). **REPROVADA_VALIDACAO**.
- Leitura: o PF de 6 no desenvolvimento vem de poucas tendências enormes de 2017–2020. Isso não se repetiu, então era efeito do regime, não da regra.

## TV42_tcf — Trend Continuation Factor (Pee / everget)
- Fonte: Pine do everget (oscillators/trend_continuation_factor.pine); resumo do artigo na TASC de mar/2002 (traders.com); script TradingView ymW2vLS6.
- Regra: +TCF = Σn(alta − quedas acumuladas), −TCF espelhado. Compra quando +TCF fica > 0 e vende quando −TCF fica > 0. A saída acontece quando o próprio lado deixa de ser positivo ("neutral") ou quando o lado oposto fica positivo ("opposite").
- Grade: n 20/35/50, saída neutral/opposite, k 2/3/4, lado; H1/H4/D1 (108).
- Escolhido: H4, n=20, saída opposite, k=2, compra e venda. DSR 0,90.
- Dev: 330 trades, +222,9R, PF 2,33, DD 4,1%. Val: 167 trades, −31,0R, PF 0,72, DD 16,5% (stress −39,9R). **REPROVADA_VALIDACAO**.
- Leitura: foi a pior na validação. O lado vendido e as viradas do mercado lateral de 2021–22 destruíram o resultado.

## TV43_ultimate_rsi — Ultimate RSI (LuxAlgo)
- Fonte: tradingview.com/script/17Jj7Vcg-Ultimate-RSI-LuxAlgo; LuxAlgo Library; tradução em deepentropy/lightweight-charts-indicators (commit f8e1b0e, src/community/ultimate-rsi.ts).
- Regra: o diff é a amplitude de n candles quando há nova máxima (+) ou nova mínima (−), senão Δfech. aRSI = RMA(diff)/RMA(|diff|)·50+50, sinal = EMA(aRSI,m). No modo mid opera o cruzamento de 50, no modo signal o cruzamento do sinal. Inverte a posição no sinal oposto.
- Grade: n 7/14/21/28, m 7/14/21, modo mid/signal, k 2/3, lado; H1/H4/D1 (288). No modo mid, m não tem efeito.
- Escolhido: H4, n=21, m=21, modo signal, k=3, só compra. DSR 0,91.
- Dev: 351 trades, +115,7R, PF 2,43, DD 2,3%. Val: 141 trades, −7,6R, PF 0,82, DD 7,4% (stress −12,6R). **REPROVADA_VALIDACAO**.
- Leitura: perdeu menos que as outras na validação, mas também perdeu. Não há vantagem demonstrada.

Observação geral: o padrão se repete em quase todo o bloco TV. Seguidores de momento ou tendência no H4 ficam ótimos em 2016–2020 e perdem em 2021–2022. O desenvolvimento do BTC favorece esse tipo de regra, e o DSR alto no desenvolvimento não protegeu contra isso.
