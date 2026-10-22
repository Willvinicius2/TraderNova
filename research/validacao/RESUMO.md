# Resumo da validação das candidatas

Gerado por `resumo.py`. Walk-forward: calibra em 3 anos, opera o ano seguinte, rola. Variante *regime* = compra só acima da média de 200 dias e vende só abaixo.

| Estratégia | Lab (tf, lado) | Fixos: valid. / reserva | Fixos regime: valid. / reserva | Grade positiva na valid. | WF BTC orig | WF BTC regime | Outros ativos estáveis no WF | Veredito |
|---|---|---|---|---|---|---|---|---|
| BM01_media | H4 both | +2.8 / +36.4 | +1.8 / +11.8 | 8/72 | +159.2R PF 2.67 DD 7.7% (6/8 anos) | +66.3R PF 2.35 DD 6.6% (5/8 anos) | - | REFERÊNCIA |
| BM02_donchian | H4 both | -0.7 / +34.2 | +0.6 / +24.5 | 11/54 | +118.5R PF 1.91 DD 6.1% (7/8 anos) | +79.8R PF 1.93 DD 6.1% (6/8 anos) | - | REFERÊNCIA |
| L04_tsmom | D1 long | -3.6 / +41.8 | -1.4 / +29.3 | 46/180 | +294.6R PF 2.81 DD 17.5% (7/8 anos) | +160.4R PF 2.39 DD 12.3% (5/8 anos) | GBPUSD | DESCARTAR |
| L07_stochastic | D1 long | +2.1 / +5.2 | -0.6 / -0.7 | 41/108 | -4.8R PF 0.94 DD 8.4% (3/7 anos) | -4.7R PF 0.95 DD 8.0% (2/7 anos) | - | DESCARTAR |
| L12_keltner_breakout | H4 both | +8.4 / +45.4 | +12.8 / +37.2 | 78/144 | +100.7R PF 1.66 DD 9.6% (7/8 anos) | +114.5R PF 2.11 DD 7.4% (6/8 anos) | XAUUSD, AUDUSD | ≈ REFERÊNCIA (regime) |
| TV21_aroon | H4 both | +5.3 / +26.4 | +6.2 / +10.5 | 19/108 | +59.8R PF 1.40 DD 13.9% (6/8 anos) | +18.3R PF 1.17 DD 7.9% (4/8 anos) | EURUSD, AUDUSD | DESCARTAR |
| TV32_lorentzian | H4 long | +5.3 / +48.2 | +7.9 / +27.1 | 55/288 | +44.9R PF 1.44 DD 8.4% (4/8 anos) | +29.0R PF 1.19 DD 14.8% (5/8 anos) | XAUUSD | DESCARTAR |
| TV39_smoothed_ha | D1 both | +5.3 / +34.5 | +8.3 / +13.0 | 10/90 | +127.5R PF 2.38 DD 4.3% (6/8 anos) | +74.4R PF 1.94 DD 6.9% (7/8 anos) | EURUSD, USDJPY | APROVEITÁVEL (orig) |
| TV72_cusum | H4 long | +14.2 / +100.3 | +18.6 / +34.9 | 174/324 | +307.0R PF 2.47 DD 10.1% (6/8 anos) | +104.7R PF 1.70 DD 8.2% (6/8 anos) | XAUUSD | ≈ REFERÊNCIA (regime) |
| TV74_rvi | H4 long | +7.9 / +58.3 | +16.9 / +41.3 | 42/108 | +113.7R PF 1.72 DD 4.7% (7/8 anos) | +52.3R PF 1.45 DD 6.6% (6/8 anos) | - | APROVEITÁVEL (orig) |
| TV79_derivative_osc | H4 long | +8.4 / +42.2 | -9.9 / +14.0 | 66/216 | +55.7R PF 1.37 DD 4.5% (6/8 anos) | +9.9R PF 1.07 DD 8.6% (4/8 anos) | XAUUSD | ≈ REFERÊNCIA (orig) |
| TV81_tdi | H4 long | +4.0 / +21.2 | +3.0 / +0.9 | 30/144 | +52.9R PF 1.36 DD 6.7% (7/8 anos) | +24.6R PF 1.42 DD 4.4% (7/8 anos) | - | ≈ REFERÊNCIA (orig) |
| TV85_ai_trend_nav | H4 both | +8.6 / +39.2 | +9.7 / +4.7 | 48/108 | +171.0R PF 3.48 DD 4.7% (7/8 anos) | +79.7R PF 1.81 DD 7.2% (7/8 anos) | EURUSD | APROVEITÁVEL (orig) |

