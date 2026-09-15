# Calibração H1 v2

Exploratory recalibration using history already examined in prior work. Later windows are excluded from parameter ranking but are not virgin out-of-sample evidence. No strategy is approved automatically. No second search after these results.

27 variantes, três ativos; ranking apenas em 2024-09 a 2025-08, score mediana de retorno menos 0,25 do pior DD nas seis células. Validação e final excluídos do ranking. Custos/risco/critérios de aprovação mantidos.

| Regra | Ativo | Preset | Validação original → calibrada | Final original → calibrada | Trades finais | PF final | DD final | Stress final | Adotada para pesquisa |
|---|---|---|---|---|---|---|---|---|---|
| T1 | BTCUSDT | T1-E0X2 | -8.68% → -4.92% | -11.45% → 1.91% | 51 | 1.16 | 4.51% | -0.17% | Não |
| T1 | ETHUSDT | T1-E0X2 | -10.45% → -10.51% | -7.02% → 3.19% | 56 | 1.23 | 5.11% | 0.96% | Não |
| T1 | SOLUSDT | T1-E0X2 | -0.94% → -3.81% | -7.31% → 0.94% | 55 | 1.07 | 3.89% | -0.70% | Não |
| T2 | BTCUSDT | T2-E0X2 | -8.62% → -1.55% | -17.41% → -5.58% | 46 | 0.62 | 8.24% | -6.74% | Sim |
| T2 | ETHUSDT | T2-E0X2 | -5.67% → -1.64% | -11.80% → -6.15% | 39 | 0.54 | 8.41% | -6.89% | Sim |
| T2 | SOLUSDT | T2-E0X2 | -7.09% → -1.47% | -3.01% → -0.25% | 42 | 0.98 | 4.69% | -1.38% | Sim |
| T3 | BTCUSDT | T3-E1X2 | -10.53% → 0.51% | -7.69% → 0.34% | 32 | 1.04 | 4.02% | -0.92% | Sim |
| T3 | ETHUSDT | T3-E1X2 | -6.86% → 1.29% | -6.79% → 3.19% | 36 | 1.30 | 2.99% | 1.68% | Sim |
| T3 | SOLUSDT | T3-E1X2 | -6.75% → -0.74% | -0.40% → 1.18% | 31 | 1.13 | 3.82% | 0.22% | Sim |

Nenhuma aprovação automática. Arquivos completos exportáveis em public/research/calibrated-*.json; grade e protocolo públicos em calibration.json.
