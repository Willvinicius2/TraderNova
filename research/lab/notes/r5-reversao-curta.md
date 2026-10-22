# r5-reversao-curta — Rodada 5, bloco 7 (TV60–TV63), BTCUSD, protocolo lab-v3

Todas sem stop no original: stop de proteção k×ATR14 (motor exige). Decisão no fechamento, entrada na abertura seguinte.
Versões "both" espelham a regra para venda abaixo da SMA de tendência.

## TV60 Connors RSI — REPROVADA_VALIDACAO (após 1 refinamento)
- Fonte: indicador embutido do TradingView (fórmula pelo código traduzido deepentropy `connors-rsi.ts`); regras de trade: LuxAlgo (extremo <10/>90 com filtro de 200, sai em 50) e FILA (sai em 70). Connors, Alvarez & Radtke (2012).
- Regra: CRSI = média de RSI(3), RSI(2) da sequência e PercentRank(100) do retorno de 1 candle (como `ta.percentrank` do Pine). Compra com fechamento > SMA200 e CRSI < limiar; sai com CRSI > 50/70.
- Original (72 comb.): reprovou no desenvolvimento. Melhor H1 thr10: 264 trades, +6,95R, PF 1,20, mas vizinhos PF 0,87 e 3/5 anos; thr5 robusto com só 44 trades.
- r1 (motivo: SMA200 intradiária cobre poucos dias; testa tendência 200/400/800 e limiar mais fino; 192 comb.): escolhido H1 trend200 thr7,5 sai 70 k2 long.
  Dev 141 trades, +8,83R, PF 1,31, DD 6,0R (3,0%), 4/5 anos. Validação 43 trades, −10,32R, PF 0,43, DD 11,3R (5,6%); stress −14,4R.
- Leitura: a vantagem do desenvolvimento era pequena (t≈1) e escolhida entre 192 combinações (DSR 0,05); sumiu em 2021–22.

## TV61 Double 7's — REPROVADA_VALIDACAO
- Fonte: StrategyQuant (regra do livro Connors & Alvarez 2008); script do TradingView é protegido.
- Regra: fechamento > SMA200 e fechamento = mínima de n fechamentos → compra; sai quando fechamento = máxima de n. Grade n 5/7/10, k 2/3/4, long/both (54 comb.).
- Escolhido D1 n10 k2 long. Dev 49 trades, +10,07R, PF 1,62, DD 2,65R (1,3%), 4/5 anos, DSR 0,74. Validação 12 trades, −0,11R, PF 0,97; stress −0,29R.
- Leitura: no D1 opera pouco e é "só compra" em alta; em 2021–22 ficou no zero. Não há evidência de vantagem.

## TV62 %b de Connors — REPROVADA_VALIDACAO (após 2 refinamentos)
- Fonte: regra do livro Connors & Alvarez (2009, High Probability ETF Trading); páginas QuantifiedStrategies/StockSharp citam a regra mas os detalhes estão atrás de paywall, então usei a definição clássica (igual à FILA).
- Regra: fechamento > SMA200 e %B(20,2) < lo por d fechamentos seguidos → compra; sai com %B > 1−lo (0,8).
- Original (108 comb.): reprovou no dev (melhor H4 50 trades, +6,0R, PF 1,29, vizinhos 1,03, 3/5 anos).
- r1 (saída na banda do meio 0,5 e tendência 100/200; 288 comb.): reprovou no dev (melhor H4 50 trades, PF 1,46, 3/5 anos).
- r2 (filtro de volatilidade opcional ATR/fechamento < mediana 500, d até 5; 192 comb.): escolhido H1 trend200 d5 lo0,1 sem filtro de vol, k2, long.
  Dev 68 trades, +13,63R, PF 1,46, DD 5,45R (2,7%), 4/5 anos. Validação 30 trades, −6,22R, PF 0,67, DD 8,2R (4,1%); stress −9,2R.
- Leitura: depois de 588 combinações a escolha (d=5, ponta da grade) é provavelmente ajuste ao ruído (DSR 0,06); falhou fora da amostra.

## TV63 Mass Index reversal bulge — REPROVADA_RESERVA
- Fonte: StockCharts ChartSchool (bulge > 27 e volta < 26,5; direção por outra análise), Pine do everget (`oscillators/mass_index.pine`), Wikipedia (direção pela EMA9). A fonte não define saída: usei saída por tempo (hold) + alvo 2R.
- Regra: MI = soma(25) de EMA9(H−L)/EMA9(EMA9(H−L)). Arma quando MI > brk e dispara quando volta abaixo de brk−0,5; EMA9 do fechamento subindo → venda, caindo → compra. Grade brk 26/26,5/27, hold 10/20/40, k 2/3, long/both (108 comb.).
- Escolhido H4 brk27 hold10 k3 both. Dev 83 trades, +10,55R, PF 1,60, DD 4,0R (2,0%), 4/5 anos. Validação 29 trades, +1,94R, PF 1,49 (stress +1,03R) — passou.
  Reserva 90 trades, −9,97R, PF 0,53, DD 13,1R (6,6%); stress −14,5R.
- Leitura: DSR 0,03 já avisava sorte na seleção; a validação passou com pouco (+1,9R) e a reserva 2023–26 desmentiu. Sem vantagem.