## BM01_media — Referência: preço acima/abaixo da média simples

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +30.0 | +30.0 | +2.1 | +6.0 |
| 2016 | 124.3 | +35.3 | +35.3 | -5.7 | +41.1 |
| 2017 | 1336.4 | +42.4 | +42.4 | -2.0 | +44.5 |
| 2018 | -73.4 | +21.9 | +21.9 | +26.0 | +22.5 |
| 2019 | 94.1 | +30.1 | +30.1 | +1.8 | +16.6 |
| 2020 | 304.9 | +43.0 | +43.0 | -4.5 | +34.0 |
| 2021 | 59.4 | -3.0 | -3.0 | -3.5 | -9.9 |
| 2022 | -64.2 | +5.8 | +5.8 | +11.7 | +11.7 |
| 2023 | 155.6 | +16.6 | +16.6 | -13.7 | -6.8 |
| 2024 | 121.0 | +19.9 | +19.9 | -4.3 | +20.2 |
| 2025 | -6.3 | -15.2 | -15.2 | -6.3 | -7.9 |
| 2026 | -4.6 | +15.2 | +15.2 | +4.6 | +6.3 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +159.2R PF 2.67 DD 7.7% (6/8 anos) | +187.7R / +117.0R | +66.3R PF 2.35 DD 6.6% (5/8 anos) | +212.1R em 992 operações |
| EJ_XAUUSD | +13.1R PF 1.32 DD 5.2% (4/6 anos) | -5.0R / -7.6R | -10.2R PF 0.68 DD 10.0% (1/3 anos) | +15.4R em 581 operações |
| EJ_EURUSD | +21.7R PF 1.28 DD 7.1% (2/4 anos) | -20.1R / -5.2R | -3.0R PF 0.97 DD 9.2% (2/4 anos) | -27.8R em 687 operações |
| EJ_GBPUSD | -26.8R PF 0.68 DD 15.1% (1/3 anos) | -15.7R / -22.4R | +0.3R PF 1.00 DD 7.2% (1/4 anos) | -11.0R em 633 operações |
| EJ_USDJPY | +30.2R PF 1.10 DD 15.7% (5/5 anos) | +46.7R / +28.9R | -7.1R PF 0.81 DD 5.5% (0/2 anos) | -8.9R em 643 operações |
| EJ_AUDUSD | -12.3R PF 0.77 DD 7.9% (0/2 anos) | -47.4R / +6.1R | -3.1R PF 0.90 DD 6.2% (1/3 anos) | -17.5R em 663 operações |
| EJ_USDCAD | +3.7R PF 1.21 DD 1.8% (2/2 anos) | -32.5R / -11.2R | -4.0R PF 0.85 DD 3.9% (0/2 anos) | +0.6R em 643 operações |

## BM02_donchian — Referência: rompimento de Donchian (tartarugas)

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +32.1 | +32.1 | +6.3 | +23.3 |
| 2016 | 124.3 | +28.9 | +28.9 | -1.8 | +30.7 |
| 2017 | 1336.4 | +42.0 | +42.0 | -6.4 | +48.4 |
| 2018 | -73.4 | +19.5 | +19.5 | +22.1 | +18.7 |
| 2019 | 94.1 | +15.3 | +15.3 | -4.4 | +9.2 |
| 2020 | 304.9 | +39.3 | +39.3 | -1.3 | +40.0 |
| 2021 | 59.4 | -0.5 | -0.5 | -0.3 | -6.8 |
| 2022 | -64.2 | -0.2 | -0.2 | +7.5 | +7.5 |
| 2023 | 155.6 | +24.3 | +24.3 | -2.5 | +5.5 |
| 2024 | 121.0 | +8.5 | +8.5 | -8.3 | +12.3 |
| 2025 | -6.3 | -10.9 | -10.9 | -11.6 | -3.3 |
| 2026 | -4.6 | +12.4 | +12.4 | +6.5 | +10.0 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +118.5R PF 1.91 DD 6.1% (7/8 anos) | +97.1R / +123.2R | +79.8R PF 1.93 DD 6.1% (6/8 anos) | +178.6R em 269 operações |
| EJ_XAUUSD | +0.5R PF 1.01 DD 9.2% (4/6 anos) | -4.5R / +10.0R | +7.8R PF 1.11 DD 15.1% (4/6 anos) | +13.0R em 172 operações |
| EJ_EURUSD | -22.7R PF 0.80 DD 16.1% (0/3 anos) | -19.3R / -8.9R | +10.6R PF 1.23 DD 4.0% (2/3 anos) | -12.2R em 174 operações |
| EJ_GBPUSD | -41.9R PF 0.73 DD 22.3% (0/4 anos) | -36.2R / -25.4R | -7.3R PF 0.92 DD 10.7% (2/5 anos) | -4.5R em 177 operações |
| EJ_USDJPY | +16.7R PF 1.10 DD 6.0% (2/5 anos) | +32.2R / +20.4R | -42.8R PF 0.53 DD 21.4% (0/4 anos) | -25.0R em 181 operações |
| EJ_AUDUSD | -11.1R PF 0.52 DD 7.3% (0/3 anos) | -19.3R / -1.3R | -0.2R PF 1.00 DD 8.8% (1/3 anos) | -33.0R em 186 operações |
| EJ_USDCAD | -13.6R PF 0.88 DD 15.1% (2/5 anos) | -11.6R / -1.2R | +13.9R PF 1.26 DD 6.5% (2/3 anos) | +8.9R em 167 operações |

