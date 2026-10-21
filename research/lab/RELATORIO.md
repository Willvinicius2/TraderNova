# Laboratório de estratégias: resultados (rodada 1)

Gerado por `python research/lab/report.py`. Protocolo em `protocol.json`: calibração só no desenvolvimento (BTC 2016–2020), validação 2021–2022 e reserva 2023–out/2026 sem reajuste, custo base 0,10% por lado e stress 0,20%. CANDIDATA passou no histórico, mas ainda precisa de acompanhamento prospectivo, custos reais da conta e risco conjunto. Não é promessa de lucro.

| Estratégia | Família | Veredito | Tempo | Parâmetros | Desenvolvimento | Validação | Reserva | Combinações | DSR |
|---|---|---|---|---|---|---|---|---|---|
| L04_tsmom Momentum de série temporal (TSMOM) | tendencia | **CANDIDATA** | D1 | {"look": 60, "rebal": 1, "k": 2.0, "side": "long"} | 46 op · +594.2R · PF 59.594 · DD 4.85R | 17 op · +5.2R · PF 1.797 · DD 5.71R | 35 op · +41.6R · PF 5.031 · DD 3.62R | 180 | 0.029 |
| L07_stochastic Estocástico de Lane (cruzamento %K/%D nas zonas) | reversao | **CANDIDATA** | D1 | {"n": 9, "zone": 25, "k": 3.0, "side": "long"} | 36 op · +4.9R · PF 1.729 · DD 2.03R | 20 op · +1.9R · PF 1.537 · DD 1.58R | 38 op · +5.2R · PF 1.541 · DD 2.79R | 108 | 0.221 |
| L12_keltner_breakout Rompimento do canal de Keltner | volatilidade | **CANDIDATA** | H4 | {"n": 50, "k": 3.0, "stop_k": 1.5, "side": "both"} | 122 op · +270.1R · PF 4.571 · DD 5.64R | 53 op · +9.3R · PF 1.258 · DD 9.31R | 143 op · +45.4R · PF 1.389 · DD 40.57R | 144 | 0.028 |
| L01_supertrend Supertrend (virada de direção) | tendencia | **REPROVADA_VALIDACAO** | H4 | {"atr_n": 7, "mult": 2.5, "side": "long"} | 133 op · +142.5R · PF 4.143 · DD 4.28R | 62 op · +1.2R · PF 1.047 · DD 5.72R | - | 120 | 0.003 |
| L02_adx_dmi Sistema direcional de Wilder (DI+/DI- com ADX) | tendencia | **REPROVADA_VALIDACAO** | H4 | {"n": 10, "adx_min": 15, "k": 2.0, "side": "long"} | 411 op · +156.1R · PF 2.314 · DD 7.9R | 175 op · -13.6R · PF 0.775 · DD 26.72R | - | 144 | 0.0 |
| L03_ichimoku Ichimoku: cruzamento Tenkan/Kijun com nuvem e Chikou | tendencia | **REPROVADA_VALIDACAO** | H1 | {"s": 3, "exit": "tk", "k": 2.0, "side": "both"} | 209 op · +198.1R · PF 2.324 · DD 13.61R | 92 op · -19.0R · PF 0.749 · DD 22.59R | - | 72 | 0.0 |
| L05_connors_rsi2 RSI(2) de Connors com filtro SMA200 | reversao | **REPROVADA_VALIDACAO** | D1 | {"thr": 15, "k": 2.0, "side": "long"} | 85 op · +6.3R · PF 1.369 · DD 2.26R | 18 op · -0.9R · PF 0.794 · DD 3.11R | - | 54 | 0.2 |
| L06_ibs Internal Bar Strength (IBS) | reversao | **REPROVADA_VALIDACAO** | D1 | {"lo": 0.25, "hi": 0.7, "k": 2.0, "side": "long"} | 190 op · +11.4R · PF 1.369 · DD 4.45R | 115 op · -2.1R · PF 0.894 · DD 3.77R | - | 216 | 0.02 |
| L08_williams_r Williams %R (-90 / -30) | reversao | **REPROVADA_VALIDACAO** | D1 | {"n": 5, "ent": -90, "ext": -30, "k": 2.0, "side": "long"} | 54 op · +5.3R · PF 1.448 · DD 4.51R | 43 op · +1.4R · PF 1.126 · DD 4.62R | - | 288 | 0.075 |
| L09_ttm_squeeze TTM Squeeze (John Carter) | volatilidade | **REPROVADA_VALIDACAO** | H4 | {"kc": 1.5, "min_sq": 1, "exit": "zero", "stop_k": 1.5, "side": "long"} | 140 op · +179.8R · PF 3.513 · DD 6.92R | 45 op · -13.6R · PF 0.574 · DD 22.64R | - | 144 | 0.0 |
| L10_williams_volbreak Volatility breakout de Larry Williams | volatilidade | **REPROVADA_VALIDACAO** | H1 | {"k": 0.7, "sf": 0.5, "hold_days": 2, "side": "long"} | 318 op · +328.0R · PF 2.624 · DD 12.34R | 125 op · -9.1R · PF 0.904 · DD 18.74R | - | 96 | 0.998 |
| L11_nr7 NR7 de Toby Crabel | volatilidade | **REPROVADA_VALIDACAO** | D1 | {"window": 3, "hold": 6, "stop": "atr", "side": "long"} | 111 op · +43.5R · PF 1.744 · DD 8.37R | 34 op · -0.0R · PF 0.999 · DD 9.32R | - | 108 | 0.0 |
| L13_heikin_ashi Tendência Heikin Ashi (velas sem pavio contra) | padroes | **REPROVADA_VALIDACAO** | D1 | {"n": 1, "k": 1.5, "side": "long"} | 136 op · +81.4R · PF 3.342 · DD 4.26R | 55 op · -5.2R · PF 0.745 · DD 9.79R | - | 72 | 0.002 |
| L14_alligator_fractal Alligator + rompimento de fractal (Bill Williams) | padroes | **REPROVADA_VALIDACAO** | H4 | {"align": false, "exit_line": "jaw", "k": 2.0, "side": "long"} | 181 op · +206.7R · PF 3.848 · DD 8.22R | 82 op · -8.6R · PF 0.804 · DD 18.2R | - | 72 | 0.0 |
| L15_floor_pivots_r1 Pivôs diários: rompimento de R1/S1 com filtro de tendência | padroes | **REPROVADA_VALIDACAO** | H4 | {"L": 200, "tgt": "nenhum", "k": 1.5, "hold": 96, "side": "long"} | 211 op · +136.4R · PF 2.656 · DD 6.54R | 76 op · -1.4R · PF 0.959 · DD 9.1R | - | 216 | 0.028 |
| L16_engulfing_trend Engolfo a favor da tendência (SMA longa) | padroes | **REPROVADA_VALIDACAO** | D1 | {"L": 100, "minbody": 0.0, "tr": 3.0, "side": "long"} | 58 op · +47.0R · PF 2.66 · DD 5.26R | 16 op · +1.4R · PF 1.135 · DD 4.85R | - | 72 | 0.257 |
| L18_obv_breakout Rompimento do OBV (Granville) confirmado pelo preço | tempo_volume | **REPROVADA_VALIDACAO** | H4 | {"n": 80, "k": 2.0, "side": "long"} | 65 op · +166.2R · PF 6.219 · DD 3.3R | 35 op · -4.4R · PF 0.824 · DD 12.88R | - | 36 | 0.894 |
| L19_mfi_r1 Money Flow Index com filtro de tendência SMA200 | tempo_volume | **REPROVADA_VALIDACAO** | H1 | {"n": 10, "lo": 10, "exit": "opposite", "k": 2.0, "side": "long"} | 78 op · +25.7R · PF 1.465 · DD 8.68R | 29 op · -19.3R · PF 0.309 · DD 19.33R | - | 144 | 0.0 |
| L15_floor_pivots Pivôs clássicos diários (P, R1, S1): rejeição ou rompimento | padroes | **REPROVADA_DESENVOLVIMENTO** | M15 | (melhor reprovada) | 731 op · +12.3R · PF 1.037 · DD 40.25R | - | - | 144 | - |
| L17_btc_seasonality Sazonalidade intradiária do BTC (21h-23h UTC) | tempo_volume | **REPROVADA_DESENVOLVIMENTO** | H1 | (melhor reprovada) | 1827 op · -206.9R · PF 0.547 · DD 209.49R | - | - | 12 | - |
| L17_btc_seasonality_r1 Sazonalidade intradiária do BTC (21h-23h UTC) só em dias fortes | tempo_volume | **REPROVADA_DESENVOLVIMENTO** | H1 | (melhor reprovada) | 261 op · -7.5R · PF 0.865 · DD 12.75R | - | - | 27 | - |
| L17_btc_seasonality_r2 Sazonalidade intradiária do BTC (21h-23h UTC) em regime de alta | tempo_volume | **REPROVADA_DESENVOLVIMENTO** | H1 | (melhor reprovada) | 1088 op · -61.0R · PF 0.781 · DD 64.18R | - | - | 27 | - |
| L19_mfi Money Flow Index: volta da sobrevenda/sobrecompra | tempo_volume | **REPROVADA_DESENVOLVIMENTO** | H4 | (melhor reprovada) | 8 op · +98.0R · PF 19.813 · DD 4.14R | - | - | 144 | - |
| L20_vwap_reversion Reversão ao VWAP diário/rolante | tempo_volume | **REPROVADA_DESENVOLVIMENTO** | H1 | (melhor reprovada) | 65 op · -22.6R · PF 0.355 · DD 26.11R | - | - | 64 | - |
| L20_vwap_reversion_r1 Reversão ao VWAP com recuperação da banda e tendência | tempo_volume | **REPROVADA_DESENVOLVIMENTO** | H1 | (melhor reprovada) | 45 op · +3.2R · PF 1.306 · DD 2.84R | - | - | 64 | - |
| L20_vwap_reversion_r2 Reversão ao VWAP semanal com recuperação da banda | tempo_volume | **REPROVADA_DESENVOLVIMENTO** | H1 | (melhor reprovada) | 18 op · +4.1R · PF 1.619 · DD 2.74R | - | - | 64 | - |

