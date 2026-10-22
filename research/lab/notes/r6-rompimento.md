# r6-rompimento (rodada 6, bloco 9: rompimento estrutural)

Ativo BTCUSD, protocolo lab-v3. Código Pine lido nas traduções do deepentropy (`/home/user/labdata/pine/deepentropy_lightweight-charts-indicators/src/community/`). Nenhum dos indicadores tem saída ou stop no Pine: usei stop k×ATR14 (e stop móvel k×ATR14 onde indicado). Sinal no fechamento, entrada na abertura seguinte. Teste de truncamento (sinais calculados com dados cortados = sinais com dados completos) feito nas 4 combinações escolhidas: nenhum uso de dado futuro. As 4 abriram a validação e reprovaram, então **nenhum refinamento foi feito** (o protocolo proíbe).

## TV68 Breakout Finder (LonesomeTheBlue)
- Fonte: https://www.tradingview.com/script/EvkXjgyw-Breakout-Finder/ ; Pine em `breakout-finder.ts`.
- Regra: candle de alta fecha acima da máxima de prd candles e de ≥ mintest pivôs de alta dentro de uma faixa de cw% do range de 300 candles (espelho para venda). Stop inicial e móvel k×ATR; sinal oposto inverte.
- Grade: prd 3/5/8, cw 2/3/5, mintest 2/3, k 2/3/4, side long/both; H1, H4 (216 comb.).
- Escolhido H4 prd=3 cw=5 mintest=2 k=3 both. **REPROVADA_VALIDACAO**.
- Dev: 187 trades, +93,6R, PF 2,36, DD 2,2%, 5/5 anos positivos, DSR 0,0. Val: 75 trades, +0,04R, PF 1,00, DD 4,3%; stress −2,9R.
- Interpretação: opera os dois lados e passou em todos os anos do desenvolvimento, mas na validação ficou exatamente no zero; a vantagem não se sustentou.

## TV69 Trendlines with Breaks (LuxAlgo), backpaint=false
- Fonte: https://www.tradingview.com/script/IYL88A1N-Trendlines-with-Breaks-LuxAlgo/ ; Pine em `trendlines-with-breaks.ts`.
- Regra: linha de baixa a partir do pivô de alta (pivothigh(len,len)) caindo ATR(len)/len×mult por candle, projetada até hoje (upper − slope×len, versão sem repintura). Compra quando o fechamento rompe a linha de baixa; venda no rompimento da linha de alta. Sinal oposto inverte/sai. Stop k×ATR.
- Grade: length 7/10/14/20/28, mult 0,5/1/1,5, k 2/3, side long/both; H1, H4, D1 (180 comb.).
- Escolhido H4 length=10 mult=0,5 k=2 long. **REPROVADA_VALIDACAO**.
- Dev: 100 trades, +279,7R, PF 6,83, DD 3,0%, 5/5 anos, DSR 0,995. Val: 60 trades, −13,7R, PF 0,68, DD 13,1%; stress −17,1R.
- Interpretação: só compra; o desenvolvimento espetacular é a alta do BTC de 2016–2020 com stop curto, e a validação (2021–22) virou prejuízo e passou do limite de DD.

## TV70 Darvas Box
- Fontes: script Pine "DARVAS BOX" da comunidade (código reproduzido em https://prorealcode.com/topic/darvas-boxes-de-trading-viex), https://www.investopedia.com/terms/d/darvasboxtheory.asp, livro do Darvas (1960). A tradução `darvas-box.ts` do deepentropy é simplificada (sem confirmação) e não foi usada.
- Regra: topo = máxima nova que não é superada nos boxp−2 candles seguintes (com k3<k2); fundo = mínima de boxp candles nesse momento. Compra no cruzamento do fechamento acima do topo confirmado, sai/vende no cruzamento abaixo do fundo. Stop k×ATR.
- Grade: boxp 4/5/6/8/10/13, k 2/3/4, side long/both; H1, H4, D1 (108 comb.).
- Escolhido H4 boxp=13 k=2 long (ponta da grade). **REPROVADA_VALIDACAO**.
- Dev: 85 trades, +213,0R, PF 5,39, DD 3,3%, 4/5 anos, DSR 0,999. Val: 42 trades, −8,6R, PF 0,72, DD 7,2%; stress −10,9R.
- Interpretação: mesmo padrão do TV69: rompimento só comprado ganha surfando a alta do desenvolvimento e perde em 2021–22.

## TV71 Range Detector (LuxAlgo)
- Fonte: https://www.tradingview.com/script/QOuZIuvH-Range-Detector-LuxAlgo/ ; Pine em `range-detector.ts`.
- Regra: range quando todos os len fechamentos ficam a menos de ATR(500)×mult da SMA(len) (com fusão de ranges que se encostam); compra quando o fechamento sai acima do topo, venda abaixo do fundo. Stop inicial e móvel k×ATR14; sinal oposto inverte.
- Grade: length 10/15/20/30, mult 0,75/1/1,25, k 2/3/4, side long/both; H1, H4, D1 (216 comb.).
- Escolhido H1 length=30 mult=1 k=4 long (ponta da grade). **REPROVADA_VALIDACAO**.
- Dev: 166 trades, +142,2R, PF 3,44, DD 3,1%, 5/5 anos, DSR 0,998. Val: 69 trades, −2,1R, PF 0,93, DD 3,4%; stress −7,0R.
- Interpretação: perda pequena na validação, mas perda; a escolha "só compra" no desenvolvimento de novo não se repetiu.

## Observação sobre o motor
- DSR do TV68 saiu 0,0 com t=3,36: o Sharpe por operação das combinações com poucas operações (só compra, ~70 trades) é maior que o da escolhida (187 trades), e o DSR usa a variância dos Sharpes por operação sem normalizar pelo número de operações. Não é bug de código, mas o DSR por operação penaliza combinações com mais trades.
