# Estudo histórico tradernova-spot-v1

Gerado: 2026-09-15T22:34:49.032Z. Triagem retrospectiva, não aprovação operacional. O período final já foi mencionado em chats anteriores; não é uma amostra intocada. Nenhuma seleção ou otimização após os resultados. Exige forward test prospectivo e dados/custos do contrato de execução.

Capital reiniciado por janela: 10.000 USDT; risco planejado até 0,5%; somente compras; sem alavancagem. Taxa 0,10% por lado e slippage 0,02% por lado. Stress: 0,15% e 0,05%. Parâmetros fixos; 18 combinações; sem otimização.

Desenvolvimento: 2024-09-01 a 2025-09-01 exclusivo; validação: 2025-09-01 a 2026-03-01 exclusivo; final: 2026-03-01 a 2026-09-01 exclusivo.

DD abaixo é marcado no fechamento dos candles, incluindo custo estimado de liquidação; não mede o pior movimento intrabar nem as regras de perda diária da mesa.

| Regra | Contrato | Período | Validação | Final | Trades final | PF final | DD final | Stress final | Triagem |
|---|---|---|---|---|---|---|---|---|---|
| T1 | BTCUSDT | M15 | -51.88% | -54.58% | 403 | 0.27 | 54.69% | -65.76% | rejected |
| T2 | BTCUSDT | M15 | -56.62% | -58.07% | 447 | 0.31 | 58.14% | -69.39% | rejected |
| T3 | BTCUSDT | M15 | -45.45% | -52.30% | 412 | 0.37 | 53.08% | -62.77% | rejected |
| T1 | BTCUSDT | H1 | -8.68% | -11.45% | 96 | 0.47 | 11.96% | -15.48% | rejected |
| T2 | BTCUSDT | H1 | -8.62% | -17.41% | 127 | 0.48 | 17.90% | -22.14% | rejected |
| T3 | BTCUSDT | H1 | -10.53% | -7.69% | 101 | 0.69 | 12.06% | -11.67% | rejected |
| T1 | ETHUSDT | M15 | -48.73% | -42.69% | 388 | 0.40 | 43.02% | -55.62% | rejected |
| T2 | ETHUSDT | M15 | -47.26% | -55.50% | 460 | 0.37 | 55.82% | -66.51% | rejected |
| T3 | ETHUSDT | M15 | -40.43% | -41.23% | 385 | 0.49 | 42.31% | -52.44% | rejected |
| T1 | ETHUSDT | H1 | -10.45% | -7.02% | 96 | 0.68 | 11.11% | -11.28% | rejected |
| T2 | ETHUSDT | H1 | -5.67% | -11.80% | 106 | 0.57 | 12.43% | -15.77% | rejected |
| T3 | ETHUSDT | H1 | -6.86% | -6.79% | 97 | 0.73 | 10.20% | -10.19% | rejected |
| T1 | SOLUSDT | M15 | -38.84% | -39.73% | 392 | 0.49 | 41.08% | -52.55% | rejected |
| T2 | SOLUSDT | M15 | -43.28% | -49.94% | 452 | 0.45 | 50.08% | -61.28% | rejected |
| T3 | SOLUSDT | M15 | -35.50% | -36.69% | 383 | 0.55 | 39.58% | -48.04% | rejected |
| T1 | SOLUSDT | H1 | -0.94% | -7.31% | 86 | 0.59 | 9.73% | -10.36% | rejected |
| T2 | SOLUSDT | H1 | -7.09% | -3.01% | 103 | 0.88 | 5.86% | -7.46% | rejected |
| T3 | SOLUSDT | H1 | -6.75% | -0.40% | 94 | 0.98 | 5.84% | -3.93% | rejected |

Arquivos completos em public/research; amostras brutas em research/cache (não versionadas); arquivos de origem e SHA-256 em public/research/manifest.json. USDT spot Binance não equivale ao contrato da The5ers ou ao monitor Kraken USD. Resultados não incluem financiamento, restrições de lote/mínimo ou conversão cambial.
