# r7-ciclos (rodada 7, protocolo lab-v4, BTCUSD)

Nenhuma das quatro saiu CANDIDATA. Três passaram no desenvolvimento e caíram na validação de 2021–2022; a TV95 não passou nem no desenvolvimento, mesmo depois de 2 refinamentos.

## TV92_sinewave — Ehlers Sinewave (Sine x LeadSine)
- Fonte: listagem EasyLanguage de Ehlers (Cybernetic Analysis, cap. 9) no fórum ProRealCode (prorealcode.com/reply/11887); o script do blackcat no TradingView foi usado como referência. O TradingView não abriu e não achei o Pine nos repositórios.
- Regra: preço (H+L)/2 → Cyber Cycle → fase dominante pela DFT → Sine = sin(fase), LeadSine = sin(fase+45). Compra quando a LeadSine cruza acima da Sine e vende no cruzamento inverso; a posição sai ou inverte no cruzamento oposto. Uso a convenção de Ehlers (a LeadSine sobe primeiro, perto do fundo do ciclo); a fila escreve o inverso. O filtro "ciclo válido" vem do Rocket Science: a fase precisa avançar entre 0,67 e 1,5 × 360/DCPeriod por candle. O original não tem stop, então usei stop de 2–3 ATR.
- Grade: alpha (0,05/0,07/0,1), filtro, k, side, nos tempos H1/H4/D1 (72 combinações).
- Veredito: **REPROVADA_VALIDACAO**. Escolhida H4 com alpha 0,05, sem filtro, k 2, só compra.
  - Desenvolvimento: 278 operações, +53,0R, PF 1,47, DD 12,3R (6,2%), 4 de 5 anos positivos, DSR 0,57.
  - Validação: 119 operações, +1,4R, PF 1,03, e −4,8R no custo stress.
- Interpretação: a vantagem do desenvolvimento era só compra e fraca (DSR 0,57). Em 2021–22 ficou no zero.

## TV93_triple_screen — Elder Triple Screen
- Fonte: regra clássica de Elder (Trading for a Living) e os scripts "Triple Screen" e "Elder's Complete Trading System" do TradingView, que só conheço pelos resumos da busca. Não achei o Pine.
- Regra:
  - Tela 1: inclinação do histograma MACD(12,26,9) no tempo maior, só com o candle maior fechado. Testei que truncar os dados não muda os valores, então não há olhar o futuro.
  - Tela 2: FI2 < 0 no candle anterior (> 0 para vender).
  - Tela 3: a ordem stop na máxima anterior foi aproximada por fechamento acima da máxima anterior, com entrada na abertura seguinte.
  - Stop: menor mínima dos 2 candles, com mínimo de 0,5 ATR.
  - Saída: quando a maré vira contra, ou alvo de 2R/3R.
- Grade: htf (H1→H4/D1, H4→D1/semana, D1→semana/mês), fi, saída, side (72 combinações).
- Veredito: **REPROVADA_VALIDACAO**. Escolhida H4 com tempo maior D1, FI2, saída pela maré, só compra.
  - Desenvolvimento: 200 operações, +236,7R, PF 2,83, DD 14,2R (7,1%), 5 de 5 anos positivos, DSR 0,76.
  - Validação: 80 operações, −7,7R, PF 0,87, DD 17,9R; no custo stress, −14,9R e DD de 11,4%.
- Interpretação: o stop curto gera poucas operações muito grandes. A maior operação sozinha valia cerca de 58R no desenvolvimento, e isso desapareceu em 2021–22.

## TV94_vqi — Volatility Quality [Alpha Extract]
- Fonte: port fiel do Pine em deepentropy/lightweight-charts-indicators (`volatility-quality.ts`), mais a página do VQI no TradingView e o fxcodebase.
- Regra: TR × sinal da vela → EMA(len) → EMA(suav), normalizado para −100..100 em 200 candles.
  - Modo "media": compra quando o VQI sobe e cruza acima da SMA(9) do VQI.
  - Modo "zero": compra quando o VQI cruza 0 (é a troca de cor do original).
  - Venda espelhada; saída no cruzamento oposto; stop de 2–3 ATR (o original não tem stop).
- Grade: 216 combinações.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida D1 com len 9, suav 3, modo zero, k 2, só compra.
  - Desenvolvimento: 70 operações, +73,4R, PF 5,35, DD 4,4R, 4 de 5 anos positivos, DSR 0,93.
  - Validação: 41 operações, −1,3R, PF 0,90 (stress −2,0R).
- Interpretação: o desenvolvimento era excelente até no DSR e mesmo assim falhou fora da amostra. O provável motivo é que isso era seguir a tendência de alta do BTC em D1, e não uma vantagem da regra.

## TV95_profile80 (+ r1, r2) — Market Profile, regra dos 80%
- Fonte:
  - Perfil: port fiel do Pine "Market Profile" de LonesomeTheBlue (deepentropy, `market-profile.ts`), com 20 canais, POC e value area de 70%.
  - Regra de Dalton: MetroTrade e Marketcalls.
- Regra: o dia UTC abre fora da value area do dia anterior já fechado e depois 'conf' candles H1 fecham dentro dela. O alvo é o outro extremo da value area e o stop fica b × ATR além do extremo de reentrada. Uma operação por dia, com saída no fim do dia ou após 24 candles.
- Resultados (todos REPROVADA_DESENVOLVIMENTO):
  - Base (108 combinações): melhor PF 1,02, com +1,0R em 132 operações. Nada de vantagem.
  - r1: filtro de rotação. Só entra se a eficiência de Kaufman de 48h for ≤ er (Dalton descreve a regra para mercado em equilíbrio). Melhor PF 1,16, com +7,1R em 121 operações, só 3 anos positivos e sem robustez.
  - r2: mantém o r1, com stop de 1–2 ATR e alvo no POC ou no outro extremo. Melhor PF 1,17, +7,3R, 3 anos positivos, mediana dos vizinhos 1,02.
- Interpretação: o BTC opera 24h, então a abertura UTC não é a abertura de pregão para a qual a regra foi feita, e no H1 a volta à value area não prevê a travessia dela.

## Motor
Nenhum bug encontrado.
