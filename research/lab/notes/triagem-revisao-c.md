# Revisão da triagem: agente c

Cinco regras D1. Os vizinhos são ±20% em cada parâmetro numérico, em BTC, ETH e SOL, com `vizinhos.py`. Para os parâmetros fixos no código, usei uma réplica em `research/cache/lab/tri/rev_c/lci.mjs`, explicada mais abaixo.

## Resumo

| id | regra | veredito | vizinhos BTC/ETH/SOL |
|---|---|---|---|
| trend-with-adx-ema-buy-sell-signals | Trend Green / Red Alert | **APROVADA_REVISAO** | 2/2 · 2/2 · 1/2 (só `len` muda o sinal) |
| macd-with-crossings-and-above-below-zero | marcadores de compra / venda | **DUVIDOSA** (duplicata da anterior) | 2/2 · 2/2 · 1/2 (só `adxLen` pesa) |
| bacap-price-structure-21-ema-trend | fechamento x linha 1 | **DUVIDOSA** | ±20%: 1/2 · 1/2 · 2/2; grade 15..27: 3/6 · 5/6 · 6/6 |
| emergent-rays-novathemachine | fechamento x linha 1 | **DUVIDOSA** (duplicata de bacap; fica bacap) | igual a bacap |
| dynamic-flow-ribbons | fechamento x linha 1 | **REPROVADA_REVISAO** | 1/6 · 6/6 · 2/6 |

## trend-with-adx-ema-buy-sell-signals (D1, Trend Green Alert / Trend Red Alert)

- **Pine:** "Trend with ADX/EMA - Buy & Sell Signals" de RMPM (tradingview.com/script/ZRYqpFdB). Não consegui ler o código-fonte: a página não abre e não encontrei o script nos clones locais. O .ts segue a definição pública do DI: RMA(TR), RMA(+DM) e RMA(−DM) com `len`, e `nz()` no primeiro candle. `trendGreen = DI+ > DI−`, `trendRed = DI− > DI+`.
- **Sinal:** é um alerta de estado, verdadeiro em todos os candles do regime (2.337 compras e 2.327 vendas em 4.677 candles). Na prática a regra é "fique do lado do DI dominante, com stop 2×ATR e reentrada depois do stop". É o sinal do autor, sem artefato da triagem.
- **Dado futuro:** nenhum. Só usa i e i−1, com RMA e EMA recursivas.
- **Vizinhos:** `vizinhos.py` informa 8/8 · 8/8 · 7/8, mas `th`, `len1` e `len2` não entram nessa regra (o resultado é idêntico ao padrão). Os vizinhos reais são `len` 11 e 17: BTC 2/2, ETH 2/2, SOL 1/2 (len=17 falha na reserva do SOL).
- **Veredito:** APROVADA_REVISAO. É a regra que fica entre as duplicatas DI+/DI−.

## macd-with-crossings-and-above-below-zero (D1, marcadores de compra / venda)

- **Pine:** "MACD With Crossings and Above Below Zero" de Kgroomes. Não encontrei o código. O .ts confere com a descrição pública: MACD/sinal, triângulos nos cruzamentos, setas DMI+ e DMI−, ADX e RSI.
- **O que a regra é de fato:** os marcadores incluem as setas "DMI+" (arrowUp, `plus > minus`) e "DMI−" (arrowDown), que aparecem em todo candle. Por isso a regra de marcadores virou o regime DI+/DI−, igual ao de trend-with-adx: 2.325 das 2.337 compras e 2.327 das 2.327 vendas coincidem. Os triângulos do MACD acrescentam cerca de 80 candles de cada lado, e 165 candles com compra e venda ao mesmo tempo são anulados em `build_sig`.
- **Dado futuro:** nenhum.
- **Vizinhos:** `vizinhos.py` informa 12/12 · 12/12 · 11/12. Porém fast, slow e signal quase não mudam o resultado, e `diLen` e `rsiLen` não entram no cálculo. Só `adxLen` pesa: BTC 2/2, ETH 2/2, SOL 1/2.
- **Veredito:** DUVIDOSA, porque é duplicata de trend-with-adx (fica trend-with-adx). O ganho vem das setas de estado do DMI, e não dos cruzamentos do MACD que dão nome ao indicador.

## bacap-price-structure-21-ema-trend (D1, fechamento x linha 1)

- **Pine:** "BACAP PRICE STRUCTURE 21 EMA TREND" de Alex_PrimeTrading (script ZqgAMXPq). Não consegui ler o código. O .ts segue a descrição: EMA 21 do high, do close e do low.
- **Linha 1:** `plot0`, a EMA21 do **high**. A regra compra quando o fechamento cruza acima da EMA21(high) e vende quando cruza abaixo.
  - O lado da compra coincide com a barra "bullish" do autor (fechamento acima das 3 EMAs).
  - O lado da venda é artefato da triagem. A barra "bearish" do autor exige `high < EMA21(low)`, uma condição bem mais forte.
  - O autor não publica sinal de compra/venda.
