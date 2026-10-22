# r5-padroes — Rodada 5, bloco 8 (padrões de barras): TV64–TV67

Ativo BTCUSD, protocolo lab-v3. Código lido nos ports fiéis do Pine em /home/user/labdata/pine/ (DE = deepentropy/lightweight-charts-indicators, commit f8e1b0e; AL = Alorse/pinescript-strategies, commit 8fb3837). Nenhum dos quatro repinta. As quatro passaram no desenvolvimento e reprovaram na validação. Como a validação já tinha sido aberta, o protocolo proíbe refinar, e não houve _r1/_r2.

Nos indicadores da LuxAlgo (TV64, TV65), a confirmação aparece no gráfico um candle depois, porque o Pine testa `close[1]`. Aqui a decisão sai no próprio fechamento que confirma, e a entrada é na abertura seguinte. A informação usada é a mesma, sem olhar o futuro.

## TV64_three_bar — Three Bar Reversal Pattern (LuxAlgo)
- Fontes: https://www.tradingview.com/script/ct5E4FSn-Three-Bar-Reversal-Pattern-LuxAlgo/ ; código DE `three-bar-reversal-pattern.ts`.
- Regra de compra (a venda é o espelho): barra 1 de baixa; barra 2 de baixa, com máxima e mínima abaixo das da barra 1; barra 3 de alta, com máxima acima da máxima da barra 1. A compra sai quando um fechamento passa a máxima da barra 1. O padrão falha se um fechamento cair abaixo da menor mínima das barras 2–3, ou se aparecer o padrão oposto. O indicador não tem saída. Stop na linha de falha (no mínimo 0,25×ATR14), alvo em tr×R. A confirmação oposta fecha a posição (side=long) ou inverte (side=both). Não reproduzi um detalhe: no lado vendido, o Pine cancela a confirmação se surgir um padrão de alta no candle seguinte. Isso exigiria olhar um candle à frente.
- Grade: tipo all/enhanced, filtro none/Supertrend(10,3)/Donchian(13) no modo "Aligned", tr 1/1,5/2/3, lado long/both; H1/H4/D1. Total de 144 combinações.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida: D1, tipo all, sem filtro, tr 3, both.
- Desenvolvimento: 43 trades, +31,9R, PF 2,87, DD 5,1R (2,6%), 4 de 5 anos positivos, PF mediano dos vizinhos 4,70, DSR 0,15.
- Validação: 20 trades, +1,6R, PF 1,14 (o mínimo exigido é 1,15), −1,4R sem a maior operação, stress +1,2R.
- Leitura: são poucas operações em D1 e o DSR é baixo. Na validação, o resultado ficou perto de zero e dependeu de uma única operação.

## TV65_nbar_reversal — N Bar Reversal Detector (LuxAlgo)
- Fontes: https://www.tradingview.com/script/efR5fu0R-N-Bar-Reversal-Detector-LuxAlgo/ , https://www.luxalgo.com/library/indicator/n-bar-reversal-detector/ ; código DE `n-bar-reversal-detector.ts`.
- Regra: generaliza o TV64 para N barras. A referência é a barra i−N. O script percorre as barras seguintes enquanto nenhuma tiver máxima acima da máxima de i−N. O padrão exige que ≥50% das N−1 barras sejam de baixa e que a máxima de i passe a máxima de i−N. A confirmação vem com um fechamento acima da máxima de i−N. Linha de falha, stop, alvo e filtros são os mesmos do TV64. O helper vem do arquivo TV64.
- Grade: N 4/7/10, filtro none/st/dc, tr 1/1,5/2/3, lado; H1/H4/D1. Total de 216 combinações.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida: H1, N 10, Supertrend, tr 3, só compra.
- Desenvolvimento: 112 trades, +51,8R, PF 1,75, DD 7,7R (3,8%), 5 de 5 anos positivos, DSR 0,45.
- Validação: 43 trades, +2,5R, PF 1,09, DD 9,0R, −0,5R sem a maior operação, stress −2,0R.
- Leitura: foi a única das quatro com os 5 anos de desenvolvimento positivos. Na validação, porém, o ganho sumiu e virou perda no custo stress.

## TV66_pinbar_magic — Pin Bar Magic v1 (ZenAndTheArtOfTrading)
- Fontes: AL `strategies/other/Pin Bar Magic v1.pine` (https://github.com/Alorse/pinescript-strategies), https://doc.stocksharp.com/de/api-examples/0439_Pin_Bar_Magic , https://www.tradingview.com/scripts/pinbar/ .
- Regra: leque de médias alinhado (EMA rápida > EMA média > SMA 50) e pin bar, isto é, sombra maior que 66% do range. A pin bar precisa furar uma das 3 médias, com abertura e fechamento do lado certo. O Pine coloca uma ordem stop na máxima do candle anterior à pin bar (high[1]), cancelada depois de 3 candles. Aqui ela foi aproximada assim: um fechamento acima desse nível, da pin bar até 3 candles depois, gera entrada na abertura seguinte. Stop em low[1] − m×ATR14. Saída quando a EMA rápida cruza a média. O trailing do Pine (1 ponto / 1 ponto) é quase nulo; troquei por um trailing de tk×ATR14. Omiti o fechamento de sexta às 16h, que é coisa de forex.
- Grade: médias 6/18/50 (Pine) e 10/20/50 (descrição da fila), m 0,5/1, tk 1/2/3/5, lado; H1/H4/D1. Total de 96 combinações.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida: H4, médias 10/20/50, m 0,5, tk 5, só compra.
- Desenvolvimento: 63 trades, +86,0R, PF 3,18, DD 8,8R (4,4%), 4 de 5 anos positivos, vizinhos 2,80, DSR 0,98.
- Validação: 22 trades, +2,5R, PF 1,17 (passaria no PF), mas −6,3R sem a maior operação, stress +0,85R.
- Leitura: o resultado depende de poucas operações longas a favor da tendência. Sem a maior operação, a validação fica negativa.

## TV67_rbd — Rally Base Drop Signals (LuxAlgo)
- Fontes: https://www.tradingview.com/scripts/rallybasedrop/ ; código DE `rally-base-drop-signals.ts`.
- Regra: Rally = 2 velas verdes seguidas, Drop = 2 vermelhas seguidas, Base = qualquer outro caso. O script guarda as 3 últimas fases distintas. Drop-Base-Rally compra e Rally-Base-Drop vende. Com cont=True, também conta RBR para compra e DBD para venda. O indicador não tem stop: usei k×ATR14, alvo tr×R (0 = sem alvo) e o sinal oposto fecha ou inverte.
- Grade: cont F/T, k 1/1,5/2/3, tr 0/1,5/2/3, lado; H1/H4/D1. Total de 192 combinações.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida: D1, só DBR/RBD, k 1, sem alvo, só compra.
- Desenvolvimento: 143 trades, +140,6R, PF 3,67, DD 7,0R (3,5%), 4 de 5 anos positivos, vizinhos 2,85, DSR 0,98.
- Validação: 63 trades, −8,9R, PF 0,77, DD 15,8R (7,9%), stress −11,3R.
- Leitura: é a mesma história das rodadas anteriores. Ficar comprado com stop curto ganhou no bull de 2016–2020 e perdeu em 2021–22. Mesmo com o filtro de 4 de 5 anos, a escolha ficou só compra.

## Motor
Não encontrei bug no motor. Uma observação: o motor ignora a direção do sinal de entrada quando já existe posição no mesmo lado. Por isso, uma confirmação nova no mesmo sentido não renova o stop. O comportamento é coerente com pyramiding=0 no Pine.
