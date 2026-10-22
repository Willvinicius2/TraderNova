# Fila de pesquisa contínua

Cada rodada pega os próximos itens **não marcados** (cerca de 16 estratégias, 4 agentes) e um agente de dados.
Antes de testar, confira `registry.json`: a mesma regra central com outros parâmetros, ativo ou tempo gráfico **não** é estratégia nova. Marque `[x]` quando o item for testado.

## Meta ("resultado bom")
Uma estratégia só sai do laboratório quando:
1. passa no lab-v2 no BTCUSD;
2. passa com os **mesmos parâmetros** em pelo menos um segundo ativo (ETH, ouro, EURUSD ou NAS100);
3. fica 30 dias em acompanhamento simulado em tempo real sem quebrar o limite de queda.
Quando 1 e 2 acontecerem, avisar o Will na hora.

**Situação em 22/10/2026:** a triagem em massa (`TRIAGEM.md`) achou 51 regras que passam no BTC e no ETH ou SOL com os mesmos parâmetros, 17 em ambos; nenhuma passa em câmbio. Will avisado. Itens 1 e 2 estão pendentes da revisão do código (agentes `triagem-revisao-*`) e o item 3 ainda não começou. **Não abrir rodadas novas até o Will responder.**

## Dados (agente de dados, toda rodada até resolver)
- [ ] ETHUSD horário/minuto em repositório público do GitHub (a rede só deixa clonar via git do github.com)
- [ ] XAUUSD horário (2010+)
- [x] EURUSD (2009–2022) e USDJPY (2007–2018) via FX-Data (rodadas 4 e 5)
- [ ] NAS100 / NDX diário ou horário

## Estratégias (fontes públicas; uma por item)
Tendência e momentum
- [ ] Dual Momentum (Antonacci): momentum absoluto + relativo
- [x] Kaufman Efficiency Ratio / KAMA como filtro de tendência com entrada na virada (rodada 8)
- [x] Linear Regression Slope (inclinação de regressão) (rodada 8)
- [x] Ehlers MAMA/FAMA (rodada 8)
- [x] Trend Intensity Index / TII (rodada 8)
- [ ] Choppiness Index como interruptor tendência/lateral
- [x] Coppock Curve (rodada 8)
- [x] Know Sure Thing (Pring) (rodada 8)
- [x] TRIX (rodada 8)
- [ ] Rate of Change com volatilidade-alvo (Moskowitz vol scaling)
Reversão e osciladores
- [x] Ultimate Oscillator (Williams) (rodada 8)
- [x] DeMarker (DeMark) (rodada 8)
- [x] TD Sequential (DeMark setup 9) (rodada 8)
- [x] Laguerre RSI (Ehlers) (rodada 8)
- [x] Z-score de preço contra média com saída na média (rodada 8)
- [ ] Commodity Channel Index de 20 com divergência? (só se não repetir TV23)
- [ ] Relative Vigor Index
- [ ] Balance of Power
Volatilidade e estrutura
- [x] Chandelier Exit como sistema (diferente de Supertrend? conferir regra central) (rodada 8)
- [ ] ATR Channel breakout com filtro de volatilidade em contração (Bollinger Bandwidth percentil)
- [x] Gap/reversão após candle de range anormal (Wide Range Bar) (rodada 8)
- [ ] Turn of the month / dia do mês no BTC
- [ ] Efeito fim de semana do BTC (sexta→segunda)
- [ ] Reversão após queda de N desvios em H1 (crash-buying)
- [x] Market Structure (Higher High / Higher Low, quebra de estrutura) (rodada 8)
- [ ] Order block / Fair Value Gap (ICT) com regras fechadas
- [ ] Ichimoku Kumo breakout (regra diferente do L03? conferir)
Combinação e regime (só regras publicadas, nada inventado sobre resultado visto)
- [ ] Filtro de regime pela SMA 200 diária aplicado a uma regra nova de reversão
- [x] Hurst exponent como interruptor tendência/reversão (rodada 8)
- [ ] Volatility regime (ATR percentil) escolhendo entre rompimento e reversão
- [ ] Ensemble de votação de 5 indicadores clássicos (Ratings próprios)