## L04_tsmom — Momentum de série temporal (TSMOM)

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +5.9 | +2.4 | -3.5 | +4.7 |
| 2016 | 124.3 | +546.0 | +543.5 | -2.5 | +546.0 |
| 2017 | 1336.4 | +0.0 | +0.0 | +0.0 | +0.0 |
| 2018 | -73.4 | -3.3 | +10.7 | +14.0 | +12.3 |
| 2019 | 94.1 | +23.5 | +21.8 | -1.7 | +12.7 |
| 2020 | 304.9 | +68.2 | +64.0 | -4.2 | +65.1 |
| 2021 | 59.4 | +2.1 | +5.3 | +3.2 | -3.6 |
| 2022 | -64.2 | -5.7 | -3.5 | +2.2 | +2.2 |
| 2023 | 155.6 | +24.7 | +21.0 | -3.7 | +13.8 |
| 2024 | 121.0 | +11.6 | +7.7 | -4.0 | +8.8 |
| 2025 | -6.3 | +0.2 | +0.5 | +0.3 | -1.4 |
| 2026 | -4.6 | +5.3 | +9.1 | +3.7 | +8.2 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +294.6R PF 2.81 DD 17.5% (7/8 anos) | +127.5R / +255.4R | +160.4R PF 2.39 DD 12.3% (5/8 anos) | +672.6R em 95 operações |
| EJ_XAUUSD | -9.8R PF 0.85 DD 17.3% (3/5 anos) | -10.2R / +27.5R | -8.7R PF 0.77 DD 12.8% (2/3 anos) | +12.7R em 62 operações |
| EJ_EURUSD | -5.3R PF 0.77 DD 5.7% (1/3 anos) | -16.8R / -5.7R | +12.0R PF 1.56 DD 7.9% (2/3 anos) | -7.1R em 81 operações |
| EJ_GBPUSD | +22.9R PF 1.34 DD 4.2% (3/6 anos) | +20.9R / +24.2R | -0.9R PF 0.98 DD 10.9% (3/6 anos) | +6.2R em 55 operações |
| EJ_USDJPY | -22.0R PF 0.22 DD 12.3% (2/3 anos) | -42.2R / -43.8R | -45.8R PF - DD 22.9% (0/2 anos) | +26.3R em 66 operações |
| EJ_AUDUSD | -4.0R PF 0.74 DD 4.6% (1/2 anos) | -50.6R / -1.5R | -12.2R PF 0.75 DD 8.7% (1/3 anos) | -1.5R em 60 operações |
| EJ_USDCAD | -7.9R PF 0.65 DD 6.2% (0/2 anos) | -14.6R / -8.3R | +0.0R PF - DD 0.0% (0/0 anos) | +9.0R em 62 operações |

## L07_stochastic — Estocástico de Lane (cruzamento %K/%D nas zonas)

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +0.1 | -4.3 | -4.5 | -0.4 |
| 2016 | 124.3 | +1.9 | -9.3 | -11.2 | +1.9 |
| 2017 | 1336.4 | +2.6 | -8.8 | -11.4 | +2.6 |
| 2018 | -73.4 | -1.8 | +0.1 | +1.9 | -1.0 |
| 2019 | 94.1 | +1.2 | -5.0 | -6.3 | -0.7 |
| 2020 | 304.9 | +0.9 | -7.9 | -8.8 | -1.4 |
| 2021 | 59.4 | +1.9 | +1.5 | -0.4 | -0.7 |
| 2022 | -64.2 | +0.3 | +0.4 | +0.1 | +0.1 |
| 2023 | 155.6 | +4.6 | -0.5 | -5.0 | +1.2 |
| 2024 | 121.0 | -0.3 | -6.0 | -5.7 | -2.4 |
| 2025 | -6.3 | -0.0 | +1.6 | +1.6 | -0.1 |
| 2026 | -4.6 | +0.9 | +1.1 | +0.2 | +0.6 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | -4.8R PF 0.94 DD 8.4% (3/7 anos) | -26.4R / +4.0R | -4.7R PF 0.95 DD 8.0% (2/7 anos) | +12.2R em 94 operações |
| EJ_XAUUSD | +12.6R PF 1.22 DD 3.6% (4/6 anos) | +6.7R / +6.0R | -12.1R PF 0.60 DD 7.9% (1/3 anos) | +6.5R em 59 operações |
| EJ_EURUSD | -18.0R PF 0.68 DD 11.9% (3/5 anos) | -24.1R / +1.5R | +3.0R PF 1.05 DD 3.8% (4/5 anos) | +3.9R em 82 operações |
| EJ_GBPUSD | +6.1R PF 1.19 DD 2.7% (3/6 anos) | -5.0R / -4.2R | +16.4R PF 1.07 DD 8.9% (4/6 anos) | -1.4R em 72 operações |
| EJ_USDJPY | +1.0R PF 1.03 DD 3.7% (4/6 anos) | -5.3R / +8.8R | -8.2R PF 0.58 DD 5.5% (1/4 anos) | +2.7R em 66 operações |
| EJ_AUDUSD | -1.8R PF 0.98 DD 8.2% (2/6 anos) | -13.1R / +1.5R | +11.5R PF 1.05 DD 13.5% (4/6 anos) | +2.2R em 71 operações |
| EJ_USDCAD | +4.7R PF 1.05 DD 5.4% (3/5 anos) | -10.2R / +2.3R | +0.4R PF 1.01 DD 5.9% (3/4 anos) | +2.3R em 67 operações |

