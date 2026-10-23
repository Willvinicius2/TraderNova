# r9-calendario (rodada 9, lab-v4, BTCUSD)

Conferência de duplicidade: L17 (e r1/r2) testou só a janela de HORAS 21h–23h UTC (r1 em certos dias, r2 com tendência). Dia do mês (L45) e janela de dias da semana (L46) são regras centrais diferentes. L47 difere do L32 (z-score do preço contra a SMA): o gatilho aqui é um choque de retorno de 1–2 h medido em desvios. L48 difere do TV23 (rompimento de ±100): exige divergência de pivôs confirmada (r candles depois, sem repintura).

## L45_turn_of_month — Turn of the month
- Fonte: QuantifiedStrategies (end of month effect in bitcoin), Macro Hive; Ariel (1987)/Lakonishok-Smidt (1988). A fonte não fixa os dias, então a janela foi calibrada.
- Regra: comprado dos últimos `before` dias do mês até o dia `after` do mês seguinte (D1); both = vendido no resto do mês; stop 3/5×ATR14.
- Escolhido: before=5, after=7, k=3, both (borda da grade).
- Dev: 120 trades, +28,7R, PF 1,78, DD 3,6R (1,8%), 5/5 anos. Val: 48, +10,0R, PF 1,98, DD 1,1% (stress +9,4R). Reserva: 91, −9,9R, PF 0,70, DD 6,8%.
- Veredito: **REPROVADA_RESERVA**. DSR 0,0 (escolha entre 144 combinações). O efeito apareceu em 2016–2022 e sumiu em 2023–2026; parece efeito de época, não regra estável.

## L46_weekend_effect — Fim de semana (sexta→segunda)
- Fonte: Caporale & Plastun (CESifo WP 6716 / DIW DP 1694, via Quantpedia): retorno anormal na segunda-feira.
- Regra: posição só nos dias [first..last] da semana (D1, 00:00 UTC); long/short/both; stop k×ATR.
- Escolhido: sexta a terça (first=4, last=8), k=3, só compra.
- Dev: 260 trades, +31,7R, PF 1,80, DD 1,8%, 4/5 anos. Val: 104, −6,0R, PF 0,73 (stress −7,2R).
- Veredito: **REPROVADA_VALIDACAO**. DSR 0,001. Venceu o "só compra", que no desenvolvimento está surfando a alta de 2016–2017 em ~70% dos dias; não se manteve.

## L47_crash_buying — Queda de N desvios em H1
- Fonte: Dubach (crypto mean reversion: compra após queda > 4 desvios em 2 h, vende por tempo após 2 h).
- Regra: z = retorno log de m candles / (desvio dos retornos de 1 h nos `look` candles anteriores × √m); compra z < −N (both: vende z > +N); saída por tempo; stop k×ATR.
- Base: REPROVADA_DESENVOLVIMENTO (melhor: m=2, N=4, look=720, hold=2, long: 176 trades, +11,3R, PF 1,35, só 3/5 anos, vizinhos PF 0,98).
- r1 (filtro de regime: comprar quedas só acima da SMA de N dias, vender picos só abaixo): escolhido m=2, N=5, hold=2, SMA 200 dias, both. Dev: 87 trades, +6,7R, PF 1,42, 4/5 anos, DD 2,0%. Val: 28, +0,6R, PF 1,07 (< 1,15), sem a maior −2,7R, stress −0,8R → **REPROVADA_VALIDACAO**. Sem r2 (validação aberta).
- Interpretação: o repique após crash existe no bruto, mas é pequeno perto do custo de 0,2% ida e volta; não sobrevive fora do desenvolvimento.

## L48_cci_divergence — CCI 20 com divergência
- Fonte: StockSharp 0068 CCI Divergence (CCI 20, divergência com CCI < −100 / > +100, saída no cruzamento do zero, stop 2%); Lambert/Wikipedia/Barchart. Stop trocado por k×ATR14.
- Escolhido: H4, r=2, gap=20, k=3, só compra (D1 tinha PF alto com só 17 trades, abaixo do mínimo).
- Dev: 85 trades, +19,9R, PF 1,85, DD 2,4%, 5/5 anos, DSR 0,40. Val: 51, −2,4R, PF 0,88 (stress −4,2R).
- Veredito: **REPROVADA_VALIDACAO**. Observação: o parâmetro `gap` quase não muda os resultados (os pivôs consecutivos raramente ficam a mais de 20 candles), então a grade efetiva é menor que 162.

Nenhuma CANDIDATA: placebo e teste cruzado não se aplicam.
