# r7-diversos (rodada 7, bloco 17: TV100–TV103), BTCUSD, lab-v4

Nenhuma das quatro passou. Todas foram reprovadas na validação (2021–2022), então nenhuma pode ser refinada.

## TV100_better_volume: Better Volume (LazyBear)
- **Fonte:** o código veio do port fiel do Pine (DE `better-volume.ts`). A leitura das barras de clímax é a da LuxAlgo ("better-volume-classifications") e a do eSignal. O indicador não traz regra de operação, então a regra foi montada.
- **Regra:**
  - As barras são classificadas como no original, com as 20 medidas e a precedência estranha de v1 preservada.
  - Um "climax up" acima da EMA(trend) dispara venda; um "climax down" abaixo da EMA dispara compra.
  - Com confirm=1, a entrada só acontece se em até `length` candles o fechamento romper o extremo oposto da barra de clímax.
  - Stop de k×ATR14, alvo em R e saída por tempo.
- **Calibrado:** length, trend, confirm, k, target_r e side, em H1, H4 e D1 (288 combinações).
- **Escolhida:** H4, length 8, EMA100, confirm=1, k 3, alvo 2,5R, só compra.
- **Veredito: REPROVADA_VALIDACAO**

| Fase | Trades | netR | PF | DD | Outros |
|---|---|---|---|---|---|
| Desenvolvimento | 169 | +27,8 | 1,50 | 4,7% | 4 de 5 anos positivos, DSR 0,07 |
| Validação (base) | 85 | +3,2 | 1,11 | 5,6% | |
| Validação (stress) | | +0,3 | | | sem a maior operação: −2,1 |

- **Interpretação:** comprar depois do clímax de venda confirmado funcionou no desenvolvimento, mas o DSR baixo indica sorte na seleção. Na validação a vantagem quase sumiu: o PF ficou abaixo de 1,15.

## TV101_rex: Rex Oscillator
- **Fonte:**
  - TradingView "REX Oscillator" (AUi1mgFZ), que não abriu.
  - ProRealCode (tópico rex-indicator, com o código MQL).
  - mql5 código 21247.
- **Regra:**
  - TVB = 3·fech − (mín + abert + máx).
  - Rex = média do TVB em `smooth` candles; Sinal = média do Rex em `signal` candles (SMA ou EMA).
  - Rex cruzando acima do sinal é compra; cruzando abaixo é venda (com side=both) ou saída.
  - Filtro opcional: EMA200. Stop de 2–3×ATR14, já que o original não tem stop.
- **Calibrado:** smooth, signal, ma, trend, k e side, em H1, H4 e D1 (288 combinações).
- **Escolhida:** H4, SMA 14/14, EMA200, k 2, só compra.
- **Veredito: REPROVADA_VALIDACAO**

| Fase | Trades | netR | PF | DD | Outros |
|---|---|---|---|---|---|
| Desenvolvimento | 472 | +100,1 | 1,83 | 3,7% | 4 de 5 anos positivos, DSR 0,85 |
| Validação (base) | 137 | +6,6 | 1,20 | 3,3% | passou no custo base |
| Validação (stress) | | −0,13 | | | reprovou por pouco |

- **Interpretação:** a melhor do bloco, com o desenvolvimento forte e DSR alto. Mesmo assim, na validação a borda fica do tamanho do custo: o netR médio por operação é de +0,05R e zera com custo dobrado. Também é "só compra" acima da EMA200.

## TV102_damiani: Damiani Volatmeter (filtro)
- **Fonte:**
  - Página do loxx no TradingView (z95IdM4a).
  - Fórmula do fxcodebase: Line1 = ATRvis/ATRsed + (Line1[1] − Line1[3])/2; Line2 = limiar − DPvis/DPsed.
  - Padrões clássicos 13/40/20/100 e limiar 1,4. A FILA cita 7/50, que também foi testado.
- **Gatilho filtrado:** cruzamento Fisher/Trigger em extremo (a lógica do TV19), porque a página do loxx diz que o Volatmeter não tem direção e cita o Fisher Transform como indicador direcional para combinar. O filtro só deixa entrar quando Line1 > Line2. A saída é o cruzamento oposto do Fisher, sem filtro. Stop de k×ATR14.
- **Original:** 288 combinações. **REPROVADA_DESENVOLVIMENTO.**
  - No H1 e no H4 perde em todos os anos.
  - O melhor D1 tem 48 trades, PF 1,74, mas só 3 de 5 anos positivos.
- **r1 (refinamento 1):** filtro de tendência EMA(100/200) a favor do sinal, com nível fixo em 0,5. Escolhida: H4, 7/50, limiar 1,2, n 13, EMA100, k 2, both.
- **Veredito final: REPROVADA_VALIDACAO**

| Fase | Trades | netR | PF | DD | Outros |
|---|---|---|---|---|---|
| Desenvolvimento | 167 | +9,0 | 1,21 | 3,5% | 4 de 5 anos positivos, DSR 0,01 |
| Validação (base) | 87 | −0,9 | 0,97 | 3,7% | |
| Validação (stress) | | −5,0 | | | |

- **Interpretação:** o filtro de volatilidade não salvou um gatilho de reversão fraco. A versão escolhida passou raspando no desenvolvimento (DSR ~0) e perdeu na validação.

## TV103_swing_seq: Swing Breakout Sequence (LuxAlgo)
- **Fonte:**
  - TradingView LZIqzxDq.
  - Página da LuxAlgo library.
  - Código do port DE `swing-breakout-sequence.ts`, portado fielmente: pernas, swings e pontos internos, sequência A/B/1–4 e ponto 5 a até thr×ATR200 do ponto 4.
  - Os swings são confirmados com atraso, na mudança de perna, e não repintam.
- **Regra:**
  - A sequência de alta tem os pontos 1 e 3 acima de A (tentativas falhas de rompimento), os pontos 2 e 4 dentro de A–B e o ponto 5 formando fundo duplo perto do 4.
  - Compra quando o fechamento passa acima de A em até `window` candles. Cancela se fechar abaixo de B.
  - Venda espelhada.
  - Stop: k×ATR, ou o ponto 5 menos 0,25×ATR.
  - Alvo de 2–3R e saída por tempo.
- **Calibrado:** em M15, H1 e H4 (288 combinações). O padrão é raro: no D1 houve só 0–1 sinal em 2016–2020, por isso o D1 foi trocado pelo M15.
- **Escolhida:** H1, length 3, thr 1,0, window 30, stop ATR, alvo 3R, both.
- **Veredito: REPROVADA_VALIDACAO**

| Fase | Trades | netR | PF | DD | Outros |
|---|---|---|---|---|---|
| Desenvolvimento | 194 | +42,7 | 1,35 | 5,8% | 5 de 5 anos positivos, **DSR 0,00** |
| Validação (base) | 90 | −38,3 | 0,52 | 20,1% | |
| Validação (stress) | | −47,8 | | | |

- **Interpretação:** o resultado do desenvolvimento foi sorte de seleção, como o DSR 0 indica, e desabou fora da amostra.

## Motor
Não achei bug no motor. Observação: o calibrate.py só grava os 5 melhores do desenvolvimento em topDevelopment, então o diagnóstico por tempo gráfico precisa ser refeito à parte. Fiz isso só no período de desenvolvimento.