## L12_keltner_breakout — Rompimento do canal de Keltner

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +41.5 | +41.5 | +11.4 | +36.7 |
| 2016 | 124.3 | +76.3 | +76.3 | +0.3 | +76.0 |
| 2017 | 1336.4 | +38.0 | +38.0 | -15.0 | +53.0 |
| 2018 | -73.4 | +42.9 | +42.9 | +36.6 | +35.0 |
| 2019 | 94.1 | +39.9 | +39.9 | +0.7 | +16.6 |
| 2020 | 304.9 | +85.2 | +85.2 | +10.5 | +73.0 |
| 2021 | 59.4 | +1.5 | +1.5 | -9.9 | -0.8 |
| 2022 | -64.2 | +6.9 | +6.9 | +13.6 | +13.6 |
| 2023 | 155.6 | +60.0 | +60.0 | -5.5 | +24.6 |
| 2024 | 121.0 | -8.7 | -8.7 | -18.6 | +4.8 |
| 2025 | -6.3 | -15.7 | -15.7 | -14.2 | -3.8 |
| 2026 | -4.6 | +9.8 | +9.8 | +9.8 | +11.7 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +100.7R PF 1.66 DD 9.6% (7/8 anos) | +179.8R / +162.1R | +114.5R PF 2.11 DD 7.4% (6/8 anos) | +336.1R em 317 operações |
| EJ_XAUUSD | +15.2R PF 1.10 DD 10.9% (3/6 anos) | +25.6R / +32.0R | +19.7R PF 1.24 DD 9.0% (3/6 anos) | +29.6R em 201 operações |
| EJ_EURUSD | -7.2R PF 0.88 DD 9.8% (1/6 anos) | +11.1R / -12.2R | +21.0R PF 1.12 DD 15.6% (5/6 anos) | +27.4R em 193 operações |
| EJ_GBPUSD | -32.7R PF 0.77 DD 18.0% (1/5 anos) | -41.1R / +7.5R | +7.0R PF 1.05 DD 7.0% (4/6 anos) | -2.0R em 210 operações |
| EJ_USDJPY | -7.9R PF 0.91 DD 8.8% (2/4 anos) | -1.1R / +17.3R | +1.9R PF 1.01 DD 10.7% (3/5 anos) | -0.6R em 212 operações |
| EJ_AUDUSD | +36.8R PF 1.44 DD 7.2% (4/5 anos) | -24.9R / +25.8R | +7.0R PF 1.20 DD 5.8% (2/4 anos) | +3.6R em 183 operações |
| EJ_USDCAD | -11.0R PF 0.87 DD 15.5% (2/6 anos) | +15.5R / +5.5R | -7.2R PF 0.90 DD 9.4% (1/5 anos) | +23.4R em 204 operações |

## TV21_aroon — Aroon (Chande): cruzamento Up/Down

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +8.0 | +8.0 | +3.8 | +4.6 |
| 2016 | 124.3 | +26.6 | +26.6 | -5.0 | +31.6 |
| 2017 | 1336.4 | +29.4 | +29.4 | -5.2 | +34.6 |
| 2018 | -73.4 | +17.1 | +17.1 | +20.9 | +16.9 |
| 2019 | 94.1 | +12.3 | +12.3 | +0.5 | +3.4 |
| 2020 | 304.9 | +35.3 | +35.3 | -3.8 | +34.0 |
| 2021 | 59.4 | +4.3 | +4.3 | +0.9 | -0.7 |
| 2022 | -64.2 | +1.0 | +1.0 | +6.9 | +6.9 |
| 2023 | 155.6 | +28.1 | +28.1 | +0.0 | +8.4 |
| 2024 | 121.0 | -0.3 | -0.3 | -5.7 | +3.3 |
| 2025 | -6.3 | -6.5 | -6.5 | -4.5 | -4.7 |
| 2026 | -4.6 | +5.1 | +5.1 | +1.4 | +3.5 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +59.8R PF 1.40 DD 13.9% (6/8 anos) | +104.4R / +88.6R | +18.3R PF 1.17 DD 7.9% (4/8 anos) | +152.5R em 382 operações |
| EJ_XAUUSD | +12.7R PF 1.19 DD 6.5% (3/6 anos) | +0.1R / +19.1R | -8.5R PF 0.81 DD 9.6% (4/6 anos) | +40.5R em 210 operações |
| EJ_EURUSD | +4.2R PF 1.03 DD 15.8% (2/5 anos) | +28.8R / -14.7R | +42.6R PF 1.20 DD 10.6% (5/6 anos) | -22.9R em 231 operações |
| EJ_GBPUSD | -24.8R PF 0.81 DD 13.6% (2/6 anos) | -20.2R / -34.0R | +6.6R PF 1.07 DD 12.0% (3/4 anos) | +11.8R em 220 operações |
| EJ_USDJPY | -7.0R PF 0.95 DD 14.2% (2/4 anos) | -27.6R / -2.8R | -26.8R PF 0.83 DD 19.1% (1/4 anos) | -26.1R em 235 operações |
| EJ_AUDUSD | -4.0R PF 0.91 DD 7.7% (3/5 anos) | -11.7R / -11.7R | +16.8R PF 1.49 DD 3.9% (4/5 anos) | -5.2R em 213 operações |
| EJ_USDCAD | +2.9R PF 1.02 DD 15.9% (1/4 anos) | +6.8R / +7.2R | +0.1R PF 1.00 DD 5.1% (1/2 anos) | -8.6R em 228 operações |