## Fragilidade das candidatas (`diagnose.py`)

Resultado sem a maior operação e em % do capital com 0,5% de risco por operação, ao lado de comprar e segurar BTC no mesmo período.

| Estratégia | Período | Op. | netR | Sem a maior | Retorno % | DD % | Comprar e segurar % |
|---|---|---|---|---|---|---|---|
| L04_tsmom | development | 46 | +594.2 | +54.8 | +297.1 | 2.42 | +6628.6 |
| L04_tsmom | validation | 17 | +5.2 | -3.6 | +2.6 | 2.86 | -43.0 |
| L04_tsmom | reserve | 35 | +41.6 | +24.9 | +20.8 | 1.81 | +401.8 |
| L07_stochastic | development | 36 | +4.9 | +3.5 | +2.4 | 1.01 | +6628.6 |
| L07_stochastic | validation | 20 | +1.9 | +0.9 | +0.9 | 0.79 | -43.0 |
| L07_stochastic | reserve | 38 | +5.2 | +3.5 | +2.6 | 1.39 | +401.8 |
| L12_keltner_breakout | development | 122 | +270.1 | +222.6 | +135.1 | 2.82 | +6628.6 |
| L12_keltner_breakout | validation | 53 | +9.3 | +1.3 | +4.7 | 4.66 | -43.0 |
| L12_keltner_breakout | reserve | 143 | +45.4 | +2.8 | +22.7 | 20.28 | +401.8 |

Fontes e regras completas em `strategies/` e `results/`. Notas de cada agente em `notes/`.
