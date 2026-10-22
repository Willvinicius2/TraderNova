# r8-tendencia: rodada 8 (lab-v4), BTCUSD

Todas as quatro saíram **REPROVADA_VALIDACAO**. Nenhuma pôde ser refinada, porque a validação já tinha sido aberta. Antes de rodar, conferi no registry.json que nenhuma estratégia já testada tem KAMA, inclinação de regressão, MAMA/FAMA ou TII como regra central. Também conferi que nenhuma olha o futuro: os sinais calculados com os dados cortados no candle 8000 são iguais aos calculados com a série inteira até esse ponto.
Nenhuma das fontes traz stop, então usei um stop de proteção de k×ATR14 em todas.

## L21_kama: Kaufman KAMA com filtro de ER
- Fontes: StockCharts ChartSchool (KAMA), TA-Lib (ER) e a regra de filtro da AMA de Kaufman (Trading Systems and Methods).
- Regra: KAMA(n, 2, 30). A virada acontece quando a KAMA se afasta da sua mínima (ou máxima) desde a última virada por mais de f × desvio-padrão(ΔKAMA, 20). A entrada só vale se ER(n) >= er_min. A posição sai ou inverte na virada oposta.
- Grade: n {10, 20}, f {0, 0.5, 1}, er_min {0, 0.2, 0.3}, k {2, 3}, lado {long, both}. Tempos gráficos H1, H4 e D1, 216 combinações.
- Combinação escolhida: H4, n=10, f=0.5, er_min=0, k=2, long.
- Desenvolvimento: 252 operações, +196,9R, PF 2,87, DD 7,9R (3,9%), 5 de 5 anos positivos, DSR 0,95.
- Validação: 109 operações, −11,2R, PF 0,79 (stress −17,0R).
- Interpretação: ficou comprada na alta de 2016–2020 e perdeu na baixa de 2021–2022. O filtro de ER nem chegou a ser usado na combinação escolhida.

## L22_linreg_slope: inclinação da regressão linear
- Fontes: StockCharts ChartSchool "Slope" (cruzamento do zero = mudança de tendência) e thinkorswim LinearRegressionSlope.
- Regra: s = inclinação da regressão de n candles × n / ATR14. A entrada acontece quando s cruza ±thr. A saída acontece quando s cruza o zero no sentido contrário.
- Grade: n {20, 50, 100}, thr {0, 0.5, 1, 2}, k {2, 3}, lado {long, both}. Tempos gráficos H1, H4 e D1, 144 combinações.
- Combinação escolhida: H4, n=20, thr=2, k=2, long.
- Desenvolvimento: 189 operações, +157,5R, PF 3,10, DD 5,8R, 5 de 5 anos positivos.
- Validação: 78 operações, −20,2R, PF 0,63, DD 14,3%.
- Interpretação: é um seguidor de momentum de compra que depende do regime de alta.

## L23_mama_fama: Ehlers MAMA/FAMA
- Fontes: Ehlers, S&C set/2001 (EasyLanguage), ProRealCode e LuxAlgo. Usei como conferência o porte em labdata/pine (mama-fama.ts).
- Regra: preço (máx+mín)/2. A transformada de Hilbert dá a fase, e daí vem alpha = fast/ΔFase, limitado entre slow e fast. A entrada é o cruzamento MAMA × FAMA, e a posição inverte no cruzamento oposto.
- Grade: fast {0.3, 0.5, 0.7}, slow {0.02, 0.05, 0.1}, k {2, 3, 4}, lado {long, both}. 162 combinações.
- Combinação escolhida: H4, fast=0.3, slow=0.05, k=2, long.
- Desenvolvimento: 118 operações, +233,7R, PF 4,95, DD 7,5R, 4 de 5 anos positivos.
- Validação: 65 operações, −20,4R, PF 0,56 (stress −24,2R).
- Interpretação: o mesmo padrão. A eficiência enorme no desenvolvimento vem da alta do BTC, não de vantagem da regra.

## L24_tii: Trend Intensity Index (M. H. Pee)
- Fontes: S&C jun/2002 (Pee), Linnsoft TII (compra acima de 80, venda abaixo de 20, mantém até o sinal oposto) e o PDF do artigo.
- Regra: TII = 100·SDPOS/(SDPOS+SDNEG), com os desvios do fechamento em relação à SMA(P) somados nos últimos P/2 candles. A entrada é o cruzamento do nível (venda em 100 − nível). A saída é o sinal oposto ou o cruzamento de 50.
- Grade: P {30, 60, 120}, nível {70, 80, 90}, saída {oposto, 50}, k {2, 3}, lado {long, both}. 216 combinações.
- Combinação escolhida: H1, P=120, nível=80, saída oposto, k=3, long.
- Desenvolvimento: 130 operações, +310,3R, PF 4,58, DD 10,5R (5,2%), 4 de 5 anos positivos.
- Validação: 57 operações, −8,4R, PF 0,82 (stress −13,0R).
- Interpretação: tendência de compra e mais nada. Perdeu pouco na validação, mas perdeu.

## Conclusão
As quatro médias e osciladores de tendência clássicos repetem o que já aconteceu com L01, TV20 e TV44: a combinação escolhida é sempre "só compra", parece ótima em 2016–2020 e fica negativa em 2021–2022. Mesmo com "both" na grade, a seleção por netR/DD escolheu "long" em todos os casos.
