# Rodada 2 — tv-comunidade-e (scripts populares da comunidade TradingView)

Ativo BTCUSD, protocolo lab-v2. O WebFetch não alcançou tradingview.com (nem luxalgo.com/tradovate); as regras vieram dos resumos do WebSearch (páginas dos scripts no TradingView e espelhos ProRealCode, LuxAlgo, TradeStation, Optuma) e da definição clássica do Pine. Nenhum script original tem stop: todos usam stop de proteção k×ATR14. Teste de causalidade (sinais com série truncada = sinais com série inteira): ok nos quatro.

Todas as quatro passaram no desenvolvimento e reprovaram na validação (2021-2022), então nenhuma foi refinada (o protocolo proíbe reajuste depois de ver a validação).

## TV16_wavetrend — WaveTrend Oscillator (LazyBear)
- Fonte: tradingview.com/script/2KE8wTuF (LazyBear), código conferido em prorealcode.com e fórum Tradovate.
- Regra: WT1=EMA(ci,n2), ci=(hlc3-EMA)/(0,015·EMA|desvio|), WT2=SMA(WT1,4). Compra no cruzamento WT1>WT2 abaixo de -nível; venda no inverso acima de +nível; sai no cruzamento oposto.
- Calibrado: n1 {8,10,13}, n2 {16,21}, nível {40,53,60}, k {2,3}, lado; H1/H4/D1 (216).
- Escolhido H4 n1=13 n2=21 nível=53 k=3 só compra. Dev: 122 trades, +16,4R, PF 1,64, DD 4,5R (2,3%). Val: 55 trades, -3,8R, PF 0,77 (stress -5,3R). DSR 0,13.
- Veredito: REPROVADA_VALIDACAO. Resultado fraco já no desenvolvimento e DSR baixo: provável sorte de seleção.

## TV17_qqe — QQE (porta MT4 de Roman Ignatov)
- Fonte: tradingview.com/script/IYfA9R2k-QQE-MT4; LuxAlgo e TradeStation para a construção (Wilders 2n-1, fator 4,236/2,618).
- Regra: RsiMa=EMA(RSI(n),SF); linha de rastreio = RsiMa ± fator×EMA(EMA(|ΔRsiMa|,2n-1),2n-1) com bandas que só apertam; compra quando RsiMa cruza acima da linha, vende abaixo; sai no cruzamento oposto.
- Calibrado: n {10,14,21}, SF {3,5,8}, fator {2,618; 4,236}, k {2,3}, lado; H1/H4/D1 (216).
- Escolhido H4 n=14 SF=8 fator 4,236 k=2 só compra. Dev: 271 trades, +135,3R, PF 2,20, DD 6,7R. Val: 118 trades, -10,6R, PF 0,84, DD 20,8R (10,4%, acima do limite), stress -16,7R. DSR 0,99.
- Veredito: REPROVADA_VALIDACAO. Funcionou como seguidor de tendência comprado no touro 2016-2020 e quebrou no mercado de 2021-2022.

## TV18_schaff — Schaff Trend Cycle (LazyBear)
- Fonte: tradingview.com/script/eZwlb7PV; LuxAlgo, Optuma, ProRealCode (23/50/10, fator 0,5, gatilhos 25/75).
- Regra: MACD 23/50 passado por dois estocásticos de 'ciclo' candles com suavização 0,5; compra no cruzamento acima de 25, venda abaixo de 75; sai no gatilho oposto.
- Calibrado: rápida {15,23}, lenta {40,50}, ciclo {8,10,12}, k {2,3}, lado; H1/H4/D1 (144).
- Escolhido H4 23/50 ciclo 12 k=2 só compra. Dev: 307 trades, +125,9R, PF 2,07, DD 7,6R. Val: 129 trades, -11,7R, PF 0,81, DD 20,5R (10,2%), stress -18,2R. DSR 0,99.
- Veredito: REPROVADA_VALIDACAO. Mesmo padrão do QQE: comprado em momento de alta, depende do regime de alta do desenvolvimento.

## TV19_fisher — Fisher Transform (Ehlers)
- Fonte: tradingview.com/script/oVoigpVw (Fisher Crossover Strategy) e indicador embutido do TradingView; LuxAlgo.
- Regra: Fisher de hl2 (0,66/0,67, limite ±0,999, 0,5·ln), Trigger = Fisher anterior; compra quando Fisher cruza acima do Trigger abaixo de -nível; venda no inverso; sai no cruzamento oposto.
- Calibrado: n {7,9,13}, nível {0; 0,5; 1; 1,5}, k {2,3}, lado; H1/H4/D1 (144).
- Escolhido D1 n=7 nível 0 k=2 só compra. Dev: 115 trades, +34,8R, PF 2,40, DD 3,4R. Val: 62 trades, -5,1R, PF 0,66, stress -6,2R. DSR 0,27.
- Veredito: REPROVADA_VALIDACAO. Comprar fundos curtos no diário pagou no touro e não na queda de 2022.

Leitura geral: as quatro escolhas foram "só compra" e o desenvolvimento (2016-2020) é quase todo de alta do BTC; nenhuma das regras mostrou vantagem fora desse regime.
