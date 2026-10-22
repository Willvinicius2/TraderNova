# r8-momento — rodada 8 (lab-v4, BTCUSD)

Nenhuma das quatro chegou a CANDIDATA. As três de momento (Coppock, KST, TRIX) escolheram no desenvolvimento a mesma coisa: só compra, H4, filtro EMA200, stop 2×ATR. Isso ganhou muito em 2016–2020 e perdeu já na validação 2021–2022. Pelo protocolo, não houve refinamento depois de abrir a validação.

## L25_coppock — Coppock Curve
- Fonte: StockCharts ChartSchool (Coppock Curve), LuxAlgo. Fórmula: WMA10(ROC14+ROC11). A fonte não traz código Pine.
- Regra: compra quando a curva cruza acima de zero. Abaixo de zero sai (side=long) ou vende (both). Filtro EMA opcional. Stop k×ATR14, que o original não tem.
- Grade: scale {1,2,4,8} (multiplica os períodos), trend {0,200}, k {2,3}, side {long,both}, em H1/H4/D1. São 96 combinações.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida: H4 scale=2 trend=200 k=2 long.
  - Desenvolvimento: 81 trades, +205,1R, PF 5,65, DD 3,4%, 5/5 anos positivos.
  - Validação: 23 trades, −10,2R, PF 0,39, stress −11,3R.
- Interpretação: o desenvolvimento brilhante é a alta do BTC filtrada pela EMA200. Na validação de 2021–22 a regra não se sustentou.

## L26_kst — Know Sure Thing (Pring)
- Fonte: Optuma KB (KST diário de Pring: ROC 10/15/20/30, SMA 10/10/10/15, pesos 1–4, sinal SMA9). Também citei a página da StockCharts, mas ela não abriu (o pedido de permissão expirou).
- Regra: compra quando o KST cruza acima do sinal e vende (both) no cruzamento abaixo. Filtros opcionais: KST>0 (zf) e EMA. Stop k×ATR14.
- Grade: scale {1,2,4}, zf {0,1}, trend {0,200}, k {2,3}, side, em H1/H4/D1. São 144 combinações.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida: H4 scale=2 zf=0 trend=200 k=2 long.
  - Desenvolvimento: 84 trades, +117,8R, PF 3,77, DD 2,4%.
  - Validação: 23 trades, −8,3R, PF 0,44, stress −9,6R.
- Interpretação: mesmo padrão da Coppock, só compra surfando a tendência. O KST não trouxe vantagem própria.

## L27_trix — TRIX
- Fonte: StockCharts ChartSchool (TRIX 15,9) e TTR (CRAN).
- Regra: TRIX é a variação % de 1 candle da EMA tripla. Opções: cruzamento da linha de sinal EMA9 ou do zero. O oposto fecha (ou inverte). Stop k×ATR14.
- Grade: n {9,15,30}, trig {signal,zero}, trend {0,200}, k {2,3}, side, em H1/H4/D1. São 144 combinações.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida: H4 n=15 cruzamento do zero, trend=200, k=2, long.
  - Desenvolvimento: 70 trades, +202,0R, PF 6,45, DD 3,0%.
  - Validação: 24 trades, −14,4R, PF 0,26, stress −15,6R.
- Interpretação: o cruzamento do zero do TRIX é, na prática, a virada da EMA tripla, ou seja, seguidor de tendência só comprado. Falhou fora da amostra.

## L28_ultimate_osc — Ultimate Oscillator (Williams), com 2 refinamentos
- Fontes: StockCharts, Incredible Charts (regras originais de Williams e revisão de Twiggs) e Wikipedia.
- L28 original: divergência de alta ou baixa entre pivôs de preço confirmados r candles depois (sem olhar o futuro). O 1º fundo precisa ter UO<30 (o 1º topo, UO>70). Gatilho quando o UO rompe o extremo do UO entre os pivôs.
  - Saídas de Williams: compra fecha com UO>70, ou com UO<45 depois de ter passado de 50. Venda fecha com UO<30 ou UO>65. Stop k×ATR14.
  - Aproximação: o "passou de 50" é contado desde o último sinal de compra.
  - Resultado: 144 combinações, **REPROVADA_DESENVOLVIMENTO**. O melhor foi D1 com só 8 trades (+2,2R, PF 1,46).
- r1 (motivo: frequência baixa demais): regra de zonas de Twiggs, com fundo mais alto depois de UO<30 e cruzamento de 50, mais filtro EMA opcional. 96 combinações, **REPROVADA_DESENVOLVIMENTO**. O melhor teve 21 trades no H1 e não foi robusto.
- r2 (motivo: no BTC o UO fica abaixo de 30 em só 0,2–0,5% dos candles): o nível do mergulho virou o parâmetro lv {30,35,40}. 144 combinações.
  - Veredito: **REPROVADA_VALIDACAO**. Escolhida: H4 lv=40 scale=2 trend=0 k=2 both.
  - Desenvolvimento: 117 trades, +27,4R, PF 1,36, DD 6,9%, 4/5 anos positivos, **DSR 0,0** (aviso de sorte na seleção).
  - Validação: 48 trades, −10,5R, PF 0,67, stress −12,8R.
- Interpretação: a regra de Williams quase não dispara no BTC. A versão afrouxada operava os dois lados, mas o DSR 0 já indicava sorte, e ela falhou na validação.
