# Agente reversao: notas (BTCUSD, protocolo lab-v1)

Todas as quatro estratégias passaram no desenvolvimento e, portanto, tiveram a validação aberta. Por isso nenhuma foi refinada: o protocolo não permite reajustar depois de ver a validação ou a reserva. Em todas a combinação escolhida foi D1, só compra, com stop de proteção em ATR. O Deflated Sharpe ficou abaixo de 0,5 em todas, o que gera um aviso de possível sorte na seleção.

## L05_connors_rsi2: RSI(2) de Connors com SMA200
- Fontes: luxalgo.com/library/concept/rsi-2, backtrex.com (connors-rsi-2-sp-500) e o livro de Connors & Alvarez (2008).
- Regra: compra quando o fechamento está acima da SMA200 e o RSI(2) fica abaixo do limiar. Sai quando o fechamento passa da SMA5 ou cai abaixo da SMA200. A venda é o espelho. A fonte não usa stop; aqui há stop de k*ATR14 porque o motor exige um.
- Calibrado: limiar {5, 10, 15}, k {2, 3, 4}, lado e tempo gráfico {H1, H4, D1}, num total de 54 combinações.
- Escolhida: D1, limiar 15, k=2, só compra. DSR 0,20.
- Desenvolvimento: 85 trades, +6,3R, PF 1,37, DD 2,3R.
- Validação: 18 trades, -0,93R, PF 0,79 (stress -1,21R). **REPROVADA_VALIDACAO.**
- Interpretação: a vantagem no desenvolvimento foi pequena, cerca de 1,3R por ano, e não se repetiu em 2021-2022.

## L06_ibs: Internal Bar Strength
- Fontes: quantifiedstrategies.substack.com (the-internal-bar-strength-ibs-indicator) e doc.stocksharp.com (IBS mean reversion).
- Regra: compra quando o IBS fica abaixo do limiar baixo (a fonte usa 0,2). Sai quando o IBS passa do limiar alto (a fonte usa 0,8). A venda é o espelho. Stop de k*ATR14.
- Calibrado: limiar baixo {0,1; 0,15; 0,2; 0,25}, limiar alto {0,7; 0,8; 0,9}, k {2, 3, 4}, lado e tempo gráfico, num total de 216 combinações.
- Escolhida: D1, limiar baixo 0,25, limiar alto 0,7, k=2, só compra. DSR 0,02.
- Desenvolvimento: 190 trades, +11,4R, PF 1,37, DD 4,5R.
- Validação: 115 trades, -2,15R, PF 0,89 (stress -4,35R). **REPROVADA_VALIDACAO.**
- Interpretação: o DSR de 0,02 já indicava que a escolha era sorte de seleção. O efeito IBS das ações não se mostrou estável no BTC.

## L07_stochastic: estocástico lento de Lane
- Fontes: help.trendspider.com (lanes-stochastic-oscillator), barchart.com (stochastic_fast) e babypips.com (Stochastics).
- Regra: usa o %K lento (média de 3) e o %D (média de 3 do %K). Compra quando o %K cruza acima do %D com o %D abaixo da zona. Sai quando o %K passa de 100 menos a zona. A venda é o espelho. Stop de k*ATR14.
- Calibrado: n {9, 14, 21}, zona {15, 20, 25}, k {2, 3}, lado e tempo gráfico, num total de 108 combinações.
- Escolhida: D1, n=9, zona 25, k=3, só compra. DSR 0,22. Mediana do PF dos vizinhos 1,29.
- Desenvolvimento: 36 trades, +4,9R, PF 1,73, DD 2,0R.
- Validação: 20 trades, +1,85R, PF 1,54 (stress +1,62R).
- Reserva: 38 trades, +5,17R, PF 1,54 (stress +4,39R), DD 2,8R.
- Veredito: **CANDIDATA.**
- Interpretação: passou nas três fases com PF estável, perto de 1,5. Mesmo assim, são poucas operações (cerca de 7 por ano), o ganho absoluto é pequeno (cerca de 1R por ano) e o DSR baixo pede cautela. É candidata a acompanhamento prospectivo, não uma estratégia aprovada.

## L08_williams_r: Williams %R (-90/-30)
- Fontes: quantifiedstrategies.substack.com (williams-r-trading-strategy-williams-203) e incrediblecharts.com (williams_percent_r).
- Regra: compra quando o %R(n) fica abaixo do limiar de entrada (a fonte usa -90). Sai quando o fechamento passa da máxima anterior ou o %R passa do limiar de saída (a fonte usa -30). A venda é o espelho. Stop de k*ATR14.
- Calibrado: n {2, 3, 5, 10}, entrada {-95, -90}, saída {-40, -30, -20}, k {2, 3}, lado e tempo gráfico, num total de 288 combinações.
- Escolhida: D1, n=5, entrada -90, saída -30 (exatamente os valores da fonte), k=2, só compra. DSR 0,075.
- Desenvolvimento: 54 trades, +5,3R, PF 1,45, DD 4,5R.
- Validação: 43 trades, +1,43R, PF 1,13 (stress +0,64R).
- Veredito: **REPROVADA_VALIDACAO**, porque o PF ficou abaixo de 1,15.
- Interpretação: a validação ficou positiva, mas fraca e abaixo do critério. A regra perdeu força fora da amostra.
