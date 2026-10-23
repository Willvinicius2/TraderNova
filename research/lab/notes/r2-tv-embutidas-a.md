# Rodada 2 — tv-embutidas-a (estratégias embutidas do TradingView, BTCUSD, lab-v2)

O WebFetch não conseguiu abrir tradingview.com (falha de DNS). Por isso as regras vieram dos resumos do WebSearch sobre as páginas do Help Center (que trazem o Pine), dos artigos da OANDA lab-education e de cópias do Pine na comunidade. Nenhuma das quatro tem stop no Pine original, então todas usam um stop de proteção de k×ATR14. Nenhuma foi refinada, porque as quatro chegaram à validação, e o protocolo proíbe reajuste depois disso.

## TV01_barupdn — BarUpDn Strategy (padroes)
- Fonte: Help Center "Built-in strategies", oanda.jp (BarUpDn) e o script 7IDDZNte.
- Regra: compra com vela de alta que abre acima do fechamento anterior; venda no espelho. Sempre posicionada, com inversão. O "max intraday loss" não foi reproduzido. Stop k×ATR.
- Calibrado: k e side (30 combinações). Escolhida: H4, k=3, só compra.
- Dev: 946 trades, +52,8R, PF 1,31, DD 6,4%. **Val: 472 trades, −17,0R, PF 0,81, DD 10,6% → REPROVADA_VALIDACAO.**
- Interpretação: a vantagem no desenvolvimento era só o beta de compra do BTC em 2016–2020, e ela some em 2021–22.

## TV02_consecutive — Consecutive Up/Down Strategy (tendencia)
- Fonte: Help Center 43000599836 (com o Pine).
- Regra: compra após N fechamentos seguidos em alta e vende após N em baixa. Sempre posicionada. Stop k×ATR.
- Calibrado: n, k e side (96 combinações). Escolhida: D1, n=4, k=2, compra e venda.
- Dev: 42 trades, +187R, PF 11,7, DD 2,5%. A amostra é pequena e quase toda da alta de 2017, e o DSR ficou em 0,47 (aviso de sorte na seleção). **Val: 26 trades, +3,1R, PF 1,22, mas fica negativa sem a maior operação (−0,13R) → REPROVADA_VALIDACAO** (o stress foi +2,6R).
- Interpretação: o PF do desenvolvimento é um artefato de poucas operações num mercado em bolha. Na validação tudo depende de uma única operação.

## TV03_greedy — Greedy Strategy (padroes)
- Fonte: Help Center 43000599876 e oanda.jp (?p=31673).
- Regra: entra com gap de abertura além da máxima/mínima anterior. A ordem stop foi aproximada por entrada na abertura seguinte. Não há pirâmide (o motor tem uma posição só). O alvo e o stop em ticks viraram tp×ATR e sl×ATR. Em BTC 24/7 o gap só aparece no intraday (são buracos ou saltos entre candles), por isso foram testados M15, H1 e H4.
- Calibrado: sl, tp e side (96 combinações). Escolhida: H1, sl=3, tp=4, só compra. DSR 0,02.
- Dev: 312 trades, +39,2R, PF 1,24, DD 4,1%. **Val: 155 trades, −47,7R, PF 0,57, DD 25% → REPROVADA_VALIDACAO.**
- Interpretação: os "gaps" do BTC são, em grande parte, ruído de dados ou de liquidez. Não há vantagem nenhuma.

## TV04_volty_expan — Volty Expan Close Strategy (volatilidade)
- Fonte: Help Center 43000599890, oanda.jp (?p=34388) e o script PRck7Phi.
- Regra: atrs = SMA(TR, length)×mult. Compra stop em fech+atrs e venda stop em fech−atrs, com inversão. A ordem stop foi aproximada por fechamento além de fech[i−1]±atrs[i−1] e entrada na abertura seguinte. Stop k×ATR. A ideia é parecida com a do L10 (Williams volatility breakout), mas a referência é o fechamento e a posição é sempre ativa.
- Calibrado: length, mult, k e side (288 combinações). Escolhida: H4, length=5, mult=1,5, k=2, só compra. DSR 0,95.
- Dev: 141 trades, +185R, PF 3,70, DD 2,8%. **Val: 67 trades, −10,5R, PF 0,74, DD 9,2% → REPROVADA_VALIDACAO.**
- Interpretação: comprar candles de expansão funcionou muito bem na tendência de alta de 2016–2020, mas não se sustentou no mercado de 2021–22.

Resumo: 0 de 4 passaram. Nenhuma é CANDIDATA.
