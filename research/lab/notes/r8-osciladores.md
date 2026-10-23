# r8-osciladores — rodada 8 (lab-v4, BTCUSD)

Números: trades / netR / PF / DD% (0,5% por operação), custo base; stress entre parênteses quando relevante.

## L29_demarker — DeMarker (DeMark)
- Fonte: capital.com (fórmula e zonas 0,3/0,7), roboforex, script TradingView CF1kNGYo; DeMark, *The New Science of Technical Analysis* (1994).
- Regra: DeM = SMA(DeMax,n)/(SMA(DeMax,n)+SMA(DeMin,n)); compra ao sair da sobrevenda (cruza acima de lo), venda ao sair da sobrecompra; saída na zona oposta ('opp') ou em 0,5 ('mid'); stop k·ATR14 (fonte sem stop fixo).
- Grade: n 8/14/21, lo 0,2/0,3, saída, k 2/3, lado; H1/H4/D1 (144).
- Veredito: **REPROVADA_VALIDACAO**. Escolhida H4 n=21 lo=0,3 opp k=2 só compra (DSR 0,51).
- Dev 158 / +49,3R / 1,61 / 3,4% (5 de 5 anos). Validação 71 / −9,5R / 0,79 / 8,7% (stress −12,9R).
- Leitura: a combinação escolhida foi "só compra" e o ganho de 2016–2020 não sobreviveu a 2021–2022; sem vantagem própria comprovada.

## L30_td_setup9 — TD Sequential setup 9 (DeMark)
- Fonte: LuxAlgo (conceito TD Sequential), mql5 blog 750147; DeMark (1994) e Perl, *DeMark Indicators* (2008).
- Regra: virada de preço + 9 fechamentos seguidos abaixo (acima) do fechamento de 4 candles antes; perfeição = mínima do 8 ou 9 ≤ mínimas do 6 e 7 (máximas no espelho); entra no fechamento do 9; saída por tempo ou no setup oposto; stop TD Risk Level (mínima do setup − range verdadeiro, piso 0,5·ATR) ou k·ATR. Sem countdown.
- Original (144): **REPROVADA_DESENVOLVIMENTO**. Só o D1 tinha PF alto (4,3) mas com 14 operações; H1/H4 PF ≈ 1,0.
- r1 (filtro de tendência SMA100/200: setup de compra só acima da média, de venda só abaixo; 144): **REPROVADA_RESERVA**. H4 perfect=0 hold=5 trend=200 atr3 both, DSR 0,04.
  - Dev 82 / +5,3R / 1,39 / 2,7%. Validação 29 / +2,1R / 1,41 / 1,1% (stress +1,1R). Reserva 68 / −1,2R / 0,91 / 3,6% (stress −4,9R).
- Leitura: vantagem pequena e com DSR muito baixo; passou na validação por pouco e sumiu na reserva. A perfeição do setup não ajudou em nenhum tempo gráfico.

## L31_laguerre_rsi — Laguerre RSI (Ehlers)
- Fonte: Ehlers, *Cybernetic Analysis* (2004), "Time Warp – Without Space Travel"; código do backtrader (lrsi), MotiveWave, LuxAlgo; Pine "laguerre RSI v4" (TheLark) em /home/user/labdata/pine.
- Regra: filtro de Laguerre de 4 estágios (gamma), LRSI = CU/(CU+CD); compra quando cruza acima de lo (0,2), vende quando cruza abaixo de 1−lo; saída no sinal oposto ou em 0,5; stop k·ATR14 (fonte sem stop).
- Grade: gamma 0,5–0,8, lo 0,15/0,2, saída, k 2/3, lado; H1/H4/D1 (192).
- Veredito: **REPROVADA_VALIDACAO**. Escolhida H4 gamma=0,8 lo=0,15 opp k=3 só compra (DSR 0,74).
- Dev 142 / +86,4R / 2,81 / 3,0% (4 de 5 anos). Validação 68 / −9,5R / 0,71 / 8,8% (stress −11,7R).
- Leitura: o melhor desenvolvimento da rodada, mas de novo "só compra" na alta de 2016–2020; perdeu em 2021–2022, o padrão da lição da rodada 5.

## L32_zscore_revert — Z-score contra a média, saída na média
- Fonte: script TradingView ymvBzYSw (Z-Score Mean Reversion), StockSharp 0218 ZScore Reversal; definição clássica (Chan, *Algorithmic Trading*, 2013).
- Regra: z = (fech − SMA n)/DP n; entra quando z cruza além de ±zin (no extremo, diferente do G3 que espera voltar à banda); sai quando z volta a 0; stop k·ATR14.
- Original (162): **REPROVADA_DESENVOLVIMENTO** (H1/H4 PF < 1; D1 PF 1,86 com 19 operações).
- r1 (filtro de regime lateral, eficiência de Kaufman ER < er; 324): **REPROVADA_DESENVOLVIMENTO** (D1 13 operações; H4 PF ≈ 1,0).
- r2 (só H4/D1, n 10–30, zin 1,0–2,0 para ter amostra no D1; 192): **REPROVADA_VALIDACAO**. D1 n=10 zin=2,0 k=2 só compra, DSR 0,02.
  - Dev 51 / +6,0R / 1,42 / 2,1%. Validação 21 / −3,8R / 0,56 / 3,0% (stress −4,2R).
- Leitura: comprar o extremo de z no BTC não tem vantagem; o pouco que apareceu no D1 era compra de queda num mercado em alta e falhou na validação.

## Observações
- Nenhuma candidata; placebo e teste cruzado não se aplicam.
- Nada de errado achado no motor. Os caches dos arquivos usam id(df)+len(df) como chave (mesmo padrão de outras estratégias); dentro de um tempo gráfico os dados são os mesmos, então não muda o resultado.
