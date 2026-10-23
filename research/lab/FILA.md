# Fila de pesquisa contínua

Cada rodada pega os próximos itens **não marcados** (cerca de 16 estratégias, 4 agentes) e um agente de dados.
Antes de testar, confira `registry.json`: a mesma regra central com outros parâmetros, ativo ou tempo gráfico **não** é estratégia nova. Marque `[x]` quando o item for testado.

## Meta ("resultado bom")
Uma estratégia só sai do laboratório quando:
1. passa no lab-v2 no BTCUSD;
2. passa com os **mesmos parâmetros** em pelo menos um segundo ativo (ETH, ouro, EURUSD ou NAS100);
3. fica 30 dias em acompanhamento simulado em tempo real sem quebrar o limite de queda.
Quando 1 e 2 acontecerem, avisar o Will na hora.

**Situação em 23/10/2026:** a triagem em massa (`TRIAGEM.md`) achou 17 regras que passam em BTC, ETH e SOL com os mesmos parâmetros (nenhuma em câmbio). O Will respondeu em 23/10: seguir. Revisão do código em `notes/triagem-revisao-*.md`; o item 3 (30 dias em papel) começou em 23/10 e vai até 22/11 (`PAPEL.md`, `papel/papel.py`). As rodadas voltaram a abrir normalmente.

## Triagem-v2 (correções achadas na revisão de 23/10, ver REVISAO_TRIAGEM.md)
- [ ] Corrigir a classificação de títulos "Bearish … Crossover", separar marcadores de estado e de evento, e preferir o plot gatilho do autor na regra genérica; rodar a triagem de novo como triagem-v2 (contar as regras novas no DSR)

## Dados (agente de dados, toda rodada até resolver)
- [x] ETHUSD horário (Binance spot pelo espelho S3, 22/10; SOLUSD também)
- [x] XAUUSD horário 2010–03/2025 (rodada 9, servidor MetaTrader validado contra Dukascopy)
- [x] EURUSD (2009–2022) e USDJPY (2007–2018) via FX-Data (rodadas 4 e 5)
- [x] NAS100 horário 2010–02/2026 (rodada 9, HistData NSXUSD)

## Estratégias (fontes públicas; uma por item)
Tendência e momentum
- [x] Dual Momentum (Antonacci): momentum absoluto + relativo (rodada 9)
- [x] Kaufman Efficiency Ratio / KAMA como filtro de tendência com entrada na virada (rodada 8)
- [x] Linear Regression Slope (inclinação de regressão) (rodada 8)
- [x] Ehlers MAMA/FAMA (rodada 8)
- [x] Trend Intensity Index / TII (rodada 8)
- [x] Choppiness Index como interruptor tendência/lateral (rodada 9)
- [x] Coppock Curve (rodada 8)
- [x] Know Sure Thing (Pring) (rodada 8)
- [x] TRIX (rodada 8)
- [x] Rate of Change com volatilidade-alvo (Moskowitz vol scaling) (rodada 9)
Reversão e osciladores
- [x] Ultimate Oscillator (Williams) (rodada 8)
- [x] DeMarker (DeMark) (rodada 8)
- [x] TD Sequential (DeMark setup 9) (rodada 8)
- [x] Laguerre RSI (Ehlers) (rodada 8)
- [x] Z-score de preço contra média com saída na média (rodada 8)
- [x] Commodity Channel Index de 20 com divergência? (só se não repetir TV23) (rodada 9)
- [x] Relative Vigor Index (rodada 9)
- [x] Balance of Power (rodada 9)
Volatilidade e estrutura
- [x] Chandelier Exit como sistema (diferente de Supertrend? conferir regra central) (rodada 8)
- [x] ATR Channel breakout com filtro de volatilidade em contração (Bollinger Bandwidth percentil) (rodada 9)
- [x] Gap/reversão após candle de range anormal (Wide Range Bar) (rodada 8)
- [x] Turn of the month / dia do mês no BTC (rodada 9)
- [x] Efeito fim de semana do BTC (sexta→segunda) (rodada 9)
- [x] Reversão após queda de N desvios em H1 (crash-buying) (rodada 9)
- [x] Market Structure (Higher High / Higher Low, quebra de estrutura) (rodada 8)
- [x] Order block / Fair Value Gap (ICT) com regras fechadas (rodada 9)
- [x] Ichimoku Kumo breakout (regra diferente do L03? conferir) (rodada 9)
Combinação e regime (só regras publicadas, nada inventado sobre resultado visto)
- [x] Filtro de regime pela SMA 200 diária aplicado a uma regra nova de reversão (rodada 9)
- [x] Hurst exponent como interruptor tendência/reversão (rodada 8)
- [x] Volatility regime (ATR percentil) escolhendo entre rompimento e reversão (rodada 9)
- [x] Ensemble de votação de 5 indicadores clássicos (Ratings próprios) (rodada 9)
