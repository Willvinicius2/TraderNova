# Rodada 2 — tv-comunidade-f (scripts populares da comunidade TradingView)

Ativo BTCUSD, protocolo lab-v2. Nenhum script original tem stop: todas usam stop de proteção k×ATR(14) (calibrado). Sinal no fechamento, entrada na abertura seguinte. Nenhum refinamento foi feito: as quatro abriram a validação, e o protocolo proíbe reajustar depois disso.
O TradingView não respondeu ao WebFetch (DNS); as regras vieram dos resumos do WebSearch das páginas do TradingView e de espelhos (cTrader, Barchart, Fidelity, Wikipedia).

## TV20_hull_suite — Hull Suite (InSilico)
- Fonte: https://www.tradingview.com/script/hg92pFwS-Hull-Suite/ (Pine reproduzido de memória: HMA/EHMA, cor verde quando HULL > HULL[2]).
- Regra: compra quando a cor vira para verde e vende quando vira para vermelho. Grade: modo hma/ehma, comprimento 34/55/89/144, k 2/3/4, lado. São 144 combinações.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida H4 hma 89 k3 long. Dev: 154 trades, +147R, PF 3,99, DD 6,4R. Val: 77 trades, −12,4R, PF 0,65, DD 17,9R (8,95%).
- Leitura: virou um seguidor de tendência que ganhou muito na alta de 2016–2020 e perdeu dinheiro em 2021–22.

## TV21_aroon — Aroon (Chande)
- Fontes: https://in.tradingview.com/support/solutions/43000501801 , https://help.ctrader.com/indicators/built-in/trend/aroon/
- Regra: Aroon Up cruza acima de Down (com Up ≥ nível opcional de 70) para comprar; o inverso para vender; sai no cruzamento oposto. Janela n+1 como no ta.aroon do Pine. Grade: n 14/25/50, nível 0/70, k 2/3/4, lado. São 108 combinações.
- Veredito: **CANDIDATA**. Escolhida H4 n50 nível70 k4 both, DSR 0,97.
  - Dev: 176 trades, +114,6R, PF 2,73, DD 5,1R.
  - Val: 64 trades, +6,1R, PF 1,23 (stress +4,3R, PF 1,16), DD 4,2%. Sem a maior operação: +2,2R base e só +0,5R no stress.
  - Reserva: 142 trades, +26,9R, PF 1,40 (stress +21,0R, PF 1,30), DD 15,6R (7,8%). Sem a maior operação: +7,9R base e +2,0R stress.
- Leitura: passou, mas com folga pequena. O PF caiu de 2,7 para cerca de 1,2–1,4 e o resultado sem a maior operação fica perto de zero no stress. Precisa de acompanhamento prospectivo antes de virar sinal.

## TV22_vortex — Vortex Indicator (Botes & Siepman)
- Fontes: https://en.wikipedia.org/wiki/Vortex_indicator , https://www.tradingview.com/script/Ol3XceHl/
- Regra: VI+ cruza acima de VI− para comprar, e o inverso para vender; sai no cruzamento oposto. Grade: n 14/21/28/42, k 2/3/4, lado. São 72 combinações.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida D1 n42 k2 both. Dev: 76 trades, +120R, PF 5,84, DD 4,0R. Val: 25 trades, −1,2R, PF 0,90.
- Leitura: o PF 5,8 no desenvolvimento era a tendência de alta do BTC, não uma vantagem que se manteve.

## TV23_cci — CCI (Lambert), cruzamento de ±100
- Fontes: https://www.barchart.com/trader/help/studies/cci.php , https://fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/cci , https://en.wikipedia.org/wiki/Commodity_channel_index
- Regra: CCI(hlc3) cruza acima de +100 para comprar e abaixo de −100 para vender. A saída é a volta pelo ±100 (Lambert) ou, na variante, o cruzamento de 0. Grade: n 14/20/30/50, saída, k, lado. São 144 combinações.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida H4 n50 saída zero k2 long. Dev: 113 trades, +221R, PF 4,25, DD 7,6R. Val: 51 trades, +0,3R, PF 1,01; stress −2,8R; sem a maior operação −7,6R.
- Leitura: empatou na validação, e o lucro do desenvolvimento era a tendência de alta.
