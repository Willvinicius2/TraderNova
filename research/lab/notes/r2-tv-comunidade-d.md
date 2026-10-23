# Rodada 2 – tv-comunidade-d (scripts da comunidade TradingView)

Ativo BTCUSD, protocolo lab-v2. Desenvolvimento 2016–2020, validação 2021–2022, reserva 2023–2026. Custo base 0,10%/lado.
O WebFetch não alcançou tradingview.com (DNS); regras tiradas dos resumos do WebSearch, dos ports (ProRealCode, mql5, Tradovate) e de LuxAlgo/StockCharts.
Nenhum dos scripts tem stop no original: todos usam stop de proteção k×ATR14 (exigido pelo motor). Todas as quatro reprovaram na validação, então **não houve refinamento** (o protocolo proíbe reajustar depois de ver a validação). A reserva não foi aberta.

## TV12_elder_impulse – Elder Impulse System
- Fonte: tradingview.com/script/Jut6HUJb, LuxAlgo, StockCharts ChartSchool.
- Regra: verde = EMA(n) e histograma MACD(12,26,9) sobem juntos; vermelho = caem juntos. Compra no 1º verde, vende no 1º vermelho; sai ao perder a cor ('blue') ou na cor oposta ('red').
- Calibrado: ema_n {8,13,21,34}, exit, k {2,3}, side; H1/H4/D1 (96 combinações).
- Escolhido D1 ema 21, exit=red, k=2, both. Dev: 159 trades, +95,3R, PF 3,48, DD 3,9R. Val: 65 trades, −0,25R, PF 0,99, DD 4,4R (stress −1,5R).
- Veredito: **REPROVADA_VALIDACAO**. Funcionou só no grande ciclo 2016–2020; em 2021–22 ficou no zero a zero.

## TV13_chaikin_osc – Chaikin Oscillator (cruzamento de zero)
- Fonte: Help Center do TradingView (43000501979), StockCharts ChartSchool.
- Regra: EMA(rápida) da linha A/D − EMA(lenta); compra no cruzamento acima de 0, vende abaixo, sai no cruzamento oposto.
- Calibrado: fast {3,6}, slow {10,20,30}, k {2,3,4}, side; 108 combinações.
- Escolhido H4 6/30, k=2, long. Dev: 141 trades, +224,5R, PF 4,34, DD 9,7R. Val: 92 trades, −4,35R, PF 0,89, DD 16,7R (stress −9,2R).
- Veredito: **REPROVADA_VALIDACAO**. O resultado do desenvolvimento era o beta da alta do BTC; fora dela, prejuízo.

## TV14_range_filter – Range Filter (DonovanWall)
- Fonte: tradingview.com/script/lut7sBgG (Range Filter DW); ports no ProRealCode/mql5 ("Range Filter Buy and Sell").
- Regra: faixa = EMA(EMA(|ΔF|,per),2per−1)×mult; filtro só anda quando o preço supera a faixa; sinal na troca de estado (CondIni), com F acima/abaixo do filtro e contador upward/downward > 0.
- Calibrado: per {25,50,100,200}, mult {2,3,4}, k {2,3}, side; 144 combinações.
- Escolhido H4 per 25, mult 3, k=2, long. Dev: 153 trades, +142,5R, PF 2,90, DD 6,0R. Val: 67 trades, −7,3R, PF 0,84, DD 23,3R (11,6% da conta; stress −10,6R).
- Veredito: **REPROVADA_VALIDACAO**. Também estourou o limite de DD de 10%.

## TV15_ssl_channel – SSL Channel (ErwinBeckers)
- Fonte: scripts SSL Channel w/alert (sm4zbLHp) e MTF (wC5DA3Wo) no TradingView; código v3 citado no fórum da Tradovate.
- Regra: Hlv = +1 se F > SMA(máximas,len), −1 se F < SMA(mínimas,len), senão mantém; compra/vende na virada do Hlv, sai na virada oposta.
- Calibrado: len {5,8,10,13,20,30}, k {1,5;2;3}, side; 108 combinações.
- Escolhido H4 len 30, k=2, long. Dev: 187 trades, +214,7R, PF 3,69, DD 6,2R. Val: 91 trades, −10,0R, PF 0,80, DD 23,0R (11,5%; stress −14,8R).
- Veredito: **REPROVADA_VALIDACAO**. É outro seguidor de tendência que só "funcionou" na alta de 2016–2020.

## Leitura geral
Os quatro scripts são seguidores de tendência (ou de momentum de volume) e repetem o padrão já visto em L01, L13, L14, TV04, TV20: PF altíssimo no desenvolvimento por causa da alta do BTC e PF < 1 em 2021–2022. Os DSR altos (0,98–1,0) mostram que a seleção não foi sorte entre as combinações, mas não protegem contra a mudança de regime.
