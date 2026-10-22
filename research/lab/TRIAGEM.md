# Triagem em massa dos scripts do TradingView

1707 indicadores da biblioteca deepentropy (ports em TypeScript de scripts do TradingView), em BTCUSD H4 e D1, com os parâmetros padrão do autor. Nada foi calibrado: compra e venda sempre, stop de 2×ATR14, saída e inversão no sinal oposto. Critérios das fases iguais aos do laboratório (lab-v4). Regras que mudam com dados futuros (teste de corte do histórico) ficam fora. Ver `protocol.json` → `triagem`.

## Funil

| Etapa | Regras |
|---|---|
| Regras com sinal testadas | 2738 |
| Repintam (fora) | 100 |
| Sem sinal de compra/venda | 907 |
| Erro ou lentidão | 86 |
| Reprovadas no desenvolvimento | 1317 |
| Reprovadas na validação | 1218 |
| Reprovadas na reserva | 68 |
| **Candidatas** | **135** |

## Passaram no desenvolvimento

| Indicador | Tempo | Regra | Veredito | Dev | Validação | Reserva | DSR | EURUSD | USDJPY |
|---|---|---|---|---|---|---|---|---|---|
| Pivot Breakout High&Low Signals (`pivot-breakout-high-low-signals`) | H4 | Buy Alert / Sell Alert | **CANDIDATA** | 91 op · +330.5R · PF 5.505 | 36 op · +14.7R · PF 1.509 | 81 op · +107.9R · PF 2.627 | 0.0 | não | não |
| Volume-Based Moving Average (`volume-based-moving-average`) | H4 | fechamento x linha 1 | **CANDIDATA** | 261 op · +286.6R · PF 4.291 | 79 op · +22.6R · PF 1.776 | 97 op · +80.1R · PF 3.097 | 0.0 | não | não |
| Relative Strength Heatmap (`relative-strength-heatmap`) | H4 | RSI Heatmap Strong Bull / RSI Heatmap Strong Bear | **CANDIDATA** | 62 op · +280.6R · PF 7.882 | 29 op · +19.0R · PF 1.899 | 54 op · +86.0R · PF 3.024 | 0.0 | não | não |
| Pullback Scalp Trade V2 (`pullback-scalp-trade-v2`) | H4 | marcadores de compra / venda | **CANDIDATA** | 123 op · +262.5R · PF 4.016 | 46 op · +10.8R · PF 1.333 | 93 op · +108.3R · PF 2.514 | 0.0 | não | não |
| Trend Scalper (`trend-scalper`) | H4 | Long Alert / Short Alert | **CANDIDATA** | 122 op · +252.1R · PF 4.027 | 57 op · +12.3R · PF 1.291 | 112 op · +92.8R · PF 2.074 | 0.0 | não | não |
| Philakone 55 EMA Swing Trading (`philakone-ema-swing`) | H4 | Buy Condition / Sell Condition | **CANDIDATA** | 171 op · +237.3R · PF 2.974 | 72 op · +13.2R · PF 1.264 | 135 op · +41.6R · PF 1.428 | 0.0 | não | não |
| Alpha Trading Signal _ Up side Down (`alpha-trading-signal-up-side-down`) | H4 | SuperTrend Buy / SuperTrend Sell | **CANDIDATA** | 229 op · +213.0R · PF 2.558 | 95 op · +16.0R · PF 1.275 | 202 op · +36.7R · PF 1.272 | 0.0 | não | não |
| SuperTrend Channels (`supertrend-channels`) | H4 | fechamento x linha 1 | **CANDIDATA** | 229 op · +213.0R · PF 2.558 | 95 op · +16.0R · PF 1.275 | 202 op · +36.7R · PF 1.272 | 0.0 | não | não |
| SuperTrend + Relative Volume (Kernel Optimized) (`supertrend-relative-volume-kernel`) | H4 | Bullish Trend / Bearish Trend | **CANDIDATA** | 229 op · +213.0R · PF 2.558 | 95 op · +16.0R · PF 1.275 | 202 op · +36.7R · PF 1.272 | 0.0 | não | não |
| Supertrend (`supertrend`) | H4 | Downtrend to Uptrend / Uptrend to Downtrend | **CANDIDATA** | 229 op · +213.0R · PF 2.558 | 95 op · +16.0R · PF 1.275 | 202 op · +36.7R · PF 1.272 | 0.0 | não | não |
| Gaussian Filter Trend (`gaussian-filter-trend`) | H4 | Bullish Trend Signal / Bearish Trend Signal | **CANDIDATA** | 123 op · +206.5R · PF 3.406 | 53 op · +13.1R · PF 1.351 | 96 op · +97.7R · PF 2.446 | 0.0 | não | não |
| AI Trend Navigator [K-Neighbor] (`ai-trend-navigator`) | H4 | Knn Crossover Average Knn / Knn Crossunder Average Knn | **CANDIDATA** | 161 op · +191.6R · PF 2.609 | 63 op · +15.0R · PF 1.372 | 114 op · +87.0R · PF 2.067 | 0.0 | não | não |
| Volume SuperTrend AI (Expo) (`volume-supertrend-ai`) | H4 | 1 Bullish Trend Start / 2 Bearish Trend Start | **CANDIDATA** | 136 op · +190.2R · PF 2.964 | 47 op · +16.5R · PF 1.518 | 106 op · +68.6R · PF 1.878 | 0.0 | não | não |
| RSI Trend Navigator (`rsi-trend-navigator`) | H4 | RSI Trend Bullish / RSI Trend Bearish | **CANDIDATA** | 91 op · +187.7R · PF 3.697 | 39 op · +10.9R · PF 1.388 | 80 op · +49.3R · PF 1.794 | 0.0 | não | não |
| Weis Wave Candle (`weis-wave-candle`) | D1 | Upward Trend Change / Downward Trend Change | **CANDIDATA** | 37 op · +186.1R · PF 12.019 | 17 op · +6.0R · PF 1.672 | 42 op · +29.5R · PF 2.328 | 0.0 | não | não |
| MechArt Moving Average and % Above V1.1 (`mechart-moving-average-and-above-v1-1`) | H4 | fechamento x linha 1 | **CANDIDATA** | 286 op · +176.1R · PF 2.462 | 133 op · +12.8R · PF 1.243 | 230 op · +120.2R · PF 2.184 | 0.0 | não | não |
| Smart Money Breakouts (`smart-money-breakouts`) | H4 | BUY / Sell | **CANDIDATA** | 61 op · +149.9R · PF 4.588 | 40 op · +11.6R · PF 1.389 | 71 op · +79.1R · PF 2.404 | 0.0 | não | não |
| Change-Point Detection (CUSUM) (`change-point-detection`) | H4 | marcadores de compra / venda | **CANDIDATA** | 93 op · +147.9R · PF 3.409 | 31 op · +10.8R · PF 1.572 | 60 op · +86.9R · PF 3.199 | 0.0 | não | não |
| EMA + VWMA + ATR Smoothed BuySell (merged) - TOM ZENG 202509 (`ema-vwma-atr-smoothed-buysell-tom-zeng-202509`) | H4 | Buy Signal / Sell Signal | **CANDIDATA** | 70 op · +136.5R · PF 3.899 | 33 op · +13.2R · PF 1.557 | 68 op · +99.5R · PF 2.926 | 0.0 | não | não |
| SuperSmoother MA Oscillator (`supersmoother-ma-oscillator`) | H4 | marcadores de compra / venda | **CANDIDATA** | 131 op · +133.7R · PF 2.542 | 67 op · +17.7R · PF 1.486 | 96 op · +72.6R · PF 2.094 | 0.0 | não | não |
| RSI Zone Step Lines (`rsi-zone-step-lines`) | D1 | fechamento x linha 1 | **CANDIDATA** | 108 op · +123.0R · PF 5.474 | 48 op · +7.7R · PF 1.47 | 117 op · +23.4R · PF 1.552 | 0.0 | não | não |
| Bilateral Filter For Loop (`bilateral-filter-for-loop`) | D1 | Bilateral Filter FL Long / Bilateral Filter FL Short | **CANDIDATA** | 32 op · +117.3R · PF 9.365 | 14 op · +16.9R · PF 3.765 | 36 op · +31.4R · PF 2.65 | 0.0 | não | não |
| Smooth RSI (`smooth-rsi`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 98 op · +114.0R · PF 4.256 | 37 op · +5.0R · PF 1.412 | 102 op · +19.6R · PF 1.597 | 0.0 | não | não |
| Trendlines with Breaks [LuxAlgo] (`trendlines-with-breaks`) | D1 | Upward Breakout / Downward Breakout | **CANDIDATA** | 40 op · +112.0R · PF 6.746 | 15 op · +13.2R · PF 2.807 | 31 op · +25.1R · PF 2.754 | 0.0 | não | não |
| SMA DMA Crossing Signal (`sma-dma-crossing-signal`) | D1 | BUY indication / SELL indication | **CANDIDATA** | 56 op · +108.9R · PF 6.645 | 29 op · +5.3R · PF 1.426 | 68 op · +20.1R · PF 1.6 | 0.0 | não | não |
| Institutional OrderBlock Pressure (`institutional-orderblock-pressure`) | D1 | Bullish OB Line Crossed Up / Bearish OB Line Crossed Down | **CANDIDATA** | 42 op · +107.8R · PF 6.638 | 18 op · +17.2R · PF 3.481 | 47 op · +24.4R · PF 2.113 | 0.0 | não | não |
| Ehlers Adaptive Trend Indicator (`ehlers-adaptive-trend-indicator`) | D1 | Buy Signal / Sell Signal | **CANDIDATA** | 53 op · +106.5R · PF 6.322 | 25 op · +5.3R · PF 1.446 | 48 op · +31.3R · PF 2.333 | 0.0 | não | não |
| Volume-Weighted Pivot Bands (`volume-weighted-pivot-bands`) | D1 | Cross Above R1 / Cross Below S1 | **CANDIDATA** | 45 op · +103.2R · PF 6.302 | 22 op · +5.1R · PF 1.432 | 43 op · +28.8R · PF 2.207 | 0.0 | não | não |
| Volatility-Gated Trend Oscillator (`volatility-gated-trend-oscillator`) | D1 | Bullish Trend Signal / Bearish Trend Signal | **CANDIDATA** | 34 op · +103.0R · PF 6.791 | 12 op · +9.5R · PF 2.997 | 30 op · +25.1R · PF 2.758 | 0.0 | não | não |
| Perforance integral (`perforance-integral`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 82 op · +100.1R · PF 4.758 | 39 op · +8.2R · PF 1.613 | 86 op · +36.8R · PF 2.44 | 0.0 | não | não |
| Normalized Candles RSI (`normalized-candles-rsi`) | D1 | Norm Close Cross Above 50 / Norm Close Cross Below 50 | **CANDIDATA** | 182 op · +99.7R · PF 3.616 | 67 op · +6.8R · PF 1.466 | 129 op · +30.7R · PF 1.966 | 0.0 | não | não |
| CVD (Cumulative Volume Delta) (`cvd-rupward`) | D1 | CVD Cross Up MA B Alert / CVD Cross Down MA B Alert | **CANDIDATA** | 104 op · +99.1R · PF 4.976 | 33 op · +8.7R · PF 1.819 | 116 op · +25.1R · PF 1.731 | 0.0 | não | não |
| Trend Regularity Adaptive MA (`trama`) | D1 | fechamento x linha 1 | **CANDIDATA** | 128 op · +99.1R · PF 4.19 | 43 op · +7.0R · PF 1.486 | 97 op · +44.9R · PF 2.954 | 0.0 | não | não |
| Pivot Breakout High&Low Signals (`pivot-breakout-high-low-signals`) | D1 | Bullish Pivot Breakout / Bearish Pivot Breakout | **CANDIDATA** | 37 op · +98.4R · PF 5.645 | 18 op · +6.6R · PF 1.784 | 38 op · +27.3R · PF 2.405 | 0.0 | não | não |
| Pivot Hilo Support n Resistance Levels R3-3 by JustUncleL (`pivot-hilo-support-n-resistance-levels-r3-3`) | D1 | Fractal Break Long / Fractal Break Short | **CANDIDATA** | 37 op · +98.4R · PF 5.645 | 19 op · +5.3R · PF 1.562 | 38 op · +27.3R · PF 2.405 | 0.0 | não | não |
| Interpolated Median Volatility LSMA | Otto (`interpolated-median-volatility-lsma-otto`) | D1 | IMVL long / IMVL short | **CANDIDATA** | 40 op · +98.3R · PF 6.139 | 14 op · +12.3R · PF 3.414 | 34 op · +29.6R · PF 2.881 | 0.0 | não | não |
| RMA ATR Bands (`rma-atr-bands`) | D1 | RMA ATR Bands Long / RMA ATR Bands Short | **CANDIDATA** | 36 op · +98.1R · PF 8.177 | 17 op · +4.8R · PF 1.548 | 37 op · +25.6R · PF 2.329 | 0.0 | não | não |
| Nadaraya-Watson Trend (`nadaraya-watson-trend`) | D1 | Source Cross Above Upper Band / Source Cross Below Lower Band | **CANDIDATA** | 46 op · +97.8R · PF 4.903 | 16 op · +8.5R · PF 2.092 | 37 op · +33.9R · PF 2.867 | 0.0 | não | não |
| Smoothed Source Weighted EMA (`smoothed-source-weighted-ema`) | D1 | marcadores de compra / venda | **CANDIDATA** | 44 op · +97.2R · PF 6.283 | 15 op · +7.9R · PF 2.079 | 50 op · +26.6R · PF 2.049 | 0.0 | não | não |
| Elliott Wave Oscillator (`elliott-wave-oscillator`) | D1 | linha 1 x zero | **CANDIDATA** | 60 op · +97.0R · PF 4.765 | 31 op · +4.9R · PF 1.404 | 62 op · +32.3R · PF 2.15 | 0.0 | não | não |
| Kalman Hull Bands For Loop | RakoQuant (`kalman-hull-bands-for-loop-rakoquant`) | D1 | RakoQuant Bull Breakout / RakoQuant Bear Breakout | **CANDIDATA** | 38 op · +96.9R · PF 5.935 | 13 op · +8.9R · PF 2.729 | 35 op · +23.6R · PF 2.271 | 0.0 | não | não |
| Moneyball EMA-MACD indicator (`moneyball-ema-macd-indicator`) | D1 | MACD New High Above Zero Line / MACD New Low Below Zero Line | **CANDIDATA** | 40 op · +96.2R · PF 6.387 | 18 op · +8.2R · PF 1.863 | 32 op · +24.6R · PF 2.552 | 0.0 | não | não |
| Conversion Periods (`ichimoku-oscillator`) | D1 | marcadores de compra / venda | **CANDIDATA** | 37 op · +95.3R · PF 5.95 | 14 op · +8.9R · PF 2.592 | 34 op · +14.2R · PF 1.701 | 0.0 | não | não |
| AllMA Trend Radar (`allma-trend-radar`) | D1 | marcadores de compra / venda | **CANDIDATA** | 92 op · +94.6R · PF 3.838 | 38 op · +3.8R · PF 1.243 | 72 op · +17.2R · PF 1.496 | 0.0 | não | não |
| Dual MA SD Oscillator (`dual-ma-sd-oscillator`) | D1 | Bull Signal / Bear Signal | **CANDIDATA** | 38 op · +93.5R · PF 6.879 | 17 op · +4.4R · PF 1.44 | 41 op · +23.2R · PF 2.087 | 0.0 | não | não |
| Double RSI (`double-rsi`) | D1 | DRSI: Buy / DRSI: Sell | **CANDIDATA** | 44 op · +93.4R · PF 5.692 | 15 op · +7.0R · PF 1.947 | 48 op · +22.0R · PF 1.834 | 0.0 | não | não |
| Volume Weighted RSI (VW RSI) (`volume-weighted-rsi`) | D1 | marcadores de compra / venda | **CANDIDATA** | 201 op · +92.7R · PF 3.213 | 79 op · +4.6R · PF 1.236 | 178 op · +22.0R · PF 1.477 | 0.0 | não | não |
| Multitimeframe Fair Value Gap – FVG (`multitimeframe-fair-value-gap-fvg`) | D1 | fechamento x linha 1 | **CANDIDATA** | 180 op · +92.4R · PF 3.12 | 79 op · +5.5R · PF 1.279 | 151 op · +32.2R · PF 1.921 | 0.0 | não | não |
| Triple MA For Loop (`triple-ma-for-loop`) | D1 | marcadores de compra / venda | **CANDIDATA** | 30 op · +92.3R · PF 6.526 | 17 op · +4.2R · PF 1.458 | 27 op · +31.0R · PF 3.431 | 0.0 | não | não |
| Kalman Hull Kijun (`kalman-hull-kijun`) | D1 | Kalman Hull Kijun Long / Kalman Hull Kijun Short | **CANDIDATA** | 112 op · +90.8R · PF 3.891 | 54 op · +6.1R · PF 1.382 | 97 op · +38.8R · PF 2.333 | 0.0 | não | não |
| EMA/RMA clouds by Alpachino (`ema-rma-clouds-by-alpachino`) | D1 | fechamento x linha 1 | **CANDIDATA** | 94 op · +90.1R · PF 4.858 | 41 op · +6.4R · PF 1.49 | 85 op · +34.0R · PF 2.507 | 0.0 | não | não |
| Muses afl script (`muses-afl-script`) | H4 | Buy Alert / Sell Alert | **CANDIDATA** | 135 op · +89.8R · PF 2.005 | 39 op · +20.2R · PF 1.866 | 106 op · +50.4R · PF 1.622 | 0.0 | não | não |
| Volume-Weighted Money Flow (`volume-weighted-money-flow`) | D1 | Bullish Strength: Absolute Consensus (100%) / Bearish Strength: Absolute Consensus (100%) | **CANDIDATA** | 39 op · +89.7R · PF 6.068 | 20 op · +9.8R · PF 2.004 | 51 op · +22.7R · PF 1.802 | 0.0 | não | não |
| Elder's force index (`elder-force`) | D1 | linha 1 x zero | **CANDIDATA** | 183 op · +89.6R · PF 2.838 | 67 op · +8.5R · PF 1.49 | 166 op · +17.0R · PF 1.338 | 0.0 | não | não |
| Sell & Buy Rates (`sell-buy-rates`) | D1 | linha 1 x zero | **CANDIDATA** | 163 op · +89.1R · PF 3.092 | 79 op · +4.6R · PF 1.201 | 144 op · +25.8R · PF 1.559 | 0.0 | não | não |
| Awesome_Accelerator_Zone Oscillator (`awesome-accelerator-zone-oscillator`) | D1 | linha 1 x zero | **CANDIDATA** | 66 op · +89.0R · PF 4.168 | 29 op · +3.0R · PF 1.246 | 60 op · +29.9R · PF 2.067 | 0.0 | não | não |
| Volumetric Entropy Index (`volumetric-entropy-index`) | D1 | EMA DNA Bull Cross / EMA DNA Bear Cross | **CANDIDATA** | 243 op · +88.0R · PF 2.674 | 93 op · +4.3R · PF 1.202 | 198 op · +28.1R · PF 1.581 | 0.0 | não | não |
| Adaptive Trend Flow [QuantAlgo] (`adaptive-trend-flow`) | D1 | Adaptive Trend Flow Long / Adaptive Trend Flow Short | **CANDIDATA** | 40 op · +87.9R · PF 5.583 | 17 op · +5.8R · PF 1.755 | 41 op · +10.2R · PF 1.421 | 0.0 | não | não |
| ADX and DI (`adx-and-di`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 116 op · +87.7R · PF 3.492 | 39 op · +11.2R · PF 2.032 | 103 op · +30.9R · PF 1.885 | 0.0 | não | não |
| DMI Delta by 0xjcf (`dmi-delta-by-0xjcf`) | D1 | linha 1 x zero | **CANDIDATA** | 116 op · +87.7R · PF 3.492 | 39 op · +11.2R · PF 2.032 | 103 op · +30.9R · PF 1.885 | 0.0 | não | não |
| MACD With Crossings and Above Below Zero (`macd-with-crossings-and-above-below-zero`) | D1 | marcadores de compra / venda | **CANDIDATA** | 117 op · +87.7R · PF 3.471 | 40 op · +13.5R · PF 2.242 | 104 op · +30.4R · PF 1.855 | 0.0 | não | não |
| ADX with Shaded Zone (`adx-with-shaded-zone`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 118 op · +87.5R · PF 3.506 | 41 op · +10.8R · PF 1.967 | 113 op · +26.7R · PF 1.703 | 0.0 | não | não |
| TR High/Low meter (`tr-high-low-meter`) | D1 | Buy Signal / Sell Signal | **CANDIDATA** | 60 op · +87.1R · PF 4.606 | 27 op · +8.0R · PF 1.614 | 50 op · +22.8R · PF 1.826 | 0.0 | não | não |
| CM_Pivot Points_M-W-D-4H-1H_Filtered (`cm-pivot-points-filtered`) | D1 | fechamento x linha 1 | **CANDIDATA** | 46 op · +87.1R · PF 5.485 | 13 op · +6.6R · PF 2.296 | 47 op · +31.2R · PF 3.072 | 0.0 | não | não |
| MESA Phase-Adaptive Band Trend (`mesa-phase-adaptive-band-trend`) | D1 | Long Signal / Short Signal | **CANDIDATA** | 42 op · +86.8R · PF 6.793 | 18 op · +6.9R · PF 1.639 | 49 op · +14.2R · PF 1.504 | 0.0 | não | não |
| Williams alligator (`williams-alligator`) | D1 | fechamento x linha 1 | **CANDIDATA** | 130 op · +86.7R · PF 3.442 | 49 op · +3.3R · PF 1.2 | 94 op · +31.6R · PF 2.055 | 0.0 | não | não |
| Trend with ADX/EMA - Buy & Sell Signals (`trend-with-adx-ema-buy-sell-signals`) | D1 | Trend Green Alert / Trend Red Alert | **CANDIDATA** | 119 op · +86.7R · PF 3.381 | 40 op · +13.5R · PF 2.242 | 104 op · +30.4R · PF 1.855 | 0.0 | não | não |
| Ichimoku Kinkō hyō 目均衡表 (`ichimoku-kink-hy`) | H4 | Signal: Bullish Reversal ▲ / Signal: Bearish Reversal ▼ | **CANDIDATA** | 101 op · +86.5R · PF 2.218 | 36 op · +23.3R · PF 2.087 | 72 op · +41.6R · PF 1.913 | 0.0 | não | não |
| Dynamic Trend Channel (DTC) (`dynamic-trend-channel`) | D1 | Buy Alert / Sell Alert | **CANDIDATA** | 35 op · +86.1R · PF 5.396 | 14 op · +5.7R · PF 1.793 | 29 op · +18.2R · PF 2.009 | 0.0 | não | não |
| Directional Indicator Crossovers v1 (`directional-indicator-crossovers-v1`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 137 op · +85.7R · PF 3.059 | 61 op · +4.0R · PF 1.223 | 110 op · +31.2R · PF 1.881 | 0.0 | não | não |
| OBV + Custom MA Strategy (`obv-custom-ma-strategy`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 247 op · +85.6R · PF 2.652 | 93 op · +5.5R · PF 1.266 | 194 op · +34.5R · PF 1.766 | 0.0 | não | não |
| Volatility Breakout Pulse (VBP FIX) (`volatility-breakout-pulse`) | D1 | BUY ALERT / SELL ALERT | **CANDIDATA** | 36 op · +85.5R · PF 5.758 | 15 op · +8.6R · PF 2.136 | 40 op · +13.2R · PF 1.561 | 0.0 | não | não |
| HTC peppermint_07 CCI w signal + s&r RSI (`htc-peppermint-07-cci-w-signal-s-r-rsi`) | D1 | marcadores de compra / venda | **CANDIDATA** | 33 op · +85.0R · PF 6.54 | 16 op · +9.8R · PF 2.096 | 32 op · +15.6R · PF 1.746 | 0.0 | não | não |
| BACAP PRICE STRUCTURE 21 EMA TREND (`bacap-price-structure-21-ema-trend`) | D1 | fechamento x linha 1 | **CANDIDATA** | 185 op · +84.2R · PF 2.986 | 77 op · +5.6R · PF 1.289 | 146 op · +23.1R · PF 1.567 | 0.0 | não | não |
| Emergent Rays - NovaTheMachine (`emergent-rays-novathemachine`) | D1 | fechamento x linha 1 | **CANDIDATA** | 185 op · +84.2R · PF 2.986 | 77 op · +5.6R · PF 1.289 | 146 op · +23.1R · PF 1.567 | 0.0 | não | não |
| Volume Spike and Contraction Indicator (`volume-spike-and-contraction-indicator`) | D1 | marcadores de compra / venda | **CANDIDATA** | 107 op · +82.4R · PF 3.057 | 45 op · +4.6R · PF 1.247 | 110 op · +8.9R · PF 1.191 | 0.0 | não | não |
| Market Structure Trend (`market-structure-trend`) | D1 | Bullish Structure Shift / Bearish Structure Shift | **CANDIDATA** | 32 op · +81.7R · PF 5.217 | 17 op · +4.5R · PF 1.53 | 34 op · +9.7R · PF 1.5 | 0.0 | não | não |
| Acceleration Bands HTF (`acceleration-bands-htf`) | D1 | fechamento x linha 1 | **CANDIDATA** | 78 op · +79.9R · PF 3.655 | 17 op · +11.4R · PF 4.17 | 64 op · +18.7R · PF 1.869 | 0.0 | não | não |
| Volume-Based Moving Average (`volume-based-moving-average`) | D1 | fechamento x linha 1 | **CANDIDATA** | 145 op · +79.2R · PF 3.165 | 29 op · +11.1R · PF 2.499 | 47 op · +34.9R · PF 3.404 | 0.0 | não | não |
| AI Source Switching Moving Average (`ai-source-switching-moving-average`) | D1 | AI Trend Flip Up / AI Trend Flip Down | **CANDIDATA** | 44 op · +76.7R · PF 4.486 | 20 op · +6.9R · PF 1.672 | 44 op · +10.5R · PF 1.342 | 0.0 | não | não |
| Clean Buy Sell Pro (`clean-buy-sell-pro`) | D1 | BUY Signal / SELL Signal | **CANDIDATA** | 30 op · +76.4R · PF 5.898 | 14 op · +4.8R · PF 1.788 | 30 op · +33.1R · PF 2.702 | 0.0 | não | não |
| Volatility Bands (`volatility-bands`) | D1 | fechamento x linha 1 | **CANDIDATA** | 82 op · +76.1R · PF 3.892 | 45 op · +8.7R · PF 1.724 | 55 op · +20.9R · PF 2.122 | 0.0 | não | não |
| ROC-Weighted MA Oscillator (`roc-weighted-ma-oscillator`) | D1 | marcadores de compra / venda | **CANDIDATA** | 30 op · +75.8R · PF 6.048 | 13 op · +5.2R · PF 1.884 | 33 op · +15.1R · PF 1.799 | 0.0 | não | não |
| Smart Money Concepts (SMC) (`smart-money-concepts-luxalgo`) | D1 | Internal Bullish CHoCH / Internal Bearish CHoCH | **CANDIDATA** | 41 op · +74.4R · PF 4.599 | 21 op · +2.9R · PF 1.286 | 38 op · +20.5R · PF 1.96 | 0.0 | não | não |
| Dynamic Flow Ribbons (`dynamic-flow-ribbons`) | D1 | fechamento x linha 1 | **CANDIDATA** | 141 op · +73.8R · PF 3.22 | 53 op · +4.6R · PF 1.274 | 144 op · +23.0R · PF 1.567 | 0.0 | não | não |
| Trend Predictor Ribbon Clone - Fixed roj karo moj karo (`trend-predictor-ribbon`) | D1 | marcadores de compra / venda | **CANDIDATA** | 59 op · +73.3R · PF 3.861 | 27 op · +6.3R · PF 1.522 | 66 op · +15.2R · PF 1.419 | 0.0 | não | não |
| Consecutive Higher/Lower Closings (`consecutive-higher-lower-closings`) | D1 | Buy Alert / Sell Alert | **CANDIDATA** | 96 op · +72.7R · PF 2.906 | 41 op · +4.0R · PF 1.242 | 101 op · +14.5R · PF 1.374 | 0.0 | não | não |
| SMA Squeeze Oscillator (`sma-squeeze-oscillator`) | D1 | Bull Cross Alert / Bear Cross Alert | **CANDIDATA** | 33 op · +71.9R · PF 5.172 | 13 op · +7.5R · PF 2.338 | 29 op · +40.9R · PF 3.215 | 0.0 | não | não |
| Ultimate RSI [LuxAlgo] (`ultimate-rsi`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 165 op · +71.4R · PF 2.421 | 63 op · +4.9R · PF 1.249 | 122 op · +19.9R · PF 1.443 | 0.0 | não | não |
| VOLD Ratio Histogram (`vold-ratio-histogram`) | D1 | linha 1 x zero | **CANDIDATA** | 132 op · +71.2R · PF 2.715 | 59 op · +16.5R · PF 2.625 | 122 op · +18.3R · PF 1.44 | 0.0 | não | não |
| Fibonacci Levels (`fibonacci-levels`) | D1 | fechamento x linha 1 | **CANDIDATA** | 82 op · +68.3R · PF 3.678 | 19 op · +10.4R · PF 3.246 | 55 op · +25.7R · PF 2.24 | 0.0 | não | não |
| Entry Points (`entry-points`) | D1 | marcadores de compra / venda | **CANDIDATA** | 84 op · +68.2R · PF 3.654 | 20 op · +10.1R · PF 3.045 | 56 op · +25.1R · PF 2.176 | 0.0 | não | não |
| Double Median ATR Bands | MisinkoMaster (`double-median-atr-bands-misinkomaster`) | D1 | fechamento x linha 1 | **CANDIDATA** | 133 op · +67.9R · PF 2.826 | 49 op · +10.5R · PF 1.724 | 122 op · +14.0R · PF 1.319 | 0.0 | não | não |
| Adaptive Entropy Trend (`adaptive-entropy-trend`) | D1 | Bullish Trend Signal / Bearish Trend Signal | **CANDIDATA** | 30 op · +67.7R · PF 4.968 | 11 op · +5.3R · PF 2.04 | 29 op · +15.3R · PF 1.92 | 0.0 | não | não |
| High Volume Buyers/Sellers+ (`high-volume-buyers-sellers`) | D1 | marcadores de compra / venda | **CANDIDATA** | 37 op · +66.9R · PF 4.308 | 12 op · +4.9R · PF 1.921 | 19 op · +18.4R · PF 2.977 | 0.0 | não | não |
| Price Action Bands | Trend & Volatility (`price-action-bands-trend-volatility`) | D1 | fechamento x linha 1 | **CANDIDATA** | 88 op · +66.0R · PF 2.993 | 32 op · +6.8R · PF 1.515 | 59 op · +12.4R · PF 1.525 | 0.0 | não | não |
| FuTech V-Spike & V-Highlighter (`futech-v-spike-v-highlighter`) | D1 | Bullish Highest Volume Candle / Bearish Highest Volume Candle | **CANDIDATA** | 43 op · +65.6R · PF 4.374 | 19 op · +9.5R · PF 1.998 | 45 op · +14.4R · PF 1.546 | 0.0 | não | não |
| Volatility stop (`volatility-stop`) | D1 | fechamento x linha 1 | **CANDIDATA** | 83 op · +63.6R · PF 2.625 | 29 op · +5.8R · PF 1.45 | 78 op · +12.0R · PF 1.304 | 0.0 | não | não |
| Wavelet Transform Trend (`wavelet-transform-trend`) | D1 | Bullish Wavelet Trend / Bearish Wavelet Trend | **CANDIDATA** | 41 op · +63.5R · PF 4.599 | 21 op · +6.7R · PF 1.605 | 48 op · +23.0R · PF 1.801 | 0.0 | não | não |
| 72s: Adaptive Hull Moving Average+ (`adaptive-hull-ma`) | D1 | marcadores de compra / venda | **CANDIDATA** | 44 op · +62.2R · PF 3.533 | 23 op · +5.0R · PF 1.559 | 56 op · +30.0R · PF 2.213 | 0.0 | não | não |
| Adaptive RSI | Lyro RS (`adaptive-rsi-lyro-rs`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 283 op · +60.7R · PF 1.834 | 131 op · +4.6R · PF 1.162 | 222 op · +11.0R · PF 1.174 | 0.0 | não | não |
| Traders Reality Main (`traders-reality-main`) | D1 | Green Vector Candle / Red Vector Candle | **CANDIDATA** | 92 op · +60.5R · PF 2.517 | 36 op · +8.2R · PF 1.522 | 73 op · +9.9R · PF 1.254 | 0.0 | não | não |
| Zero-Lag GARCH Bands | NAL (`zero-lag-garch-bands-nal`) | D1 | fechamento x linha 1 | **CANDIDATA** | 143 op · +60.4R · PF 2.323 | 43 op · +3.7R · PF 1.265 | 88 op · +15.4R · PF 1.443 | 0.0 | não | não |
| FuTech V-Spike & V-Highlighter (`futech-v-spike-v-highlighter`) | D1 | Bullish Volume Spike / Bearish Volume Spike | **CANDIDATA** | 86 op · +56.4R · PF 2.445 | 36 op · +4.8R · PF 1.296 | 71 op · +17.7R · PF 1.452 | 0.0 | não | não |
| Adaptive Friction Filter (AFF) (`adaptive-friction-filter`) | D1 | Bullish Trend Signal / Bearish Trend Signal | **CANDIDATA** | 147 op · +55.3R · PF 1.949 | 55 op · +4.8R · PF 1.243 | 120 op · +17.1R · PF 1.369 | 0.0 | não | não |
| Curved Trend Channels (`curved-trend-channels`) | D1 | fechamento x linha 1 | **CANDIDATA** | 147 op · +55.0R · PF 2.246 | 33 op · +8.0R · PF 1.837 | 108 op · +14.8R · PF 1.368 | 0.0 | não | não |
| B + A + D v0.4 (`b-a-d-v0-4`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 246 op · +53.6R · PF 1.767 | 105 op · +6.8R · PF 1.228 | 197 op · +21.0R · PF 1.377 | 0.0 | não | não |
| MACDAS (`macdas`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 193 op · +53.2R · PF 1.843 | 83 op · +6.1R · PF 1.24 | 135 op · +33.6R · PF 1.817 | 0.0 | não | não |
| AI-Weighted RSI (`ai-weighted-rsi`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 301 op · +52.2R · PF 1.67 | 131 op · +6.5R · PF 1.238 | 214 op · +16.5R · PF 1.303 | 0.0 | não | não |
| Strong Demands & Supplies + Liquidity | Zonas de Compra e Venda (`strong-demands-supplies-liquidity-zonas-de`) | D1 | Bullish Engulfing / Bearish Engulfing | **CANDIDATA** | 147 op · +51.8R · PF 2.056 | 65 op · +11.4R · PF 1.699 | 132 op · +22.1R · PF 1.453 | 0.0 | não | não |
| TMA Overlay (`tma-overlay`) | D1 | Bullish Engulfing / Bearish Engulfing | **CANDIDATA** | 147 op · +51.8R · PF 2.056 | 65 op · +11.4R · PF 1.699 | 132 op · +22.1R · PF 1.453 | 0.0 | não | não |
| Price Action: Engulfing Patterns (`price-action-engulfing-patterns`) | D1 | marcadores de compra / venda | **CANDIDATA** | 145 op · +51.7R · PF 2.055 | 60 op · +9.7R · PF 1.589 | 132 op · +22.1R · PF 1.453 | 0.0 | não | não |
| TMO (True Momentum Oscillator) (`tmo`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 267 op · +51.5R · PF 1.673 | 111 op · +5.6R · PF 1.189 | 199 op · +18.3R · PF 1.322 | 0.0 | não | não |
| SMI ergodic oscillator (`smi-ergodic-osc`) | D1 | linha 1 x zero | **CANDIDATA** | 263 op · +51.0R · PF 1.651 | 101 op · +5.3R · PF 1.189 | 186 op · +14.6R · PF 1.267 | 0.0 | não | não |
| SMI ergodic indicator (`smi-ergodic`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 263 op · +51.0R · PF 1.651 | 101 op · +5.3R · PF 1.189 | 186 op · +14.6R · PF 1.267 | 0.0 | não | não |
| Double Median SD Bands | MisinkoMaster (`double-median-sd-bands-misinkomaster`) | D1 | fechamento x linha 1 | **CANDIDATA** | 101 op · +47.9R · PF 2.14 | 45 op · +11.5R · PF 1.813 | 94 op · +12.3R · PF 1.352 | 0.0 | não | não |
| Voss Predictive Filter (`voss-predictive-filter`) | D1 | Voss Predictive Filter: Above Zero / Voss Predictive Filter: Below Zero | **CANDIDATA** | 222 op · +47.4R · PF 1.644 | 88 op · +9.2R · PF 1.366 | 198 op · +11.1R · PF 1.17 | 0.0 | não | não |
| Buy Sell Signal (`buy-sell-signal-kelfry98`) | D1 | 🟢 BUY Signal / 🔴 SELL Signal | **CANDIDATA** | 85 op · +46.9R · PF 2.43 | 36 op · +4.7R · PF 1.315 | 66 op · +27.5R · PF 2.093 | 0.0 | não | não |
| Length (`redk-vader`) | D1 | *  VADER Speeding Up / ** VADER Slowing Down | **CANDIDATA** | 182 op · +46.2R · PF 1.725 | 72 op · +9.8R · PF 1.483 | 137 op · +14.1R · PF 1.273 | 0.0 | não | não |
| TASC 2026.04 A Synthetic Oscillator (`tasc-2026-04-a-synthetic-oscillator`) | D1 | linha 1 x zero | **CANDIDATA** | 240 op · +45.7R · PF 1.617 | 93 op · +8.5R · PF 1.351 | 201 op · +11.7R · PF 1.184 | 0.0 | não | não |
| MACD DEMA (`macd-dema`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 222 op · +45.2R · PF 1.632 | 84 op · +7.3R · PF 1.288 | 162 op · +15.3R · PF 1.308 | 0.0 | não | não |
| Trend Flow Oscillator (CMF + MFI) + ADX (`trend-flow-oscillator-adx`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 115 op · +44.9R · PF 2.077 | 35 op · +8.0R · PF 1.562 | 80 op · +13.8R · PF 1.368 | 0.0 | não | não |
| Bollinger Awesome Alert R1.1 (`bollinger-awesome-alert`) | D1 | BBAWE Buy / BBAWE Sell | **CANDIDATA** | 79 op · +42.1R · PF 2.219 | 34 op · +3.4R · PF 1.242 | 78 op · +21.6R · PF 1.642 | 0.0 | não | não |
| Easy Entry/Exit Trend Colors (`easy-trend-colors`) | D1 | marcadores de compra / venda | **CANDIDATA** | 193 op · +41.0R · PF 1.623 | 64 op · +7.9R · PF 1.369 | 125 op · +11.5R · PF 1.235 | 0.0 | não | não |
| Delta-RSI Oscillator (`delta-rsi-oscillator`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 227 op · +40.8R · PF 1.57 | 90 op · +4.3R · PF 1.155 | 180 op · +12.7R · PF 1.209 | 0.0 | não | não |
| FVG Positioning Average (`fvg-positioning-average`) | D1 | fechamento x linha 1 | **CANDIDATA** | 52 op · +40.8R · PF 3.221 | 34 op · +7.9R · PF 1.691 | 82 op · +34.5R · PF 2.388 | 0.0 | não | não |
| Order Block Detector (`order-block-detector`) | D1 | Bullish OB Formed / Bearish OB Formed | **CANDIDATA** | 82 op · +40.7R · PF 2.013 | 35 op · +7.0R · PF 1.493 | 67 op · +31.0R · PF 2.101 | 0.0 | não | não |
| Volume Candle Highlighter (`volume-candle-highlighter`) | D1 | marcadores de compra / venda | **CANDIDATA** | 62 op · +40.6R · PF 2.132 | 20 op · +10.1R · PF 2.38 | 37 op · +10.9R · PF 1.475 | 0.0 | não | não |
| Trend-Pro (`trend-pro`) | D1 | marcadores de compra / venda | **CANDIDATA** | 59 op · +39.0R · PF 2.381 | 26 op · +7.3R · PF 1.611 | 55 op · +24.3R · PF 1.912 | 0.0 | não | não |
| ML Moving Average (`ml-moving-average`) | D1 | fechamento x linha 1 | **CANDIDATA** | 233 op · +36.1R · PF 1.492 | 91 op · +6.7R · PF 1.275 | 189 op · +10.6R · PF 1.184 | 0.0 | não | não |
| Fourier series Model Of The Market (`fourier-series-model-of-the-market`) | D1 | FSMM: Above Zero / FSMM: Below Zero | **CANDIDATA** | 334 op · +28.7R · PF 1.299 | 131 op · +5.3R · PF 1.16 | 254 op · +10.5R · PF 1.146 | 0.0 | não | não |
| Vortex Pro with Moving average (`vortex-pro-with-moving-average`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 299 op · +24.4R · PF 1.275 | 122 op · +6.0R · PF 1.203 | 205 op · +7.3R · PF 1.128 | 0.0 | não | não |
| QTechLabs Machine Learning Logistic Regression Indicator (`qtechlabs-machine-learning-logistic-regression-indicator`) | D1 | Buy Signal / Sell Signal | **CANDIDATA** | 115 op · +24.1R · PF 1.446 | 44 op · +7.5R · PF 1.444 | 82 op · +6.4R · PF 1.169 | 0.0 | não | não |
| Stochastic momentum index (`smi`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 324 op · +23.8R · PF 1.244 | 124 op · +6.7R · PF 1.216 | 235 op · +23.7R · PF 1.378 | 0.0 | não | não |
| RCI ribbon (`rci-ribbon`) | D1 | linha 1 x linha 2 | **CANDIDATA** | 181 op · +19.1R · PF 1.274 | 66 op · +4.3R · PF 1.202 | 117 op · +14.7R · PF 1.375 | 0.0 | não | não |
| Indicador Millo SMA20-SMA200-AO-RSI M1 (`indicador-millo-sma20-sma200-ao-rsi-m1`) | H4 | Buy / Sell | **REPROVADA_RESERVA** | 64 op · +387.1R · PF 9.183 | 32 op · +8.7R · PF 1.351 | 61 op · +45.1R · PF 1.836 | 0.0 | - | - |
| Smart Money Breakout Signals (`smart-money-breakout-signals`) | H4 | Bullish Signal / Bearish Signal | **REPROVADA_RESERVA** | 64 op · +341.8R · PF 8.211 | 33 op · +15.6R · PF 1.634 | 75 op · +71.7R · PF 2.083 | 0.0 | - | - |
| CHN BUY SELL with EMA 200 (`chn-buy-sell-with-ema-200`) | H4 | BUY Signal / SELL Signal | **REPROVADA_RESERVA** | 131 op · +329.6R · PF 4.961 | 56 op · +25.1R · PF 1.745 | 136 op · +115.0R · PF 2.205 | 0.0 | - | - |
| MA Ribbon 5EMA | 20EMA | 50SMA | 200EMA (`ma-ribbon-5ema-20ema-50sma-200ema`) | H4 | Price Crossed Above 200 EMA / Price Crossed Below 200 EMA | **REPROVADA_RESERVA** | 318 op · +299.2R · PF 3.578 | 95 op · +30.2R · PF 1.858 | 269 op · +99.6R · PF 1.85 | 0.0 | - | - |
| WAE Sniper Scalp XAUUSD M1 Tuned (`wae-sniper-scalp-xauusd-m1-tuned`) | H4 | marcadores de compra / venda | **REPROVADA_RESERVA** | 214 op · +295.4R · PF 3.771 | 69 op · +27.7R · PF 1.774 | 177 op · +108.9R · PF 2.154 | 0.0 | - | - |
| Dynamic Score PSAR (`dynamic-score-psar`) | H4 | Histogram Turned Bullish / Histogram Turned Bearish | **REPROVADA_RESERVA** | 261 op · +265.1R · PF 2.88 | 129 op · +15.3R · PF 1.197 | 255 op · +75.1R · PF 1.458 | 0.0 | - | - |
| Normalized Candles RSI (`normalized-candles-rsi`) | H4 | Norm Close Cross Above 70 / Norm Close Cross Below 30 | **REPROVADA_RESERVA** | 111 op · +263.2R · PF 4.564 | 53 op · +20.2R · PF 1.577 | 127 op · +70.4R · PF 1.68 | 0.0 | - | - |
| Mix1 : Ema Cross + Trend Channel (`mix1-ema-cross-trend-channel`) | H4 | Buy / Sell | **REPROVADA_RESERVA** | 106 op · +253.7R · PF 3.979 | 44 op · +23.3R · PF 1.716 | 93 op · +88.5R · PF 2.211 | 0.0 | - | - |
| CM_Pivot Points_M-W-D-4H-1H_Filtered (`cm-pivot-points-filtered`) | H4 | fechamento x linha 1 | **REPROVADA_RESERVA** | 92 op · +245.8R · PF 7.308 | 23 op · +16.0R · PF 2.309 | 103 op · +67.6R · PF 2.257 | 0.0 | - | - |
| Big Snapper Alerts R3.0 (`big-snapper-alerts`) | H4 | marcadores de compra / venda | **REPROVADA_RESERVA** | 238 op · +239.0R · PF 2.559 | 104 op · +14.7R · PF 1.217 | 241 op · +50.6R · PF 1.299 | 0.0 | - | - |
| Supertrend MTF Heikin Ashi (`supertrend-mtf-heikin-ashi`) | H4 | Supertrend Trend Up / Supertrend  Trend Down | **REPROVADA_RESERVA** | 269 op · +229.8R · PF 2.569 | 123 op · +14.6R · PF 1.214 | 251 op · +75.7R · PF 1.459 | 0.0 | - | - |
| Dynamic Score PSAR (`dynamic-score-psar`) | H4 | Bullish Reversal / Bearish Reversal | **REPROVADA_RESERVA** | 210 op · +226.7R · PF 3.055 | 111 op · +11.5R · PF 1.171 | 199 op · +52.9R · PF 1.395 | 0.0 | - | - |
| Institutional OrderBlock Pressure (`institutional-orderblock-pressure`) | H4 | Bullish OB Line Crossed Up / Bearish OB Line Crossed Down | **REPROVADA_RESERVA** | 272 op · +220.5R · PF 2.392 | 123 op · +12.3R · PF 1.179 | 256 op · +68.0R · PF 1.393 | 0.0 | - | - |
| Sigmoid RSI | NAL (`sigmoid-rsi-nal`) | H4 | marcadores de compra / venda | **REPROVADA_RESERVA** | 253 op · +219.8R · PF 2.545 | 103 op · +14.9R · PF 1.239 | 214 op · +74.8R · PF 1.567 | 0.0 | - | - |
| Machine Learning RSI | AI Classification & Ranking (`machine-learning-rsi-ai-classification-ranking`) | H4 | Trend Flip Up / Trend Flip Down | **REPROVADA_RESERVA** | 299 op · +217.5R · PF 2.354 | 145 op · +15.0R · PF 1.179 | 283 op · +67.3R · PF 1.378 | 0.0 | - | - |

## Placebo e múltiplos testes

Das 135 candidatas, 68 ganham do placebo com folga na validação e na reserva (resultado real maior que o dobro da mediana de 20 sorteios de entradas ao acaso, mais 5R). O Deflated Sharpe, calculado com todas as regras testadas, ficou abaixo de 0,5 em todas: com milhares de tentativas, nenhum desenvolvimento sozinho prova que não é sorte. Por isso o que vale é o teste fora da amostra (validação, reserva e outros ativos).

## Meta (passa no BTC e em outro ativo, mesmos parâmetros)

Ainda não.

Candidata da triagem não é estratégia aprovada: o port e a regra de sinal precisam ser revisados por um agente no laboratório completo antes de qualquer uso.