## TV32_lorentzian — Machine Learning: Lorentzian Classification (jdehorty), kNN causal

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +13.1 | +14.8 | +1.6 | +6.9 |
| 2016 | 124.3 | +50.5 | +50.3 | -0.1 | +50.5 |
| 2017 | 1336.4 | +16.0 | +6.7 | -9.3 | +16.0 |
| 2018 | -73.4 | +4.5 | +23.6 | +19.2 | +15.2 |
| 2019 | 94.1 | +34.0 | +34.2 | +0.3 | +15.9 |
| 2020 | 304.9 | +9.4 | +10.1 | +0.6 | +7.1 |
| 2021 | 59.4 | +5.6 | +1.3 | -4.3 | -1.0 |
| 2022 | -64.2 | -0.3 | +8.6 | +8.9 | +8.9 |
| 2023 | 155.6 | +37.5 | +31.2 | -6.2 | +15.1 |
| 2024 | 121.0 | +15.8 | +19.4 | +3.6 | +15.6 |
| 2025 | -6.3 | -3.0 | -12.0 | -9.0 | -9.6 |
| 2026 | -4.6 | -2.0 | -2.0 | -0.0 | +6.0 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +44.9R PF 1.44 DD 8.4% (4/8 anos) | +40.6R / +95.5R | +29.0R PF 1.19 DD 14.8% (5/8 anos) | +167.8R em 201 operações |
| EJ_XAUUSD | +29.1R PF 1.88 DD 4.5% (3/6 anos) | +11.8R / +10.5R | +2.9R PF 1.13 DD 4.3% (2/4 anos) | +3.5R em 128 operações |
| EJ_EURUSD | -16.5R PF 0.75 DD 11.8% (1/2 anos) | -6.9R / -12.1R | +2.6R PF 1.06 DD 3.3% (2/4 anos) | -12.0R em 136 operações |
| EJ_GBPUSD | -17.5R PF 0.74 DD 8.8% (0/6 anos) | -17.0R / -18.2R | -12.8R PF 0.74 DD 10.3% (1/6 anos) | -23.2R em 149 operações |
| EJ_USDJPY | -6.0R PF 0.84 DD 6.0% (2/4 anos) | -0.0R / -0.1R | -21.6R PF 0.51 DD 13.4% (1/4 anos) | +18.5R em 126 operações |
| EJ_AUDUSD | -6.0R PF 0.93 DD 8.2% (2/4 anos) | -11.2R / -5.9R | +6.5R PF 1.15 DD 3.3% (2/3 anos) | -24.1R em 139 operações |
| EJ_USDCAD | -1.9R PF 0.96 DD 7.0% (2/5 anos) | -24.1R / +4.6R | +15.5R PF 1.46 DD 4.3% (4/6 anos) | +7.8R em 139 operações |

## TV39_smoothed_ha — Trend Indicator A-V2: cor da Heikin Ashi suavizada por EMA

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +16.6 | +16.6 | +1.8 | +1.4 |
| 2016 | 124.3 | +27.6 | +27.6 | -2.4 | +30.0 |
| 2017 | 1336.4 | +22.7 | +22.7 | -4.0 | +26.7 |
| 2018 | -73.4 | +12.5 | +12.5 | +17.1 | +13.7 |
| 2019 | 94.1 | +24.7 | +24.7 | +2.5 | +4.0 |
| 2020 | 304.9 | +54.3 | +54.3 | -2.1 | +47.6 |
| 2021 | 59.4 | +8.0 | +8.0 | +1.6 | +4.1 |
| 2022 | -64.2 | -2.7 | -2.7 | +4.2 | +4.2 |
| 2023 | 155.6 | +18.4 | +18.4 | -3.1 | +9.9 |
| 2024 | 121.0 | +11.9 | +11.9 | -3.8 | +2.9 |
| 2025 | -6.3 | -4.7 | -4.7 | -2.4 | -5.7 |
| 2026 | -4.6 | +8.9 | +8.9 | +3.9 | +5.9 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +127.5R PF 2.38 DD 4.3% (6/8 anos) | +134.7R / +155.3R | +74.4R PF 1.94 DD 6.9% (7/8 anos) | +181.6R em 240 operações |
| EJ_XAUUSD | +8.0R PF 1.13 DD 7.3% (4/6 anos) | +6.0R / +6.0R | -16.8R PF 0.62 DD 10.5% (1/4 anos) | +18.6R em 141 operações |
| EJ_EURUSD | +15.6R PF 1.11 DD 12.4% (3/5 anos) | -27.1R / +7.3R | +27.3R PF 1.27 DD 4.4% (5/6 anos) | -3.5R em 157 operações |
| EJ_GBPUSD | -3.2R PF 0.99 DD 17.6% (2/6 anos) | +13.6R / +34.8R | -3.7R PF 0.97 DD 15.5% (2/5 anos) | -4.6R em 149 operações |
| EJ_USDJPY | +23.2R PF 1.10 DD 12.3% (4/5 anos) | +21.6R / +26.2R | -24.9R PF 0.81 DD 13.9% (1/3 anos) | -28.1R em 164 operações |
| EJ_AUDUSD | -23.1R PF 0.60 DD 12.9% (0/3 anos) | -40.1R / -12.0R | -1.4R PF 0.97 DD 6.3% (0/2 anos) | -15.6R em 141 operações |
| EJ_USDCAD | -18.9R PF 0.78 DD 13.1% (2/4 anos) | -41.8R / +1.0R | -3.9R PF 0.92 DD 5.7% (0/2 anos) | +6.1R em 141 operações |

