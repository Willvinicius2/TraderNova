# Rodada 2: tv-embutidas-c (embutidas do TradingView: MACD, Parabolic SAR, Technical Ratings)

Ativo BTCUSD, protocolo lab-v2. As três reprovaram na **validação** (2021-2022). Pelo protocolo, nenhuma foi refinada depois disso.
O WebFetch não alcançou tradingview.com nem oanda.jp (erro de DNS). As regras saíram dos resumos do WebSearch (Help Center do TradingView e OANDA lab-education) e do código Pine público das embutidas.

## TV09_macd: MACD Strategy
- **Fonte:** Help Center "Built-in strategies" e o artigo da OANDA lab-education (pine_script_macd_strategy).
- **Regra:** delta = MACD - sinal. Compra quando delta cruza acima de zero e vende quando cruza abaixo, invertendo a posição. O Pine não tem stop, então usei um stop de proteção k×ATR(14).
- **Calibrado:** rápida 8/12/16, lenta 21/26/34, sinal 7/9/11, k 2/3, lado só compra ou os dois, em H1/H4/D1 (324 combinações).
- **Escolhido:** H4, 16/34/11, k=2, só compra. DSR 0,99.
- **Desenvolvimento:** 319 trades, +160,3R, PF 2,30, DD 4,5%.
- **Validação:** 138 trades, -10,3R, PF 0,84, DD 10,4%, sem a maior operação -16,8R, stress -17,4R. **REPROVADA_VALIDACAO.**
- **Interpretação:** seguiu bem a alta de 2016-2020 do BTC, mas perdeu no ciclo de 2021-2022. Na prática é um filtro de tendência de alta, sem vantagem própria.

## TV10_parabolic_sar: Parabolic SAR Strategy
- **Fonte:** TradingView Help Center 43000645065 (Parabolic SAR Strategy) e a lógica do Pine embutido.
- **Regra:** SAR de Wilder replicado do Pine. A virada do SAR gera a entrada na abertura seguinte. O Pine executa a ordem stop no nível do SAR, dentro do candle; aqui a entrada é aproximada para a abertura seguinte. A saída usa o próprio SAR como stop móvel, tocado dentro do candle.
- **Calibrado:** start 0,01/0,02/0,03, incremento 0,01/0,02/0,03, máximo 0,1/0,2/0,3, lado, em H1/H4/D1 (162 combinações).
- **Escolhido:** H4, 0,03/0,01/0,1, só compra. DSR 0,996.
- **Desenvolvimento:** 340 trades, +144,9R, PF 2,30, DD 3,9%.
- **Validação:** 161 trades, -15,5R, PF 0,77, DD 10,1%, stress -23,6R. **REPROVADA_VALIDACAO.**
- **Interpretação:** é o mesmo padrão do MACD. Rende muito no período de alta e devolve tudo no período lateral ou de baixa.

## TV11_technical_ratings: Technical Ratings Strategy ("Technicals Strategy")
- **Fonte:** TradingView Help Center 43000628415 (a estratégia) e 43000614331 (o rating), o indicador aberto "Technical Ratings" e o artigo da OANDA.
- **Regra:** 15 médias e 11 osciladores, cada um valendo +1/0/-1, conforme as regras do código Pine aberto. Reproduzi de memória do código público, porque não consegui abrir a página. A nota final é a média dos dois grupos.
  - Strong Buy (> thr) abre compra e Strong Sell abre venda.
  - Stop de 3×ATR(14).
  - Stop móvel: ativa quando o lucro chega a act×ATR e fica 2×ATR atrás do melhor preço. É recalculado no fechamento; no Pine é dentro do candle.
- **Calibrado:** grupo (todos, médias, osciladores), thr 0,4/0,5/0,6, ativação do stop móvel 3/5/7 ATR, lado, em H1/H4/D1 (162 combinações).
  - O grupo "osciladores" nunca passa de 0,4 e não gerou operações.
- **Escolhido:** H4, só médias, thr 0,6, ativação 7 ATR, só compra. DSR 0,955.
- **Desenvolvimento:** 206 trades, +99,4R, PF 2,40, DD 3,1%.
- **Validação:** 72 trades, -4,7R, PF 0,85, DD 5,2%, stress -7,3R. **REPROVADA_VALIDACAO.**
- **Interpretação:** perdeu menos que as outras duas, mas também falhou. A combinação escolhida é um "comprar acima das médias", que só funcionou no mercado de alta.

## Observação geral
Nas três, a melhor combinação do desenvolvimento ficou só no lado comprado, com PF perto de 2,3. Isso reflete a alta forte do BTC em 2016-2020, não uma vantagem da regra. A validação desmentiu esse resultado.
