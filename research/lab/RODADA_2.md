# Rodada 2 (21/10/2026): estratégias do TradingView

23 estratégias do TradingView em 6 agentes, no BTCUSD, com o protocolo lab-v2. O lab-v2 exige ainda que cada fase continue positiva sem a maior operação e que a queda máxima fique em até 10% da conta, com 0,5% de risco por operação.

- **11 embutidas novas:** BarUpDn, Consecutive Up/Down, Greedy, Volty Expan Close, InSide Bar, OutSide Bar, Pivot Extension, Pivot Reversal, MACD, Parabolic SAR e Technical Ratings.
- **12 populares da comunidade:** Elder Impulse, Chaikin Oscillator, Range Filter, SSL Channel, WaveTrend, QQE, Schaff Trend Cycle, Fisher Transform, Hull Suite, Aroon, Vortex e CCI.
- **10 embutidas ficaram de fora porque já tinham sido testadas** (não repetir): Bollinger Bands (as duas versões), Channel BreakOut e Price Channel (Donchian), Keltner Channels, MovingAvg Cross e MovingAvg2Line Cross, RSI, Stochastic Slow, Supertrend e Momentum.

## Resultado

**1 CANDIDATA e 22 reprovadas, todas na validação de 2021–2022.**

**TV21 Aroon (H4, compra e venda, n=50, nível 70)** foi a única que passou nas três fases, inclusive sem a maior operação e dentro do limite de queda. Ela não está aprovada para sinal:

| Fase | Operações | Resultado | PF | Queda máxima |
|---|---|---|---|---|
| Desenvolvimento | 176 | +114,6R | 2,73 | 2,5% |
| Validação | 64 | +6,1R | 1,23 | 4,2% |
| Reserva | 142 | +26,9R | 1,40 | 7,8% |

O PF caiu bastante depois do desenvolvimento, e a vantagem que sobrou é pequena.

**As 22 reprovadas tiveram o mesmo padrão da rodada 1.** A combinação escolhida era "só compra", ganhou na alta do BTC de 2016–2020 e perdeu em 2021–2022.

**OutSide Bar foi a que chegou mais perto entre as reprovadas.** Ficou positiva na validação (+25R, PF 1,16), mas a queda de 14,7% passou do limite.

## Ressalvas

- **Fontes:** a rede do ambiente não abre tradingview.com. As regras vieram dos resumos de busca, da OANDA lab-education, de cópias do Pine em outros sites e do código Pine conhecido. Cada arquivo diz de onde tirou a regra.
- **Stop:** nenhum script original tinha stop, então todos usam k×ATR como proteção.
- **Ordens stop do Pine:** foram aproximadas pelo fechamento além do nível, com entrada na abertura seguinte.

## Placar acumulado

- **43 estratégias testadas no laboratório** (20 na rodada 1 e 23 na rodada 2), além das 9 das pesquisas anteriores.
- **4 candidatas:** L07 Estocástico, L12 Keltner, L04 Momentum e TV21 Aroon.
- **0 aprovadas para sinal real.**

## Próximo passo sugerido

As 4 candidatas precisam de acompanhamento em tempo real e de teste em outro ativo (ETH, ouro, EURUSD) antes de qualquer sinal. Só entre essas quatro, TV21 e L07 passariam no lab-v2.