## TV72_cusum — Change-Point Detection (CUSUM) LuxAlgo: opera a mudança de regime

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +22.6 | +31.2 | +8.6 | +12.2 |
| 2016 | 124.3 | +55.7 | +52.5 | -3.2 | +55.7 |
| 2017 | 1336.4 | +24.8 | +24.4 | -0.4 | +24.8 |
| 2018 | -73.4 | +6.3 | +31.4 | +25.1 | +17.7 |
| 2019 | 94.1 | +30.5 | +24.3 | -6.2 | +0.6 |
| 2020 | 304.9 | +38.9 | +35.2 | -3.7 | +37.6 |
| 2021 | 59.4 | +20.7 | +34.9 | +14.2 | +10.5 |
| 2022 | -64.2 | -6.5 | -1.4 | +5.1 | +8.1 |
| 2023 | 155.6 | +58.4 | +52.5 | -5.9 | +16.5 |
| 2024 | 121.0 | +28.9 | +21.3 | -7.5 | +19.3 |
| 2025 | -6.3 | -2.4 | -4.1 | -1.7 | -4.5 |
| 2026 | -4.6 | +15.4 | +19.0 | +3.5 | +3.6 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +307.0R PF 2.47 DD 10.1% (6/8 anos) | +221.8R / +126.0R | +104.7R PF 1.70 DD 8.2% (6/8 anos) | +270.6R em 158 operações |
| EJ_XAUUSD | +31.5R PF 1.53 DD 6.1% (4/6 anos) | +25.1R / +22.5R | +5.0R PF 1.07 DD 11.9% (2/6 anos) | +48.5R em 100 operações |
| EJ_EURUSD | -9.5R PF 0.94 DD 13.2% (3/6 anos) | -1.6R / +4.5R | +15.5R PF 1.12 DD 6.0% (3/5 anos) | -28.7R em 105 operações |
| EJ_GBPUSD | -7.2R PF 0.95 DD 11.5% (2/6 anos) | -7.5R / -16.2R | -8.6R PF 0.92 DD 10.2% (3/6 anos) | +13.1R em 92 operações |
| EJ_USDJPY | -8.6R PF 0.90 DD 13.8% (4/6 anos) | -31.1R / -29.8R | -15.7R PF 0.70 DD 8.5% (0/4 anos) | +11.4R em 88 operações |
| EJ_AUDUSD | +36.6R PF 1.18 DD 7.8% (4/6 anos) | -1.7R / +33.6R | +6.2R PF 1.06 DD 5.9% (3/6 anos) | -2.9R em 85 operações |
| EJ_USDCAD | -23.7R PF 0.64 DD 14.7% (1/6 anos) | -15.0R / -8.3R | -9.1R PF 0.88 DD 10.5% (0/2 anos) | +6.0R em 101 operações |

