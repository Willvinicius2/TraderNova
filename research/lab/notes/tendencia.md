# Agente tendencia — notas (BTCUSD, protocolo lab-v1)

Custos: base 0,10%/lado, stress 0,20%/lado. Números em R (risco do stop inicial). Nenhum refinamento feito: as três reprovadas caíram na VALIDAÇÃO, e o protocolo proíbe reajuste depois disso.

## L01_supertrend — Supertrend (Seban)
- Fonte: help.ctrader.com (Supertrend), LuxAlgo/TradingView script r6dAP7yi.
- Regra: linha (máx+mín)/2 ± mult*ATR(n) com bandas finais; entra na virada de direção, sai na virada oposta; stop inicial na própria linha (mín. 0,5 ATR).
- Calibrado: atr_n {7,10,14,20} x mult {2..4} x side x H1/H4/D1 = 120.
- Escolhido: H4, n=7, mult=2,5, só compra. **REPROVADA_VALIDACAO**.
- Dev: 133 trades, +142,5R, PF 4,14, DD 4,3R. Val: 62 trades, +1,2R, PF 1,05 (stress −0,9R). Reserva não aberta.
- Leitura: o lucro do desenvolvimento era a alta de 2016-2020; em 2021-2022 o sinal ficou no zero a zero, sem vantagem depois dos custos.

## L02_adx_dmi — Sistema direcional de Wilder
- Fonte: barchart.com (ADX/DMI), metatrader5.com (ADMI), Wilder (1978).
- Regra: DI+ cruza acima de DI− com ADX ≥ limiar → compra (venda espelhada se side=both); sai no cruzamento oposto; stop k*ATR(14).
- Calibrado: n {10,14,20} x ADX {15,20,25,30} x k {2,3} x side x 3 TFs = 144.
- Escolhido: H4, n=10, ADX≥15, k=2, só compra. **REPROVADA_VALIDACAO**.
- Dev: 411 trades, +156,1R, PF 2,31, DD 7,9R. Val: 175 trades, −13,6R, PF 0,78, DD 26,7R (stress −22,7R).
- Leitura: desempenho forte no desenvolvimento não sobreviveu fora da amostra; DSR ≈ 0 já indicava sorte de seleção.

## L03_ichimoku — Ichimoku Kinko Hyo
- Fonte: Wikipedia (Ichimoku Kinkō Hyō), LuxAlgo (Ichimoku signals).
- Regra: Tenkan cruza Kijun, fechamento do mesmo lado da nuvem (nuvem deslocada 26*s, sem olhar o futuro), Chikou confirmando (fechamento vs 26*s atrás). Saída por cruzamento TK oposto ou por fechar do lado errado da Kijun; stop k*ATR(14).
- Calibrado: escala s {1,2,3} (9/26/52 vezes s) x saída {tk,kijun} x k {2,3} x side x 3 TFs = 72.
- Escolhido: H1, s=3, saída tk, k=2, compra e venda. **REPROVADA_VALIDACAO**.
- Dev: 209 trades, +198,1R, PF 2,32, DD 13,6R. Val: 92 trades, −19,0R, PF 0,75, DD 22,6R (stress −30,2R).
- Leitura: mesmo padrão: ganho concentrado no ciclo de alta do desenvolvimento, perda clara em 2021-2022.

## L04_tsmom — Momentum de série temporal (Moskowitz, Ooi & Pedersen 2012)
- Fonte: SSRN 2089463 (JFE 104, 2012), PDF em fairmodel.econ.yale.edu, Quantpedia.
- Regra: a cada `rebal` dias, sinal do retorno dos últimos `look` dias (positivo = comprado; negativo = vendido ou fora). Sem volatility scaling (o R já normaliza pelo stop). Stop de proteção k*ATR(14 dias).
- Calibrado: look {30,60,90,180,365} x rebal {1,7,30} x k {2,4} x side x 3 TFs = 180.
- Escolhido: D1, look=60, rebal=1 (diário), k=2, só compra. **CANDIDATA**.
- Dev: 46 trades, +594,2R, PF 59,6, DD 4,9R. Val: 17 trades, +5,2R, PF 1,80, DD 5,7R (stress +4,8R). Reserva: 35 trades, +41,6R, PF 5,03, DD 3,6R (stress +40,4R).
- Atenção (honestidade): os números em R são inflados por poucas operações longas com stop fixo pequeno frente a altas enormes. No dev, uma única operação (out/2016–jan/2018) vale +539R; sem ela sobram +54,8R. Na validação, sem a maior operação (+8,7R) o resultado fica −3,6R. Na reserva, sem a maior (+16,7R) ainda sobram +25,0R. DSR = 0,03 (provável sorte na seleção). É essencialmente "ficar comprado no BTC quando o retorno de 60 dias é positivo": passou em histórico, mas com amostra pequena, dependência de caudas e de um único ativo em alta secular. Precisa de acompanhamento prospectivo e de métrica em % do capital (não só R) antes de qualquer uso.
