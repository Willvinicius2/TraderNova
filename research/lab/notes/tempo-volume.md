# Notas: agente tempo-volume (família tempo_volume)

Ativo: BTCUSD (Bitstamp, 1 min reamostrado). Custo base 0,10% por lado, stress 0,20%.
**Volume:** o volume é só do Bitstamp, uma corretora entre muitas. OBV, MFI e VWAP aqui medem o fluxo de uma
corretora, não do mercado inteiro de BTC. Isso vale para L18, L19 e L20.

## L17_btc_seasonality: sazonalidade intradiária do BTC
- Fonte: Quantpedia, "Are There Seasonal Intraday or Overnight Anomalies in Bitcoin?" (compra 21:00 UTC, vende 23:00 UTC; atualização cita sexta > quinta > sáb/dom como dias mais fortes).
- Regra: comprado só na janela da fonte, saída por tempo; stop de proteção 2*ATR14 (a fonte não tem). Calibrado só a janela (hora 19-22, duração 1-3 h), H1.
- Veredito: **REPROVADA_DESENVOLVIMENTO** (original e os 2 refinamentos).
  - Original (12 comb.): melhor 21h/3h: 1827 trades, netR -161, PF 0,65. Sem custo seria +88R (PF 1,27).
  - r1, só dias fortes da fonte (27 comb.): melhor sexta 22h/3h: 261 trades, netR -7,5, PF 0,87.
  - r2, só em regime de alta (preço > SMA de N dias) (27 comb.): melhor 1088 trades, netR -61, PF 0,78.
- Interpretação: o efeito de horário existe no bruto do período 2016-2020 (cerca de +0,10% por janela), mas é menor que o custo de 0,20% ida e volta. Num spot com 0,10% por lado ele não se paga. A fonte também é posterior e em parte se sobrepõe ao nosso desenvolvimento.

## L18_obv_breakout: rompimento do OBV (Granville)
- Fontes: StockCharts ChartSchool (OBV), IncredibleCharts, MetaTrader 4 help. Definição clássica de Granville (1963): o rompimento do OBV antecede o do preço.
- Regra: compra quando o OBV fecha acima da máxima dos N candles anteriores e o preço está acima da EMA(N); venda no espelho; sai quando o OBV cruza de volta sua SMA(N); stop k*ATR14. Grade N {20,40,80}, k {2,3}, lado {long, both}, H1/H4/D1 (36 comb.).
- Veredito: **REPROVADA_VALIDACAO**.
  - Escolhido H4, N=80, k=2, só compra. Dev: 65 trades, netR +166, PF 6,22, DD 3,3R, PF mediano dos vizinhos 3,94, DSR 0,89.
  - Validação 2021-2022: 35 trades, netR -4,4, PF 0,82, DD 12,9R (stress -6,4R). A reserva não foi aberta.
- Interpretação: o desenvolvimento muito bom vem quase todo de comprar a forte alta do BTC de 2016-2020 com uma saída que segue a tendência. Em 2021-2022, com topo duplo e baixa, o sinal não se manteve. Pelo protocolo, não há reajuste.

## L19_mfi: Money Flow Index (Quong & Soudack)
- Fontes: StockCharts ChartSchool (MFI), cTrader help. Níveis 20/80 e extremos 10/90 da fonte.
- Regra: compra quando o MFI(n) volta a cruzar para cima do nível lo; venda quando volta a cruzar para baixo de 100-lo; saída em 50 ou no nível oposto; stop k*ATR14. Grade n {10,14,20}, lo {10,20}, saída {mid, opposite}, k {2,3}, lado, H1/H4/D1 (144 comb.).
- Original: **REPROVADA_DESENVOLVIMENTO**. Nenhuma combinação com trades suficientes passou na robustez. A melhor elegível por trades foi H1 n20/lo10: 70 trades, PF 1,79, mas isolada. Os vizinhos e o H1 em geral perdiam.
- r1 (só compra acima da SMA200 e só vende abaixo, porque o MFI fica preso no extremo em tendência forte, como avisa a StockCharts): **REPROVADA_VALIDACAO**.
  - Escolhido H1, n=10, lo=10, saída no nível oposto, k=2, só compra. Dev: 78 trades, netR +25,7, PF 1,47, DD 8,7R, vizinhos 1,22, DSR 0,00 (aviso de provável sorte).
  - Validação: 29 trades, netR -19,3, PF 0,31 (stress -22,7R).
- Interpretação: a vantagem no desenvolvimento era fraca e o DSR já indicava sorte de seleção. Não houve vantagem fora da amostra.

## L20_vwap_reversion: reversão ao VWAP
- Fontes: scripts TradingView "VWAP Intraday/Weekly/Monthly" e "Institutional VWAP Bands [JOAT]", LuxAlgo VWAP strategy. São convenções de praticantes, sem backtest publicado.
- Original (VWAP do dia UTC ou rolante de 24h; entra com fechamento além de VWAP ± d*ATR; alvo no VWAP; M15/H1; 64 comb.): **REPROVADA_DESENVOLVIMENTO**. Todas as combinações perderam, até sem custo (ex.: H1 rolante d=2, both: PF bruto 0,77).
- r1 (entrada só quando o preço fecha de volta para dentro da banda, a regra de recuperação do JOAT, e só a favor da EMA200): **REPROVADA_DESENVOLVIMENTO**. Melhor: H1 dia d=2,5, 45 trades, netR +3,2, PF 1,31, abaixo do mínimo de 60 trades. O resto ficou perto de zero.
- r2 (âncora semanal ou rolante de 7 dias, H1/H4, porque o alvo diário é pequeno perto do custo): **REPROVADA_DESENVOLVIMENTO**. Melhor: 18 trades, PF 1,62, poucos demais.
- Interpretação: no BTC intradiário, preço esticado longe do VWAP tende a continuar, não a voltar. A reversão simples perde até no bruto. As versões filtradas mal empatam e geram poucas operações.

## Observações sobre o motor e os dados
- Em estratégias reprovadas, `topDevelopment` ordena por netR/max(DD,5). Por isso o "melhor" impresso pode ser uma combinação com poucos trades e PF enorme (ex.: L19 H4 com 8 trades e PF 19,8), que nunca foi elegível. Não é bug, mas engana na leitura.
- O último candle do cache (2026-10-21 02:00 H1) é parcial (volume ~3,6). Não afeta o desenvolvimento.