## TV74_rvi — Relative Volatility Index refinado (Dorsey): cruzamento do nível com filtro de tendência

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +27.3 | +38.4 | +11.0 | +20.9 |
| 2016 | 124.3 | +47.6 | +51.1 | +3.5 | +47.6 |
| 2017 | 1336.4 | +52.4 | +41.5 | -10.9 | +52.4 |
| 2018 | -73.4 | +2.9 | +29.4 | +26.5 | +17.7 |
| 2019 | 94.1 | +21.2 | +26.8 | +5.6 | +16.6 |
| 2020 | 304.9 | +31.5 | +35.9 | +4.4 | +16.5 |
| 2021 | 59.4 | +12.8 | +11.6 | -1.2 | +3.0 |
| 2022 | -64.2 | -5.0 | +9.0 | +13.9 | +13.9 |
| 2023 | 155.6 | +43.4 | +48.1 | +4.7 | +15.2 |
| 2024 | 121.0 | +23.0 | +15.9 | -7.1 | +21.9 |
| 2025 | -6.3 | -2.6 | -4.5 | -1.8 | -3.6 |
| 2026 | -4.6 | -5.5 | -4.3 | +1.3 | +7.9 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +113.7R PF 1.72 DD 4.7% (7/8 anos) | +109.9R / +118.5R | +52.3R PF 1.45 DD 6.6% (6/8 anos) | +221.7R em 776 operações |
| EJ_XAUUSD | +1.1R PF 1.01 DD 6.2% (4/6 anos) | -35.7R / +26.5R | -14.6R PF 0.88 DD 15.7% (1/3 anos) | +36.1R em 412 operações |
| EJ_EURUSD | -10.8R PF 0.87 DD 13.7% (2/4 anos) | -14.1R / -37.0R | +24.2R PF 1.60 DD 2.6% (4/4 anos) | -11.0R em 400 operações |
| EJ_GBPUSD | -10.7R PF 0.83 DD 13.3% (3/4 anos) | -16.6R / -13.4R | -4.7R PF 0.95 DD 10.4% (3/5 anos) | -6.5R em 401 operações |
| EJ_USDJPY | -14.4R PF 0.81 DD 9.0% (2/4 anos) | -15.6R / -3.2R | -8.6R PF 0.58 DD 5.3% (0/1 anos) | +16.7R em 444 operações |
| EJ_AUDUSD | +4.4R PF 1.24 DD 1.6% (2/3 anos) | -9.8R / +0.7R | +2.8R PF 1.27 DD 1.6% (1/3 anos) | -8.5R em 405 operações |
| EJ_USDCAD | -1.3R PF 0.45 DD 1.0% (0/2 anos) | -36.9R / -14.4R | -10.0R PF 0.63 DD 5.0% (0/2 anos) | -14.7R em 420 operações |

## TV79_derivative_osc — Derivative Oscillator (Constance Brown/everget): RSI suavizado menos sua SMA9, cruzamento do zero

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +19.4 | +35.9 | +16.4 | +31.9 |
| 2016 | 124.3 | +20.4 | +16.1 | -4.3 | +20.4 |
| 2017 | 1336.4 | +47.5 | +51.1 | +3.6 | +47.5 |
| 2018 | -73.4 | -0.4 | +5.8 | +6.2 | +4.6 |
| 2019 | 94.1 | +19.8 | +19.2 | -0.6 | +2.7 |
| 2020 | 304.9 | +27.9 | +16.4 | -11.6 | +14.5 |
| 2021 | 59.4 | +7.2 | +6.6 | -0.6 | +6.4 |
| 2022 | -64.2 | +1.3 | -15.0 | -16.3 | -16.3 |
| 2023 | 155.6 | +23.3 | +22.5 | -0.8 | +8.1 |
| 2024 | 121.0 | +16.2 | +15.8 | -0.4 | +9.3 |
| 2025 | -6.3 | +3.1 | -6.4 | -9.5 | -7.8 |
| 2026 | -4.6 | -0.4 | +4.6 | +5.1 | +4.5 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +55.7R PF 1.37 DD 4.5% (6/8 anos) | +27.0R / +73.7R | +9.9R PF 1.07 DD 8.6% (4/8 anos) | +165.9R em 609 operações |
| EJ_XAUUSD | +24.4R PF 1.22 DD 9.4% (5/6 anos) | +29.8R / +23.6R | +9.8R PF 1.06 DD 9.1% (3/6 anos) | +23.4R em 298 operações |
| EJ_EURUSD | +2.4R PF 1.03 DD 8.3% (2/5 anos) | -0.8R / +8.6R | +13.5R PF 1.17 DD 6.8% (3/6 anos) | +21.3R em 245 operações |
| EJ_GBPUSD | -0.6R PF 0.99 DD 6.7% (3/6 anos) | -4.4R / +6.0R | +6.0R PF 1.18 DD 4.0% (3/6 anos) | -3.3R em 281 operações |
| EJ_USDJPY | -4.9R PF 0.97 DD 9.9% (2/4 anos) | -32.8R / -7.7R | -21.2R PF 0.63 DD 11.2% (0/2 anos) | +23.5R em 289 operações |
| EJ_AUDUSD | -0.2R PF 0.99 DD 7.3% (2/5 anos) | -5.5R / -6.6R | -25.1R PF 0.86 DD 19.6% (4/6 anos) | -15.9R em 273 operações |
| EJ_USDCAD | +11.0R PF 1.08 DD 6.6% (3/6 anos) | -10.6R / +3.4R | +5.8R PF 1.08 DD 6.2% (2/4 anos) | +1.9R em 338 operações |

