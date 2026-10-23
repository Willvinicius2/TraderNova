# r6-nnfx: rodada 6, bloco 12 (sistemas estilo NNFX), BTCUSD, protocolo lab-v3

Todas sem refinamento. Três reprovaram na validação, e o protocolo proíbe refinar depois disso. Grade de 144 combinações (48 × H1/H4/D1) em cada uma.
Nenhum dos quatro indicadores tem stop no Pine, então todos usam um stop de proteção de k × ATR14.
Números no formato trades / netR / PF / DD% (0,5% de risco por operação), custo base.

## TV80 SSL Hybrid (Mihkel00)
- Fonte: tradingview.com/script/FyW6Gz4r-SSL-Hybrid, prorealcode.com (ssl-hybrid-indicator). A lógica foi lida no port fiel do deepentropy (`ssl-hybrid.ts`).
- Regra: baseline HMA(len) com canal ±0,2×EMA(TR,len). Entra quando o fechamento sai do canal com a continuação SSL2 (JMA5, até 0,9×ATR) confirmando. Sai quando o fechamento cruza a SSL3 de saída, uma HMA(len3).
- Calibrado: len {30,45,60,90}, len3 {10,15,25}, k {1,5; 2,5}, lado {long, both}.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida H4 len=90, len3=25, k=2,5, só compra. DSR 0,86.
- Desenvolvimento: 384 / +66,6R / 1,65 / 5,1%, positiva em 4 de 5 anos. Validação: 163 / −14,8R / 0,70 / 8,7%, stress −21,7R.
- Interpretação: comprar o rompimento da baseline funcionou na alta de 2016–2020 e perdeu em 2021–2022.

## TV81 Traders Dynamic Index (Dean Malone; script Goldminds/thienlovv)
- Fonte: luxalgo.com/library/concept/traders-dynamic-index, earnforex (TDI). Também o port `tdi-rsi.ts` do deepentropy.
- Regra: RSI com linha de preço SMA2, linha de sinal SMA7 e bandas BB(34; 1,6185). Entra quando a linha de preço cruza a de sinal, acima de 50 e dentro das bandas. Com base=1, exige também a linha base (SMA34 do RSI) acima de 50. Sai no cruzamento oposto ou, com exit=base, quando a linha de preço cruza a base.
- Calibrado: rsi {8,13,21}, base {0,1}, exit {cross, base}, k {2,3}, lado {long, both}.
- Veredito: **CANDIDATA**. Escolhida H4 rsi=21, base=1, exit=base, k=3, **só compra**. DSR 0,998. Mediana do PF dos vizinhos: 1,93.
- Desenvolvimento: 240 / +75,8R / 2,23 / 2,7%, positiva em 5 de 5 anos.
- Validação: 69 / +4,0R / 1,22 / 2,4%. No stress, +1,6R. Sem a maior operação, só +1,5R.
- Reserva: 179 / +21,2R / 1,39 / 4,7%. No stress, +10,6R.
- Placebo (20 sorteios com as entradas embaralhadas e as mesmas saídas, stop e lado), mediana:
  - desenvolvimento +60,0R (PF 1,78), real à frente em 19 de 20;
  - validação −4,6R (PF 0,82), real à frente em 20 de 20;
  - reserva +24,4R (PF 1,39), igual ou melhor que o real em 14 de 20.
- Teste cruzado com os mesmos parâmetros, sem recalibrar:
  - EURUSD reprova: desenvolvimento +0,4R com PF 1,01, validação −2,9R, reserva −17,9R.
  - USDJPY reprova no desenvolvimento (+7,2R, PF 1,14, abaixo de 1,15). A validação (+12,5R, PF 1,52) e a reserva (+3,7R, PF 1,23) passariam.
- Interpretação honesta: a seleção ficou "só compra". Entradas ao acaso, com a mesma saída pela linha base, ganham quase o mesmo no desenvolvimento e na reserva. A maior parte do resultado vem de ficar comprado com saída lenta na alta do BTC, não do cruzamento do TDI. A validação passou por margem pequena e não se repetiu no EURUSD. Não é estratégia aprovada.

## TV82 Absolute Strength Index (Zeiierman)
- Fonte: tradingview.com/scripts/asi (resumo de busca) e o port `absolute-strength-index.ts` do deepentropy.
- Regra: o retorno de L candles é normalizado entre os percentis 85% e 15% dos L retornos de 1 candle anteriores, numa escala de −1 a +1. Entra quando o ASI cruza a SMA(ma) do próprio ASI e sai no cruzamento oposto.
- Calibrado: L {10,15,25,40}, ma {7,14,21}, k {2,3}, lado {long, both}.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida D1 L=25, ma=21, k=2, só compra. DSR 0,97.
- Desenvolvimento: 92 / +67,3R / 3,81 / 2,6%, positiva em 4 de 5 anos. Validação: 40 / −2,2R / 0,81 / 2,7%, stress −2,9R.
- Interpretação: o PF alto no desenvolvimento era o momentum da alta. Ele desaparece em 2021–2022.

## TV83 Trendilo (dudeowns)
- Fonte: jp.tradingview.com/script/h5kMWewu-Trendilo-OPEN-SOURCE e o port ProBuilder em prorealcode.com/prorealtime-indicators/trendilo.
- Regra: pch = variação % de 1 candle; avpch = ALMA(pch, len, 0,85, 6); banda = bmult × RMS(avpch, len). Comprado quando avpch passa acima de +banda, vendido abaixo de −banda. Sai ao voltar para dentro da banda (exit=neutral) ou só no estado oposto (exit=flip).
- Calibrado: len {20,35,50,80}, bmult {0,8; 1,0; 1,2}, exit {neutral, flip}, k=2,5, lado {long, both}.
- Veredito: **REPROVADA_VALIDACAO**. Escolhida H1 len=80, bmult=1,2, exit=flip, k=2,5, só compra. DSR 0,99.
- Desenvolvimento: 183 / +348,1R / 3,99 / 4,4%, positiva em 5 de 5 anos. Validação: 90 / −8,5R / 0,87 / DD 14,2%, stress −17,4R.
- Interpretação: o resultado enorme no desenvolvimento vinha de segurar a compra até o estado oposto durante a alta. Na validação o DD passou de 10%.

## Observações
- Em todas as quatro, a melhor combinação do desenvolvimento foi "só compra", mesmo com "both" na grade e com o filtro de 4 em 5 anos.
- Não achei bug no motor.
- Aproximações:
  - TV80: a EMA(TR, len) começa sem SMA inicial (pandas ewm, adjust=False). A diferença para o Pine é pequena e só aparece no aquecimento.
  - TV82: o stop k × ATR substitui o stop ausente no Pine. Isso vale também para as outras três.
