# r6-zonas — Rodada 6, bloco 11 (osciladores de zona)

Ativo BTCUSD, protocolo lab-v3. Nenhum refinamento: as três reprovadas já tinham aberto a validação (o protocolo proíbe reajuste).

## TV76 Volume Zone Oscillator (Khalil/Steckler; LazyBear)
- Fonte: TASC mai/2011 (traders.com/Documentation/FEEDbk_docs/2011/05/Khalil.html) e Traders' Tips mai/2011 (código _VZO_Strategy da TradeStation com as regras); thinkorswim VolumeZoneOscillator; script TradingView P6bSDkjh.
- Regra: VZO = 100·EMA(±volume)/EMA(volume). ADX14 > adx = tendência; com preço > EMA60 compra ao cruzar acima de -40 ou de 0, sai ao cruzar abaixo de 60 ou com preço < EMA60 e VZO < 0 (venda espelhada). Sem tendência: compra ao cruzar acima de -40/+15, vende abaixo de +40/-5. Sem as saídas por divergência. Stop de proteção k·ATR14 (o script não tem).
- Grade: n {10,14,21}, adx {15,18,22}, k {2,3}, side {long,both}; H1/H4/D1 (108 combinações).
- Veredito: **REPROVADA_VALIDACAO**. D1 n=21 adx=18 k=2 long. Dev 41 trades, +62,1R, PF 5,23, DD 3,2R (4/5 anos). Val 11 trades, -0,56R, PF 0,89.
- Interpretação: em D1 são poucos trades (8/ano) e o PF 5 do desenvolvimento era a alta do BTC 2016–2020; em 2021–22 sumiu.

## TV77 Price Zone Oscillator (Khalil/Steckler; LazyBear)
- Fonte: TASC jun/2011 (traders.com/Documentation/FEEDbk_docs/2011/06/Khalil.html); thinkorswim PriceZoneOscillatorLE/SX (mesmas zonas do VZO).
- Regra: igual ao TV76 com o fechamento no lugar do volume.
- Grade: igual ao TV76 (108).
- Veredito: **REPROVADA_VALIDACAO**. D1 n=21 adx=15 k=2 both. Dev 51 trades, +66,7R, PF 5,14, DD 3,8R. Val 19 trades, -1,17R, PF 0,90.
- Interpretação: mesmo quadro do VZO; o volume não acrescenta nada em relação ao preço, e nenhum dos dois se manteve fora da amostra.

## TV78 CM Stochastic POP (Bernstein; ChrisMoody)
- Fonte: port do Pine "CM_Stochastic POP Method 1" (deepentropy/lightweight-charts-indicators, src/community/stoch-pop-1.ts); LuxAlgo library "Stochastic Pop" (Bernstein; filtro ADX<20 de Steckler).
- Regra: %K = SMA5 do estocástico de klen; compra quando %K cruza acima de U, vende quando cruza abaixo de 100-U; sai ao voltar para dentro da zona. Filtro opcional ADX14 anterior < 20. Stop k·ATR14. Zonas simétricas (o script usa 60/30 por padrão).
- Grade: klen {8,14,21}, U {60,70,80}, adx_max {20, sem}, k {2,3}, side; 216 combinações.
- Veredito: **REPROVADA_VALIDACAO**. H4 klen=21 U=70 sem ADX k=2 both. Dev 505 trades, +166R, PF 1,92, DD 8,9R (5/5 anos, DSR 0,73). Val 237 trades, -35R, PF 0,68, DD 36R.
- Interpretação: o momento de curto prazo funcionou em 2016–2020 e virou perda forte em 2021–22, a mesma armadilha da rodada 5.

## TV79 Derivative Oscillator (Constance Brown; everget)
- Fonte: Pine original everget (github.com/everget/tradingview-pinescript-indicators, oscillators/derivative_oscillator.pine); TC2000 help "Derivative Oscillator"; script TradingView 6wfwJ6To.
- Regra: sRSI = EMA3(EMA5(RSI)); DOSC = sRSI - SMA9(sRSI). Compra quando o DOSC cruza acima de 0 (ou da linha de sinal); filtro de regime opcional EMA(trend); o cruzamento oposto fecha. Stop k·ATR14.
- Grade: rsi {9,14,21}, trig {zero,signal}, trend {0,100,200}, k {2,3}, side; 216 combinações.
- Veredito: **CANDIDATA** (só no histórico do BTC). H4 rsi=14 zero trend=200 k=2 **long**. DSR 0,98.
  - Dev: 313 trades, +115R, PF 2,10, DD 6,3R (3,2%), 4/5 anos.
  - Val: 78 trades, +8,4R, PF 1,34, DD 7,3R; stress +4,6R; sem a maior +5,3R.
  - Reserva: 217 trades, +41,9R, PF 1,48, DD 11,0R (5,5%); stress +22,4R.
  - Placebo (20 sorteios): mediana dev +48R PF 1,51 (0/20 ≥ real); val -5,9R PF 0,79 (3/20); reserva +1,5R PF 1,02 (0/20).
  - Teste cruzado (mesmos parâmetros): EURUSD reprova (dev +13,2R PF 1,20; val +2,6R PF 1,06; reserva +1,0R PF 1,02); USDJPY reprova (dev +1,5R PF 1,02; val +12,1R PF 1,31; reserva -3,1R PF 0,88).
- Interpretação: é "só compra" acima da EMA200, e cerca de 40% do lucro do desenvolvimento o placebo também tem (efeito de estar comprado na alta). Na validação e na reserva ela bate o placebo com folga, mas a validação é fraca (t=0,97) e a regra não se sustenta no câmbio. Merece acompanhamento só no BTC, não é estratégia aprovada.
