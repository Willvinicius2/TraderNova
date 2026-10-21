# Rodada 2 — tv-embutidas-b (estratégias embutidas do TradingView, BTCUSD)

Protocolo lab-v2. Custos base 0,10%/lado (stress 0,20%). Nenhuma das quatro tem stop no Pine original: todas usam stop de proteção k×ATR14 (exigência do motor). As quatro são "sempre posicionadas" (doten) no Pine; com side=long o sinal de venda só fecha a compra. Todas abriram a validação e reprovaram lá, então **nenhum refinamento foi feito** (o protocolo proíbe reajuste depois de ver a validação).

## TV05_inside_bar — InSide Bar Strategy
- Fonte: https://in.tradingview.com/support/solutions/43000591665-inside-bar-strategy/ ; OANDA lab-education (explica o Pine embutido). O WebFetch não abriu o tradingview.com (DNS); regra confirmada pelos resumos de busca e pelo Pine embutido conhecido.
- Regra: candle interno (high<high[1] e low>low[1]); de alta → compra, de baixa → vende, a mercado (aqui na abertura seguinte).
- Calibrado: k (1,5–6) × side × H1/H4/D1 = 30.
- Escolhido D1 k=1,5 long. Dev: 125 trades, +46,3R, PF 1,99, DD 3,6%. Validação: 38 trades, −6,0R, PF 0,70 (stress −7,0R). **REPROVADA_VALIDACAO**.
- Interpretação: no desenvolvimento o ganho é basicamente estar comprado em BTC 2016–2020; em 2021–2022 o padrão sozinho não tem vantagem.

## TV06_outside_bar — OutSide Bar Strategy
- Fonte: Help Center "Built-in strategies" do TradingView; OANDA lab-education ?p=33250.
- Regra: candle externo (high>high[1] e low<low[1]); de alta → compra, de baixa → vende.
- Calibrado: k × side × tempos gráficos = 30.
- Escolhido H4 k=1,5 both. Dev: 703 trades, +132R, PF 1,36, DD 9,8%. Validação: 304 trades, +25,1R, PF 1,16, stress +3,8R, positiva sem a maior operação (+12,4R), mas **DD 14,7% > 10%** → **REPROVADA_VALIDACAO** (único critério que falhou). DSR 0,45 (aviso de provável sorte).
- Interpretação: a mais próxima de passar, mas a vantagem é fina (PF ~1,16, quase zerada no custo stress) e o drawdown é alto demais para 0,5% de risco.

## TV07_pivot_extension — Pivot Extension Strategy
- Fonte: https://in.tradingview.com/support/solutions/43000599888-pivot-extension-strategy/ ; OANDA lab-education ?p=33258.
- Regra (Pine): ph=ta.pivothigh(left,right), pl=ta.pivotlow(left,right) — pivôs de swing, não os pivôs diários P/R1/S1 do L15. Pivô de baixa confirmado (right candles depois) → compra; pivô de alta confirmado → vende. Pivô = máxima/mínima estritamente além dos left anteriores e right seguintes; confirmado só no fechamento de j+right (sem olhar o futuro).
- Calibrado: left 2–8, right 1–3, k 2–4, side, ×3 tempos = 216.
- Escolhido H4 left=2 right=3 k=4 long. Dev: 967 trades, +64,4R, PF 1,55, DD 2,4%. Validação: 402 trades, −11,0R, PF 0,82 (stress −21,4R). **REPROVADA_VALIDACAO**. DSR 0,01.
- Interpretação: comprar cada fundo de swing confirmado funcionou no mercado de alta, não em 2021–2022; DSR baixíssimo indica escolha por sorte entre muitas combinações.

## TV08_pivot_reversal — Pivot Reversal Strategy
- Fonte: Help Center "Built-in strategies" do TradingView; cópia do Pine em marketcalls.in (conversão para AFL) e descrição da LuxAlgo. WebFetch falhou nos dois; regra via resumos de busca + Pine embutido conhecido.
- Regra (Pine): ao confirmar pivô de alta guarda hprice e arma ordem stop de compra em hprice+tick, ativa até ser executada (máxima passa de hprice) ou surgir novo pivô de alta; espelho para venda. Ordem stop aproximada: trigger=close (fechamento além do nível, entrada na abertura seguinte) ou trigger=touch (candle tocou o nível, entrada na abertura seguinte — momento do Pine, preço pior). Ver também L14 (rompimento de fractal), regra parecida mas lá com filtro Alligator.
- Calibrado: left 2–6, right 1–3, k 2–4, side, trigger, ×3 tempos = 324.
- Escolhido H4 left=6 right=3 k=2 long close. Dev: 131 trades, +230R, PF 4,39, DD 3,8%. Validação: 74 trades, −26,0R, PF 0,54, DD 15,2% (stress −30,1R). **REPROVADA_VALIDACAO**.
- Interpretação: o PF 4,4 do desenvolvimento é o rompimento de topos capturando a alta de 2017/2020; na validação virou perda grande. Resultado de desenvolvimento espetacular não sobrevive fora da amostra.

## Observações sobre o motor
- calibrate.py faz o hash só do arquivo da estratégia; por isso o helper de pivôs foi copiado dentro de TV07/TV08 em vez de ficar num módulo separado.
- Nenhum bug encontrado.
