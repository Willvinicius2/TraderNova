# Rodada 9 — agente r9-momento

Ativo BTCUSD, protocolo lab-v4. DD em % = DD em R × 0,5. Nenhum refinamento: as duas reprovadas caíram na validação (o protocolo proíbe reajustar depois).

## L37_dual_momentum — Dual Momentum (Antonacci)
- Fonte: Antonacci, *Dual Momentum Investing* (2014) / optimalmomentum.com; awealthofcommonsense.com (resumo do GEM); TradingView "12M Return Strategy".
- Adaptação (só há um ativo): absoluto = retorno de `look` dias > 0 (caixa ≈ 0); relativo = esse retorno acima da média dele mesmo nos últimos `rel` dias (o ativo contra a própria história de momentum). Rebalanceia a cada `rebal` dias e fica em caixa se algum dos dois filtros falhar. É diferente do L04, que usava só o absoluto. Stop de 3×ATR de 14 dias.
- Escolhido: D1, look 90, rel 365, rebal 7, k 3, both. DSR 0,58.
- Dev: 33 trades, +55,5R, PF 5,56, DD 6,2R (3,1%), 4/5 anos. Val: 12 trades, +3,3R, PF 1,82 (stress +3,1R), mas **−0,37R sem a maior operação**.
- **REPROVADA_VALIDACAO.** Opera pouco (6 por ano), e em 2021–22 o resultado veio de uma única operação.

## L38_roc_voltarget — ROC com volatilidade-alvo (Moskowitz, Ooi & Pedersen 2012)
- Fonte: SSRN 2089463; alphaarchitect (TSMOM e vol scaling); quantpedia.
- Regra: z = ROC(look) / (σ diária EWMA com centro de massa de 60 d × √look). Compra quando z cruza acima de z0, vende quando cruza abaixo de −z0, sai quando z volta a cruzar 0, decidido a cada candle. Stop de k×σ diária×preço, ou seja, posição inversa à volatilidade, que é o vol scaling em R. Há um filtro opcional de σ alta. Difere do L04 (sinal bruto do retorno, rebalanceamento a cada N dias, stop por ATR).
- Escolhido: H4, look 30, z0 0,5, k 2, vmax off, both. DSR 0,84.
- Dev: 63 trades, +112,4R, PF 5,58, DD 4,3R (2,2%), 5/5 anos, +79R sem a maior.
- Val: 31 trades, +11,2R, PF 1,85, DD 6,2R (3,1%), stress +10,4R.
- Res: 63 trades, +35,0R, PF 1,97, DD 7,8R (3,9%), stress +32,3R, +18R sem a maior.
- **CANDIDATA.** Placebo (20 sorteios), mediana: dev +22,7R, val +1,3R, res +3,5R; nenhum sorteio igualou o real (0/20 nas três fases).
- Teste cruzado, mesmos parâmetros: EURUSD reprova (val −8,0R, res −9,4R); USDJPY reprova (sem a maior ≤ 0, res +0,03R); ETH reprova (dev com só 41 trades, val sem a maior < 0; a reserva passa, +35,6R); SOL reprova (dev com 26 trades, res PF 1,09).
- Interpretação: é a melhor da rodada no BTC e o placebo diz que a vantagem vem da regra, mas é um seguidor de tendência que não se repete no câmbio. Isso confirma o padrão da triagem: funciona em cripto e não é uma regra geral.

## L39_relative_vigor — Relative Vigor Index (Ehlers, TASC 2002)
- Não é duplicata do TV74_rvi, que é o Relative *Volatility* Index de Dorsey. A triagem-v1 já tinha rodado o cruzamento puro (len 10, sem filtro); aqui entram o filtro de tendência EMA e a opção de zona.
- Fonte: Ehlers, TASC jan/2002; luxalgo; capital.com; Pine embutido do TradingView (port deepentropy rvi.ts).
- Escolhido: H4, len 10, EMA 100, sem zona, k 2, só compra. DSR 0,88.
- Dev: 513 trades, +103,6R, PF 1,77, DD 7,5R (3,8%), 4/5 anos. Val: 154 trades, −0,08R, PF 1,00, DD 17,3R (8,6%), stress −8,4R.
- **REPROVADA_VALIDACAO.** A vantagem do desenvolvimento era da compra na alta e sumiu em 2021–22.

## L40_balance_of_power — Balance of Power (Livshin, TASC ago/2001)
- Fonte: StockCharts ChartSchool (BOP; o autor recomenda SMA de 14 e o cruzamento de zero); luxalgo; Pine embutido (deepentropy bop.ts). A triagem tinha rodado o BOP cru; aqui ele é suavizado, com limiar e filtro EMA.
- Escolhido: D1, SMA 28, limiar 0, EMA 200, k 2, both. DSR 0,87.
- Dev: 41 trades, +146,5R, PF 15,1, DD 3,9R (1,9%), 5/5 anos. Val: 30 trades, +4,5R, PF 1,62, DD 2,3R, stress +3,9R, +1,5R sem a maior.
- Res: 80 trades, +10,5R, PF 1,47, DD 7,9R (3,9%), stress +8,0R, **+1,3R sem a maior** (passa por pouco).
- **CANDIDATA, mas fraca.** Placebo, mediana: dev +37,2R, val −1,8R, res +8,2R (7/20 sorteios ≥ real na reserva). Na reserva o placebo ganha quase o mesmo, então a vantagem ali não é da regra, e sim do filtro EMA 200, das saídas e do stop.
- Teste cruzado: reprova nos quatro ativos. EURUSD val −0,4R; USDJPY passa dev e val mas a res dá −4,5R; ETH dev com 27 trades e val PF 1,11; SOL val −1,4R.
- Interpretação: o PF 15 do desenvolvimento é a alta do BTC filtrada pela EMA 200. Fora dela, o ganho é quase o do placebo.
