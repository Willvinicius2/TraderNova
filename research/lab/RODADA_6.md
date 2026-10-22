# Rodada 6 (22/10/2026): blocos 9 a 12 da fila do TradingView

Foram 16 scripts do TradingView (TV68–TV83), divididos entre 4 agentes, todos no BTCUSD com o protocolo lab-v3.

## Resultado

**4 CANDIDATAS fracas e 12 reprovadas na validação.** Nenhuma das candidatas passou no EURUSD nem no USDJPY com os mesmos parâmetros (`results/_cross_EURUSD.json`, `results/_cross_USDJPY.json`).

| Candidata | Escolha | Validação | Reserva | Placebo (mediana dev / val / reserva) | Leitura |
|---|---|---|---|---|---|
| TV72 CUSUM (LuxAlgo) | H4, só compra | 27 op · +13,1R · PF 1,79; sem a maior +1,4R | 61 op · +100,3R · PF 3,36 | +114,8R / +1,1R / +44,8R | A validação depende de uma operação. A maior parte do lucro vem do viés de alta e da saída. |
| TV74 Relative Volatility Index | H4, só compra | 140 op · +7,9R · PF 1,17 (no limite) | 282 op · +58,3R · PF 1,53; DD no stress 14,4% | +89,9R / −14,8R / +38,7R | Passa raspando. O stress fica perto de zero na validação. |
| TV79 Derivative Oscillator | H4, só compra acima da EMA200 | 78 op · +8,4R · PF 1,34 | 217 op · +41,9R · PF 1,48 | +48R / −5,9R / +1,5R | É a melhor do lote contra o placebo na validação e na reserva, mas a validação é fraca (t ≈ 1). |
| TV81 Traders Dynamic Index | H4, só compra | 69 op · +4,0R · PF 1,22 | 179 op · +21,2R · PF 1,39 | +60,0R / −4,6R / +24,4R | Entradas ao acaso ganham quase o mesmo. A vantagem não é da regra. |

As 12 reprovadas:

- **Bloco 9 (Breakout Finder, Trendlines with Breaks, Darvas, Range Detector):** a vantagem forte no desenvolvimento virou prejuízo em 2021–22. Três delas eram só compra.
- **Bloco 11 (VZO, PZO, Stochastic POP):** caíram na validação.
- **Bloco 12 (SSL Hybrid, ASI, Trendilo):** caíram na validação, e o Trendilo passou do limite de 10% de queda.
- **Bloco 10 (RWI, PFE):** também caíram na validação.

## Observações dos agentes

- Mesmo com "both" na grade e com a regra de 4 em 5 anos, a maioria das combinações escolhidas foi "só compra". A alta do BTC continua dominando a seleção.
- O calibrate.py aplica o limite de 10% de queda só no custo base. No stress, ele exige apenas netR > 0. A TV74 passou na reserva com queda de 14,4% no stress. Isso segue o texto do protocolo, mas é uma regra a endurecer numa versão futura, antes de uma rodada nova.
- O DSR penaliza combinações com mais operações, porque o Sharpe é medido por operação. Por isso o TV68 saiu com DSR 0,0 mesmo com t = 3,4.

## Placar acumulado

- Estratégias testadas no laboratório: 103.
- Candidatas: 10 no BTC (L04, L07, L12, TV21, TV32, TV39, TV72, TV74, TV79, TV81).
- Aprovadas: 0. Nenhuma candidata passou num segundo ativo.