- **Dado futuro:** nenhum (só EMAs).
- **Vizinhos:** `vizinhos.py` informa 2/2 nos três ativos, mas `lineSize` não muda nada. Com o comprimento 21 fixo variando na réplica:
  - ±20% (17 e 25): BTC 1/2, ETH 1/2, SOL 2/2.
  - Grade 15/17/19/23/25/27: BTC 3/6, ETH 5/6, SOL 6/6.
  - As falhas no BTC são quase todas "sem a maior ≤ 0": o resultado depende de uma operação grande.
- **Veredito:** DUVIDOSA. O port é fiel e não usa dado futuro, mas a regra é genérica (fechamento x EMA21 do high, com a venda inventada) e o BTC só passa em metade dos vizinhos. Esta é a que fica em relação a emergent-rays.

## emergent-rays-novathemachine (D1, fechamento x linha 1)

- **Pine:** "Emergent Rays" de NovaTheMachine (script SQI0BZrR). Não consegui o código. Pela descrição, o autor diz que o indicador **não gera sinais de entrada**; ele propõe pullbacks nos raios e fim de tendência quando o preço fecha do outro lado de um raio. O .ts tem 10 pares de EMA(high) e EMA(low), com comprimentos de 21 a 65.
- **Linha 1:** `plot0`, a EMA21 do high, idêntica à linha 1 de bacap (diferença de 1e-15). A regra é a mesma, com resultados iguais até a segunda casa.
- **Dado futuro:** nenhum.
- **Vizinhos:** `vizinhos.py` informa 2/2, mas `opacity` não muda nada. Os vizinhos reais são os de bacap.
- **Veredito:** DUVIDOSA, por ser duplicata de bacap (fica bacap).

## dynamic-flow-ribbons (D1, fechamento x linha 1)

- **Pine:** "Dynamic Flow Ribbons [BigBeluga]", Pine v6, com o código obtido de uma cópia no Scribd (scribd.com/document/897318202). O .ts confere linha a linha:
  - `dist = sma(high−low, 200)`;
  - bandas `ema(hlc3, 15) ± factor·dist`, com a trava do supertrend;
  - `_direction` a partir de `trend_line[1]`;
  - `line_ = avg(lower, upper)`.
- **Linha 1:** `plot0`, o "TrendLine", que é o ponto médio das bandas (perto da EMA15 de hlc3 quando nenhuma banda está travada). O sinal do autor é a mudança de `_direction` (cor), não o cruzamento do fechamento com a linha média. A regra testada é artefato da triagem.
- **Dado futuro:** nenhum. Usa `dist[i−1]` e valores do candle anterior.
- **Vizinhos:** pela réplica, com fator 2,4/3,6, EMA 12/18 e SMA 160/240: BTC 1/6, ETH 6/6, SOL 2/6. `vizinhos.py` testou o fator 2 e 4 (bug abaixo): 0/2, 2/2, 1/2.
- **Veredito:** REPROVADA_REVISAO. A regra não é a do autor e só o ETH aguenta os vizinhos; no BTC e no SOL praticamente só o padrão passa.

## Como foram feitos os vizinhos de parâmetros fixos

`research/cache/lab/tri/rev_c/` tem uma cópia temporária e local, sem editar o clone:

- `lci.mjs` reexporta a biblioteca e acrescenta `rev-bacap` (`len`) e `rev-dfr` (`factorX100`, `emaLen`, `distLen`).
- Com os valores padrão, as réplicas reproduzem a linha 1 dos originais (diferença ≤ 1e-15 em bacap e emergent; 0 de 4.677 candles divergentes em dynamic-flow-ribbons).
- Os vizinhos rodaram com o próprio `vizinhos.py`, apontando `T.TRI` para essa pasta pelo script `scratchpad/c/viz_rev.py`.

## Problemas na triagem

1. **`vizinhos.py`: arredondamento de entradas float.** Uma entrada float com padrão inteiro (`factor: 3`) chega pelo JSON como int e é arredondada para 2 e 4 (±33%), em vez de 2,4 e 3,6.
2. **`vizinhos.py`: parâmetros inertes inflam a contagem.** Parâmetros que não entram no sinal contam como "vizinhos que passam" (lineSize, opacity, th, len1/len2, diLen, rsiLen). É preciso olhar quais parâmetros mudam o sinal de fato.
3. **`sinais.mjs`: marcadores de estado tratados como entrada.** Marcadores de estado (setas DMI em todo candle) entram como sinal de entrada junto com os marcadores de evento. A regra "marcadores" fica dominada pelo estado e perde o sinal que dá nome ao indicador.
4. **`sinais.mjs`: a regra genérica usa `plots[0]`.** Esse plot pode ser uma linha qualquer (EMA do high, linha média das bandas), e não o gatilho do autor. Por isso duas regras "diferentes" (bacap e emergent-rays) saíram idênticas.
