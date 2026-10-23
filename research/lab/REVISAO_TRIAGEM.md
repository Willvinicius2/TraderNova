# Revisão das 17 regras da triagem que passaram em BTC, ETH e SOL (23/10/2026)

Três agentes revisaram o port em TypeScript contra o Pine ou a descrição pública, procuraram dado futuro e rodaram o
teste de vizinhos (±20% em cada parâmetro que muda o sinal; `triagem/vizinhos.py`). Notas completas em
`notes/triagem-revisao-{a,b,c}.md`. Nenhuma das 17 usa dado futuro (leitura do código e recálculo com candles cortados).
O Pine original só foi achado para dynamic-flow-ribbons; nas outras o `.ts` foi comparado com a descrição do autor.

| Regra | TF | Revisão | Vizinhos BTC / ETH / SOL | Observação |
|---|---|---|---|---|
| kalman-hull-kijun | D1 | Aprovada | 6/6 · 6/6 · 4/6 | Alerta de estado (preço acima/abaixo da base): reentra logo após um stop. 0,92 de posição em comum com sma-dma. |
| sma-dma-crossing-signal | D1 | Aprovada | 11/12 · 10/12 · 7/12 | O autor trata SELL como saída; a triagem usa como venda. |
| traders-reality-main | D1 | Aprovada | 4/4 · 3/4 · 3/4 | Vela de clímax (PVSRA); só o multiplicador 1,6 falha. |
| directional-indicator-crossovers-v1 | D1 | Aprovada | 2/2 · 2/2 · 2/2 | Representante da família DI+ x DI−. |
| trend-with-adx-ema-buy-sell-signals | D1 | Aprovada | 2/2 · 2/2 · 1/2 | Também é DI+ x DI− (estado); conta junto com a família DI. |
| macdas | D1 | Aprovada | 4/6 · 2/6 · 4/6 | MACD de Aspray; fraco no ETH. |
| philakone-ema-swing | H4 | Duvidosa | 3/8 · 7/8 · 3/8 | No BTC, mudar a EMA 21 ou 55 deixa a validação negativa. |
| adaptive-friction-filter | D1 | Duvidosa | 1/6 · 2/6 · 6/6 | No BTC quase só o padrão passa. |
| zero-lag-garch-bands-nal | D1 | Duvidosa | 5/8 · 5/8 · 7/8 | A regra genérica usa a banda superior; a regra do autor reprova. |
| adx-and-di | D1 | Duvidosa | 2/2 · 1/2 · 1/2 | Família DI. |
| adx-with-shaded-zone | D1 | Duvidosa | 1/2 · 2/2 · 1/2 | Família DI. |
| elder-force | D1 | Duvidosa | 2/2 · 1/2 · 1/2 | Com length=10, ETH e SOL falham. |
| bacap-price-structure-21-ema-trend | D1 | Duvidosa | 1/2 · 1/2 · 2/2 | A venda foi criada pela triagem; depende de uma operação no BTC. |
| dmi-delta-by-0xjcf | D1 | Duplicata | – | 292 de 293 sinais iguais a adx-and-di. |
| macd-with-crossings-and-above-below-zero | D1 | Duplicata | – | Dominada pelas setas DMI; igual a trend-with-adx. |
| emergent-rays-novathemachine | D1 | Duplicata | – | Mesma EMA21 do high de bacap. |
| dynamic-flow-ribbons | D1 | Reprovada | 1/6 · 6/6 · 2/6 | Regra testada não é a do autor; só o ETH aguenta os vizinhos. |

**Leitura honesta:** sobram 5 ideias distintas aprovadas (Kalman Hull Kijun, SMA/DMA, Traders Reality, família DI e
MACDAS), todas seguidoras de tendência em D1, e todas só em cripto (BTC, ETH e SOL andam juntos). As 17 seguem no
acompanhamento em papel (`PAPEL.md`), com a revisão ao lado; a decisão final usa só as aprovadas.

## Problemas da triagem achados na revisão (para a triagem-v2)
1. `sinais.mjs`: "crossover" está na lista de compra, então títulos como "Bearish DI Crossover" ficam neutros e o alerta do autor se perde.
2. `sinais.mjs`: marcadores de estado (setas em todo candle) entram junto com os de evento e dominam a regra.
3. `sinais.mjs`: a regra genérica usa o primeiro plot, que pode não ser o gatilho do autor (banda superior, EMA do high).
4. `vizinhos.py` (corrigido em 23/10): variantes que não mudam o sinal entravam na contagem; negativos viravam 1.
