# r9-regime — rodada 9 (lab-v4, BTCUSD)

As quatro estratégias reprovaram na validação (2021–2022). O protocolo não permite refinar depois de abrir a validação, então nenhuma ganhou _r1/_r2. A reserva não foi aberta.

## L41_chop_switch — Choppiness Index (Dreiss) como interruptor
- Fonte: LuxAlgo, conceito Choppiness Index (fórmula de Dreiss, limiares 61,8/38,2); Help Center do TradingView 43000501980; IncredibleCharts.
- Regra: o CHOP cruza abaixo de `lo` (a congestão acaba) → entra na direção de fech−fech[n]. Sai quando o CHOP cruza acima de `hi` ou no stop móvel k×ATR. No modo `switch`, com CHOP > hi, entra também na volta do RSI14 de 30/70, com alvo na SMA20. A diferença do L36 é o regime, que aqui vem do CHOP e não do Hurst, e o gatilho, que é o próprio CHOP e não Donchian nem z-score.
- Calibrado: n, lo, hi, k, side e mode (192 combinações). Escolha: H4 n=28 lo=45 hi=61,8 k=3, side both, mode trend. DSR 0,99. Mediana do PF dos vizinhos: 2,52.
- Desenvolvimento: 175 trades, +101,6R, PF 2,67, DD 2,2%, 5/5 anos positivos. Validação: 69 trades, +1,2R, PF 1,05. Sem a maior operação fica em −2,7R e no stress em −1,4R.
- Veredito: **REPROVADA_VALIDACAO**. O desenvolvimento era forte e robusto, mas a vantagem praticamente zerou em 2021–22.

## L42_sma200_reversion — banda da faixa média + IBS, com regime da SMA200 diária
- Fonte: QuantifiedStrategies, "3 best mean reversion strategies". A banda é a máxima de 25 dias − 2,25 × a média de H−L de 25 dias. Entra com IBS < 0,6 e sai quando o fechamento passa da máxima de ontem. A mesma regra está portada no StockSharp 0541. O filtro de regime pela SMA200 diária é o clássico (Faber; Connors e Alvarez).
- Calibrado: n, mult, ibs, k e side (216 combinações). Escolha: D1 n=40 mult=1,75 ibs=0,3 k=2, só compra. DSR 0,54.
- Desenvolvimento: 106 trades, +15,6R, PF 1,83, DD 1,6%, 4/5 anos. Validação: 22 trades, −1,5R, PF 0,75.
- Veredito: **REPROVADA_VALIDACAO**. O ganho no desenvolvimento era pequeno, com DSR de 0,54, e não se manteve.

## L43_atr_regime — percentil do ATR escolhe entre rompimento e reversão
- Fonte: LuxAlgo, "Volatility Regime Switches" (expansão → seguir tendência; compressão → reversão; estresse → ficar de fora) e "Volatility percentile/rank". Os módulos são o Donchian N com saída em N/2 e o RSI(2) 10/90 com saída na SMA5.
- Calibrado: L, lo, hi, N, k, side e stress (384 combinações). Escolha: H4 L=250 lo=0,3 hi=0,5 N=55 k=3, só compra, sem filtro de estresse. DSR 0,12.
- Desenvolvimento: 246 trades, +49,0R, PF 1,84, DD 7,7%, 4/5 anos. Validação: 88 trades, −2,1R, PF 0,89, stress −6,2R.
- Veredito: **REPROVADA_VALIDACAO**. O DSR baixo já avisava que a escolha podia ser sorte entre muitas combinações.

## L44_ensemble_vote — votação de 5 indicadores clássicos
- Fonte: LuxAlgo, "Ensemble Voting of Signals" (votos de EMA20/50, preço × SMA200, RSI14, MACD e Estocástico; zona neutra de 5 pontos; placar de −100 a 100 suavizado por EMA3; limiares 20/60); script "Ensemble Consensus System" do TradingView. A diferença do TV11 está em ter 5 votos de peso igual (o TV11 usa 26 componentes), entrar no cruzamento do limiar e sair pela perda do consenso, sem stop móvel por lucro.
- Calibrado: thr, ex, k e side (162 combinações). Escolha: H4 thr=20 ex=−20 k=2, só compra. DSR 1,0. Mediana do PF dos vizinhos: 4,5.
- Desenvolvimento: 124 trades, +267R, PF 5,23, DD 4,6%, 4/5 anos (2018 ficou em −2R). Validação: 63 trades, −10,7R, PF 0,71, DD 9,0%; no stress o DD passa de 10% (10,3%).
- Veredito: **REPROVADA_VALIDACAO**. É o caso clássico de "só compra" que surfou a alta de 2016–17 e 2019–20 e quebrou em 2021–22.
