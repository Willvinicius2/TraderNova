# Agente r5-elder-williams: notas (BTCUSD, protocolo lab-v3, rodada 5)

TradingView não foi aberto diretamente, exceto o Help Center do AO (in.tradingview.com/support/solutions/43000501826), que abriu pelo WebFetch. Fórmulas tiradas dos ports em /home/user/labdata/pine (deepentropy standard/bull-bear-power.ts e elder-force.ts; everget awesome_oscillator.pine e accelerator_oscillator.pine). Nenhum dos quatro indicadores tem stop: usei k*ATR14 como stop de proteção. Todas as quatro reprovaram na validação, então nenhuma foi refinada (o protocolo proíbe).

## TV56_elder_ray: Elder-Ray em pullback
- Fonte: daytrading.com/elder-ray-index; doc.stocksharp.com (Elder Ray); luxalgo.com; port do Bull Bear Power embutido.
- Regra: compra com EMA(n) subindo e Bear Power (mín − EMA) negativo mas subindo; venda espelhada com o Bull Power (positivo mas caindo) e EMA caindo. Saída quando a EMA vira ou no sinal oposto.
- Grade: n 13/21/34, saída ema/opp, k 2/3, side long/both; H1/H4/D1 (72).
- Veredito: **REPROVADA_VALIDACAO**. Escolha D1 n=34, saída opp, k=2, both.
  Dev 118 trades, +107,4R, PF 4,86, DD 5,2R, 5/5 anos positivos | Val 37 trades, +4,2R, PF 1,28, DD 4,0R (stress +3,5R), mas **−1,1R sem a maior operação**. DSR 0,98.
- Interpretação: a validação ficou positiva só por causa de uma operação grande. Sem ela fica perto de zero, então não há vantagem que se sustente fora do desenvolvimento.

## TV57_force_pullback: Force Index(2) em pullback
- Fonte: StockCharts ChartSchool (Force Index); ta-lib.org (EFI); port do Elder Force Index embutido.
- Regra: FI = EMA2((fech − fech anterior) × volume); tendência pela EMA(t). Modo neg: entra quando o FI cruza abaixo de 0 a favor da tendência. Modo turn: entra quando o FI volta acima de 0. Venda espelhada. Saída pelo FI ou pela virada da EMA.
- Grade: t 13/22/34, modo neg/turn, saída fi/ema, k 2/3, side; H1/H4/D1 (144).
- Veredito: **REPROVADA_VALIDACAO**. Escolha D1 t=34, modo turn, saída ema, k=2, both.
  Dev 95 trades, +91,9R, PF 4,68, DD 3,9R, 5/5 anos | Val 33 trades, +2,0R, PF 1,18, DD 2,9R (stress +1,4R), mas **−2,7R sem a maior operação**. DSR 0,16 (aviso de provável sorte na seleção).
- Interpretação: mesmo quadro do TV56. Quem gera o resultado é a saída pela EMA, que segura a tendência; o gatilho do Force Index pouco acrescenta. A validação depende de uma única operação.

## TV58_ao_saucer: saucer do Awesome Oscillator
- Fonte: TradingView Help Center (AO, lido); everget awesome_oscillator.pine; cmcmarkets.com.
- Regra: AO = SMA5 − SMA34 da mediana. Compra com 3 barras acima de 0: duas vermelhas seguidas e depois uma verde. Venda espelhada abaixo de 0. Saída no cruzamento do zero ou após 2 barras contrárias, com alvo opcional em R.
- Grade: saída zero/color2, alvo 0/2/3R, k 1,5/2/3, side; H1/H4/D1 (108).
- Veredito: **REPROVADA_VALIDACAO**. Escolha H4, saída color2, sem alvo, k=2, só compra.
  Dev 338 trades, +103,5R, PF 2,19, DD 7,3R, 4/5 anos | Val 101 trades, −0,7R, PF 0,98, DD 10,5R (stress −6,0R). DSR 0,98.
- Interpretação: a escolhida é só compra e ganhava com a alta de 2016–2020. Em 2021–2022 ficou no zero a zero, ou seja, o padrão não tem vantagem própria.

## TV59_accelerator: Accelerator Oscillator
- Fonte: manual do MetaTrader 5 (Bill Williams' Indicators, AC); everget accelerator_oscillator.pine; luxalgo.com.
- Regra: AC = AO − SMA5(AO). Compra com 2 colunas verdes acima de 0 ou 3 verdes abaixo de 0. Venda espelhada. Saída na 1ª ou 2ª coluna contrária, ou no sinal oposto, com alvo opcional.
- Grade: saída red1/red2/opp, alvo 0/2R, k 2/3, side; H1/H4/D1 (72).
- Veredito: **REPROVADA_VALIDACAO**. Escolha D1, saída opp, sem alvo, k=2, só compra.
  Dev 143 trades, +55,7R, PF 2,74, DD 4,5R, 5/5 anos | Val 55 trades, −3,1R, PF 0,82, DD 7,8R (stress −4,2R). DSR 0,98.
- Interpretação: estar comprado no D1 do BTC rendeu no desenvolvimento. Na validação o sinal do AC perdeu.

## Observação sobre o calibrate.py (não editado)
- Em `anosPositivos` (calibrate.py, ~linha 127) os anos são agrupados pelo ano de **saída** da operação. A posição fechada como "fim_periodo" em 01/01/2021 cria um sexto "ano" (2021) dentro do desenvolvimento: no TV56 saiu anosPositivos=6 com anosTotal=5. Isso pode fazer passar uma combinação com só 3 dos 5 anos reais positivos, se a operação de 2021 for positiva. Sugestão: agrupar pelo ano de entrada ou contar só 2016–2020. Nas minhas quatro estratégias isso não mudou nenhum veredito.
