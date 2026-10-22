# Rodada 5 (22/10/2026): blocos 5 a 8 da fila do TradingView

16 scripts do TradingView (TV52–TV67) em 4 agentes, no BTCUSD, com o protocolo lab-v3. Além das regras do lab-v2, o desenvolvimento precisa ser positivo em pelo menos 4 dos 5 anos (2016–2020).

## Resultado

**0 candidatas.** 14 reprovaram na validação e 2 na reserva: TV54 Ease of Movement e TV63 Mass Index.

| Agente | Estratégias | O que aconteceu |
|---|---|---|
| r5-volume | TV52 Klinger, TV53 CMF, TV54 Ease of Movement, TV55 NVI | TV54 passou na validação (+3,6R, PF 1,37), mas ficou no zero a zero na reserva (+0,4R, PF 1,02, negativa no custo stress). TV52 ficou com PF 1,152 na validação, logo abaixo do mínimo. TV53 e TV55 eram "só compra" e quebraram em 2022. |
| r5-elder-williams | TV56 Elder-Ray, TV57 Force Index, TV58 AO saucer, TV59 Accelerator | TV56 e TV57 ficaram positivas na validação só por uma operação grande cada. TV58 e TV59 ganhavam só por estar compradas na alta. |
| r5-reversao-curta | TV60 Connors RSI, TV61 Double 7's, TV62 %b de Connors, TV63 Mass Index | TV60 e TV62 precisaram de refinamento para passar no desenvolvimento e depois perderam na validação. TV63 passou na validação e perdeu −10R na reserva. O DSR baixo (0,03 a 0,06) indica sorte na seleção. |
| r5-padroes | TV64 Three Bar Reversal, TV65 N Bar Reversal, TV66 Pin Bar Magic, TV67 Rally-Base-Drop | Todas reprovaram na validação: perto de zero, dependentes da maior operação ou com perda. |

## Correção no critério anual (calibrate.py)

Dois agentes notaram uma falha: o critério de 4 dos 5 anos contava as operações pelo ano de saída. Por causa disso:

- A saída forçada em 01/01/2021 virava um 6º ano dentro do desenvolvimento.
- Um ano sem nenhuma saída simplesmente não era contado.

Agora a contagem considera só os anos de 2016 a 2020. A saída forçada conta em 2020, e um ano sem saída conta como não positivo. As 16 estratégias e os refinamentos foram recalculados com a correção, e nenhum veredito mudou.

## Placar acumulado (laboratório)

| Item | Valor |
|---|---|
| Estratégias testadas | 87 |
| Candidatas (rodadas 1–4) | 6: L04, L07, L12, TV21, TV32, TV39 |
| Aprovadas | 0 |

Nenhuma candidata passou no teste cruzado com EURUSD (`results/_cross_EURUSD.json`).

## Segundo ativo: USDJPY (2007 a jun/2018)

Ticks Dukascopy de FX-Data/FX-Data-USDJPY-DS. Ouro, índices e outras criptos não têm fonte acessível com ~10 anos. Nenhuma das 6 candidatas passou nas 3 fases (`results/_cross_USDJPY.json`): todas reprovam na reserva (jul/2016 a jun/2018), sempre negativas sem a maior operação.
