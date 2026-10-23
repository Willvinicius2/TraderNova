# Revisão da triagem — agente b

Seis regras D1. As quatro primeiras são a mesma ideia: o +DI cruza o -DI (Wilder). Só muda a suavização.

Checagens feitas em todas:
- **Dado futuro.** Li o código: o candle i só usa i e i-1, mais ta.ema/rma/sma/dmi, que são causais. Também rodei um teste de corte, com o indicador calculado nos candles até k e comparado ao valor no candle k-1 (k = 300, 800, 1500, n-200, n-5) em BTC e ETH. Deu 0 divergências em todos os plots dos seis indicadores (script em scratchpad/la.mjs).
- **Vizinhos.** Rodei `vizinhos.py` com ±20% em cada parâmetro. Os parâmetros que não mudam o sinal aparecem como "=" e não entram na contagem.

## adx-and-di D1 | linha 1 x linha 2
- **Fonte.** "ADX and DI for v4", de BeikabuOyaji. O Pine completo não abriu: o .pinescript4 em indie-script.github.io foi bloqueado pelo proxy. Trechos publicados na página da indie-script conferem com o .ts: TR com nz(close[1]), DM+ e DM- exclusivos, soma de Wilder `s - s/len + x`, DX e ADX = sma(DX, len).
- **Linhas.** plot0 = DI+ e plot1 = DI-, portanto a regra é DI+ x DI-. É o sinal clássico do DMI; o autor não marca sinal próprio.
- **Vizinhos (len 11/17).** BTC 2/2, ETH 1/2, SOL 1/2. Com len=17, ETH e SOL caem por outros critérios: o netR fica positivo nas três fases.
- **Duplicata.** É a mesma regra que dmi-delta-by-0xjcf: 292 de 293 sinais iguais em BTC.
- **Veredito: DUVIDOSA.** O port é fiel e não usa dado futuro, mas os vizinhos só passam com folga em um ativo.

## dmi-delta-by-0xjcf D1 | linha 1 x zero
- **Fonte.** "DMI Delta by 0xjcf", de J_O_S_E_. Não achei o Pine. O .ts é DI+ − DI- de ta.dmi(14, 14), que é a definição pública.
- **Linha.** plot0 = delta (histograma), então delta x zero equivale a DI+ x DI-. Os demais inputs (limites, ADX, volume, RSI) só mudam a cor e não o sinal.
- **Vizinhos (dmiLength 11/17).** BTC 2/2, ETH 1/2, SOL 1/2, idênticos aos de adx-and-di.
- **Veredito: DUVIDOSA.** Duplicata de adx-and-di; fica adx-and-di, ou a representante da família (abaixo).

## adx-with-shaded-zone D1 | linha 1 x linha 2
- **Fonte.** "ADX with Shaded Zone", de MathThomas. Não achei o Pine.
- **Diferença.** O .ts usa DM+ e DM- não exclusivos ("como o Pine", diz o cabeçalho) e RMA(length). Por isso não é idêntico ao Wilder exato: 230 de 293 sinais iguais aos de adx-and-di.
- **Linhas.** plot0 = +DI e plot1 = -DI.
- **Vizinhos (length 11/17).** BTC 1/2, ETH 2/2, SOL 1/2.
- **Veredito: DUVIDOSA.** É quase duplicata da família DI e não tem fonte conferível.

## directional-indicator-crossovers-v1 D1 | linha 1 x linha 2
- **Fonte.** "Directional Indicator Crossovers v1 [JopAlgo]". Não achei o Pine. O .ts segue a definição de Wilder com EMA(20).
- **Linhas.** plot0 = +DI e plot1 = -DI. O cruzamento é exatamente o alertcondition do autor ("Bullish/Bearish DI Crossover", com o filtro de ADX desligado no padrão). Logo, a regra genérica coincide com o sinal do autor.
- **Bug da triagem.** Em sinais.mjs, `side("Bearish DI Crossover")` dá 0, porque o LONG contém "crossover" e o SHORT contém "bearish". Por isso o alerta não virou regra. Os marcadores (círculo em top/bottom) também dão 0. Aqui não muda nada, mas outros indicadores com títulos "Bearish … Crossover" podem ter perdido a regra de alerta.
- **Vizinhos (dilen 16/24).** BTC 2/2, ETH 2/2, SOL 2/2. adxLen e adxThr não mudam o sinal.
- **Veredito: APROVADA_REVISAO.** É a representante da família DI.

## macdas D1 | linha 1 x linha 2
- **Fonte.** MACDAS (MACD de Thomas Aspray), de KIVANC (fr3762) no TradingView. O código não abriu, mas a definição pública confere com o .ts: macdAS = MACD − sinal e signalAS = EMA(macdAS, 9).
- **Linhas.** plot0 = MACD-AS e plot1 = Signal-AS. O cruzamento entre eles é o uso descrito por Aspray. O warmup = slow + signal só esconde o começo.
- **Vizinhos (fast, slow, signal).** BTC 4/6, ETH 2/6, SOL 4/6.
- **Veredito: APROVADA_REVISAO.** A maioria passa em BTC e SOL. ETH é fraco (reserva de +7R e vizinhos caindo).

## elder-force D1 | linha 1 x zero
- **Fonte.** "Elder Force Index", a embutida do TradingView: `ta.ema(ta.change(close) * volume, 13)`. O .ts confere.
- **Linha.** plot0 = EFI x zero, que é o uso de Elder (troca de sinal).
- **Volume.** O resultado depende do volume da fonte de dados (BTC D1 tem 3 candles com volume 0).
- **Vizinhos (length 10/16).** BTC 2/2, ETH 1/2, SOL 1/2. length=10 falha em ETH e SOL.
- **Veredito: DUVIDOSA.**

## Observações sobre os scripts
- **Família DI.** adx-and-di, dmi-delta, shaded-zone e DIXV1 são o mesmo sinal com suavizações diferentes (63–100% dos sinais em comum). Contam como uma regra só; sugiro manter directional-indicator-crossovers-v1.
- **vizinhos.py.** Usa `max(1, round(v*f))`, o que transforma parâmetros negativos em 1 (lowerLimit=-30 virou 1). Um float com valor inteiro (volumeMultiplier 3.0, que chega do JSON como 3) é tratado como int. Aqui isso não afetou o resultado, porque esses parâmetros não mudam o sinal.
