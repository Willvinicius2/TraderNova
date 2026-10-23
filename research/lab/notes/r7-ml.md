# r7-ml — Rodada 7, bloco 13 (aprendizado de máquina), BTCUSD, protocolo lab-v4

Código Pine lido no porte linha a linha de github.com/deepentropy/lightweight-charts-indicators (commit f8e1b0e), exceto TV86 (código v.3 colado no fórum ProRealCode). Nenhum dos quatro tem stop no original: stop de proteção k_atr × ATR14. Todo "treino" usa só candles até o atual.

## TV84_knn — Machine Learning: kNN-based Strategy (capissimo)
- Fonte: usethinkscript.com/threads/machine-learning-knn-based-indicator-for-thinkorswim.16778 + porte DE `ml-knn-strategy.ts`.
- Regra: 2 variáveis (RSI/CCI/ROC 28 e 14, ou "All"), rótulo sign(fech[1]-fech) do próprio candle; lógica literal do original (empurra o rótulo quando o ponto está MAIS LONGE que todos os anteriores, fila dos últimos floor(√K) rótulos); soma > 0 compra, < 0 vende; filtro opcional ATR10>ATR40. Diferença: treino em janela deslizante dos últimos 1000 candles (o Pine guarda tudo desde 2000).
- Calibrado: indicador, K, filtro, lado; H1/H4/D1 (144 combinações).
- Veredito: **REPROVADA_VALIDACAO**. Escolhido H4 ROC K=400 both. Dev 606 trades, +123,4R, PF 1,89, DD 3,0%, 5/5 anos, DSR 0,68. Validação 273 trades, −18,6R, PF 0,76 (stress −28R, DD 14%).
- Interpretação: a "vizinhança" do original é na prática um ruído sobre os últimos rótulos; o bom desenvolvimento não se repetiu em 2021–22. Sem refinamento (validação já aberta).

## TV85_ai_trend_nav — AI Trend Navigator [K-Neighbor] (Zeiierman)
- Fonte: tradingview.com/script/30aLnPNh + porte DE `ai-trend-navigator.ts`.
- Regra: kNN_MA = média dos k valores de SMA(hl2,maLen) dos 30 candles anteriores mais próximos de RMA(fech,maLen); linha = WMA5(kNN_MA) cruza a RMA(kNN_MA, suavização): compra acima, venda abaixo, sai no cruzamento oposto.
- Calibrado: k, suavização, maLen, lado (108 combinações).
- Veredito: **CANDIDATA** (não é estratégia aprovada). H4, k=10, suavização 100, maLen 10, both, DSR 0,985.
  - Dev 68 trades, +194,4R, PF 5,91, DD 3,3%, sem maior +144R, 5/5 anos.
  - Validação 29 trades, +9,7R, PF 1,54, DD 4,4%, sem a maior só +0,12R (no limite); stress +8,7R.
  - Reserva 70 trades, +39,4R, PF 1,89, DD 4,5%, sem maior +18,7R; stress +35,1R.
  - Placebo (entradas embaralhadas, 20 sorteios), mediana: dev +45,8R PF 2,30; val −2,5R PF 0,82; reserva +11,5R PF 1,30. Real ≥ placebo em 20/20, 19/20 e 18/20. O placebo de dev já ganha muito (as saídas por cruzamento surfam tendência), mas a regra fica bem acima dele.
  - Teste cruzado (mesmos parâmetros, H4): EURUSD reprova (dev +3,9R PF 1,08; val −2,0R; reserva −19,7R, DD 16%). USDJPY reprova (dev +29,4R PF 1,50 mas sem a maior < 0 e DD 11%; val +10,5R PF 1,38 sem maior < 0; reserva −1,8R).
- Interpretação: é um seguidor de tendência lento (média ~140 candles H4 por operação, 26–31% de acerto) que vive de poucas tendências grandes do BTC; na validação depende quase de uma operação e não se transfere para câmbio. Tratar como hipótese, não como vantagem confirmada.

## TV86_logreg — Machine Learning: Logistic Regression (capissimo)
- Fonte: prorealcode.com/topic/machine-learning-logistic-regression (Pine v.3) + usethinkscript (tópico 17134).
- Regra (padrões do Pine): a hipótese do original é sigmoid(dot(X,0,p)) = 0,5 fixa, então a "loss" vira uma soma dupla de fech² nos últimos p candles; minimax(loss, nlbk) reescalado ao mínimo/máximo do fechamento; fech > scaled_loss compra, < vende; sai após hold candles sem mudança ou inverte. Filtro opcional ATR1>ATR10.
- Calibrado: lookback, nlbk, hold, filtro, lado (324 combinações).
- Veredito: **REPROVADA_VALIDACAO**. H4, p=5, nlbk=10, hold 20, filtro vol, long. Dev 256 trades, +75,1R, PF 2,05, DD 2,3%, 5/5 anos, DSR 0,92. Validação 113 trades, −9,8R, PF 0,78 (stress −13,8R).
- Interpretação: não há regressão logística de fato (o peso não entra no treino); é um filtro de momento de curto prazo e só compra, que não sobreviveu a 2021–22.

## TV87_knn_trend — Machine Learning: kNN Trend Predictor (tkarolak), look-ahead off
- Fonte: tradingview.com/script/lhpm23En + LuxAlgo library + porte DE `machine-learning-knn-trend-predictor.ts`.
- Regra: no Pine a distância nova entra no anel antes de calcular o mínimo, então o "vizinho" é sempre o fechamento e a curva é a SMA(N) do fechamento (reproduzido fielmente; K sem efeito). Direção +1 quando curva < fech[1]; compra/venda na virada; inverte na oposta.
- Calibrado: N, k_atr, lado (48 combinações).
- Veredito: **REPROVADA_VALIDACAO**. D1, N=100, k_atr 2, both, DSR 0,99. Dev 68 trades, +110,9R, PF 8,41, DD 1,5%. Validação 23 trades, +2,6R, PF 1,30 mas sem a maior operação −3,0R (reprova).
- Interpretação: é fech[1] contra SMA(100) diária; o desenvolvimento 2016–20 é dominado pelas grandes tendências do BTC e em 2021–22 o resultado dependeu de uma operação.