## TV81_tdi — Traders Dynamic Index (Dean Malone)

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +16.5 | +21.6 | +4.5 | +16.4 |
| 2016 | 124.3 | +13.5 | +9.2 | -4.5 | +13.5 |
| 2017 | 1336.4 | +34.6 | +32.9 | -1.6 | +34.6 |
| 2018 | -73.4 | +1.3 | +10.9 | +9.6 | +8.4 |
| 2019 | 94.1 | +8.5 | +10.9 | +3.5 | +3.5 |
| 2020 | 304.9 | +17.9 | +9.2 | -2.5 | +11.5 |
| 2021 | 59.4 | +5.8 | -1.6 | -7.5 | -1.1 |
| 2022 | -64.2 | -1.8 | +2.0 | +4.1 | +4.1 |
| 2023 | 155.6 | +19.3 | +9.7 | -9.3 | -1.0 |
| 2024 | 121.0 | +3.0 | -1.3 | -3.6 | +1.4 |
| 2025 | -6.3 | -0.3 | -9.3 | -9.0 | -11.0 |
| 2026 | -4.6 | -0.8 | +7.1 | +7.9 | +11.6 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +52.9R PF 1.36 DD 6.7% (7/8 anos) | +37.5R / +48.0R | +24.6R PF 1.42 DD 4.4% (7/8 anos) | +101.0R em 488 operações |
| EJ_XAUUSD | +11.1R PF 1.18 DD 10.6% (5/6 anos) | +0.9R / +10.2R | +8.6R PF 1.17 DD 4.8% (4/6 anos) | +31.3R em 276 operações |
| EJ_EURUSD | -19.6R PF 0.66 DD 12.7% (2/5 anos) | -22.3R / -15.2R | +5.3R PF 1.08 DD 4.0% (3/6 anos) | -18.2R em 220 operações |
| EJ_GBPUSD | -2.0R PF 0.97 DD 4.9% (3/6 anos) | -23.5R / -4.8R | -0.8R PF 0.99 DD 6.6% (3/6 anos) | -18.4R em 245 operações |
| EJ_USDJPY | -0.1R PF 1.00 DD 9.1% (2/5 anos) | -0.1R / -7.6R | -19.9R PF 0.80 DD 12.2% (0/3 anos) | +16.9R em 247 operações |
| EJ_AUDUSD | -9.2R PF 0.64 DD 5.5% (2/6 anos) | -23.4R / -18.2R | +13.2R PF 1.27 DD 3.5% (3/6 anos) | -23.0R em 245 operações |
| EJ_USDCAD | -12.5R PF 0.54 DD 6.3% (0/3 anos) | -13.4R / -6.5R | -1.3R PF 0.87 DD 3.3% (1/3 anos) | +0.6R em 284 operações |

## TV85_ai_trend_nav — AI Trend Navigator [K-Neighbor] (Zeiierman)

| Ano | B&H BTC % | orig R | both R | short R | regime R |
|---|---|---|---|---|---|
| 2015 | 34.2 | +18.1 | +18.1 | +0.0 | +1.8 |
| 2016 | 124.3 | +20.9 | +20.9 | -2.9 | +23.9 |
| 2017 | 1336.4 | +56.4 | +56.4 | -4.7 | +61.1 |
| 2018 | -73.4 | +12.8 | +12.8 | +19.1 | +15.8 |
| 2019 | 94.1 | +48.3 | +48.3 | +2.6 | -0.4 |
| 2020 | 304.9 | +61.6 | +61.6 | -1.5 | +54.0 |
| 2021 | 59.4 | +12.0 | +12.0 | +2.4 | +6.0 |
| 2022 | -64.2 | -3.4 | -3.4 | +3.7 | +3.7 |
| 2023 | 155.6 | +28.1 | +28.1 | -2.4 | +8.8 |
| 2024 | 121.0 | +2.5 | +2.5 | -4.2 | -5.3 |
| 2025 | -6.3 | -0.8 | -0.8 | +0.4 | -6.2 |
| 2026 | -4.6 | +9.4 | +9.4 | +6.6 | +7.4 |

| Ativo | WF orig (3 anos) | WF orig 2 / 4 anos | WF regime | Fixos do BTC (orig), período todo |
|---|---|---|---|---|
| BTCUSD | +171.0R PF 3.48 DD 4.7% (7/8 anos) | +177.6R / +179.9R | +79.7R PF 1.81 DD 7.2% (7/8 anos) | +247.9R em 167 operações |
| EJ_XAUUSD | -2.6R PF 0.97 DD 13.5% (4/6 anos) | -1.2R / +0.1R | -16.3R PF 0.49 DD 10.0% (0/1 anos) | -2.4R em 125 operações |
| EJ_EURUSD | +16.2R PF 1.13 DD 7.4% (3/5 anos) | -22.2R / -6.0R | +23.6R PF 1.26 DD 6.0% (4/6 anos) | -30.1R em 125 operações |
| EJ_GBPUSD | +10.4R PF 1.04 DD 21.6% (2/6 anos) | -40.1R / +37.5R | -18.9R PF 0.88 DD 17.6% (2/5 anos) | -5.9R em 127 operações |
| EJ_USDJPY | -13.2R PF 0.93 DD 13.3% (2/4 anos) | -6.6R / -18.8R | -33.4R PF 0.46 DD 16.8% (0/2 anos) | -22.0R em 144 operações |
| EJ_AUDUSD | -13.0R PF 0.66 DD 9.6% (1/2 anos) | -57.6R / +8.6R | +5.3R PF 1.10 DD 6.6% (1/3 anos) | +8.2R em 115 operações |
| EJ_USDCAD | +2.2R PF 1.08 DD 3.6% (1/2 anos) | -33.1R / -27.9R | -14.6R PF 0.81 DD 12.2% (0/2 anos) | +9.0R em 103 operações |

