# r4-trailing — Rodada 4, bloco 1 (trailing adaptativo): TV36–TV39

Ativo BTCUSD, protocolo lab-v2. Código lido em /home/user/labdata/pine/deepentropy_lightweight-charts-indicators/src/community/ (ports fiéis do Pine). Nenhum dos scripts tem stop: em todos usei stop de proteção k×ATR14 (Wilder), saída/inversão no sinal oposto. Nenhum repinta. Sinais só a partir do candle 200 (aquecimento dos laços recursivos). Nenhuma passou o desenvolvimento e reprovou nele, então não houve refinamento (as reprovadas já tinham aberto a validação: o protocolo proíbe reajuste).

## TV36_ott — Optimized Trend Tracker (KivancOzbilgic / Anıl Özekşi)
- Fonte: https://www.tradingview.com/script/zVhoDQME/ ; código DE `optimized-trend-tracker.ts`.
- Regra: VAR (VIDYA com |CMO 9|) e OTT (stop percentual que só aperta, ×(200±pct)/200). Compra quando a VAR cruza acima da OTT de 2 candles atrás; venda no inverso.
- Grade: período 2/5/10/20, percentual 0,7/1,4/2,8/5,0, k 2/3, lado long/both; H1/H4/D1 (192).
- Veredito: **REPROVADA_VALIDACAO**. Escolhida H4 período 10, 5%, k 2, só compra.
- Dev 75 trades, +242,9R, PF 6,74, DD 6,2R | Val 33 trades, −10,9R, PF 0,59, DD 13,8R (stress −12,5R).
- Leitura: excelente no bull de 2016–2020, perde em 2021–22. É o padrão de quase todo seguidor de tendência long-only em BTC deste laboratório.

## TV37_alphatrend — AlphaTrend (KivancOzbilgic)
- Fonte: https://www.tradingview.com/script/o50NYLAZ-AlphaTrend/ ; código DE `alpha-trend.ts`.
- Regra: linha = mínima − SMA(TR)×coef se MFI≥50 (ou RSI), senão máxima + ATR×coef, só anda a favor. Compra quando AT cruza acima de AT[2], com o filtro de alternância do script (O1>K2); venda no espelho.
- Grade: coef 0,5/1/1,5/2, período 7/14/21, filtro mfi/rsi, k 2/3, lado; H1/H4/D1 (288).
- Veredito: **REPROVADA_VALIDACAO**. Escolhida H4 coef 1,5, período 14, MFI, k 2, só compra.
- Dev 80 trades, +252,4R, PF 6,36, DD 9,2R | Val 30 trades, −7,7R, PF 0,67, DD 14,8R (stress −9,3R).
- Leitura: o mesmo comportamento do TV36. O filtro MFI não protegeu na queda de 2021–22.

## TV38_follow_line — Follow Line Indicator (Dreadblitz)
- Fonte: https://www.tradingview.com/script/29iYBNku-Follow-Line-Indicator/ (espelho it.tradingview.com/script/RwHWOeMU); código DE `follow-line.ts`.
- Regra: fechamento acima da Bollinger(n, desvio) leva a linha para mínima − ATR(5) sem nunca descer; abaixo da banda inferior, o espelho. Compra quando a linha vira para cima, venda quando vira para baixo. O ATR(5) é uma RMA calculada só nos candles de rompimento, como no Pine.
- Grade: BB 14/21/34, desvio 0,75/1/1,5, filtro ATR desligado/ligado, k 2/3, lado; H1/H4/D1 (216).
- Veredito: **REPROVADA_VALIDACAO**. Escolhida H4 BB 34, desvio 0,75, sem ATR, k 2, só compra.
- Dev 143 trades, +229,2R, PF 4,47, DD 5,8R | Val 77 trades, −17,1R, PF 0,68, DD 27,3R (13,7%, acima do limite de 10%).
- Leitura: foi a pior na validação. O DD passou do limite de perda total.

## TV39_smoothed_ha — Trend Indicator A-V2 (DZIV)
- Fonte: https://www.tradingview.com/scripts/dziv/ e cópia do código v2.3 em https://www.mql5.com/en/job/250638 ; código DE `trend-indicator-a-v2.ts`.
- Regra: Heikin Ashi do próprio tempo gráfico, EMA(n) da abertura HA e EMA(n) do fechamento HA. Compra quando a EMA do fechamento cruza acima da EMA da abertura (nuvem fica verde); venda no inverso.
- Grade: n 5/9/14/21/30, k 1,5/2/3, lado long/both; H1/H4/D1 (90).
- Veredito: **CANDIDATA**. Escolhida D1 n 21, k 1,5, compra e venda. DSR 0,95; PF dos vizinhos 4,26.
- Dev 111 trades, +133,2R, PF 4,26, DD 4,75R (2,4%).
- Val 45 trades, +5,9R, PF 1,29, DD 6,3R (3,1%); stress +4,7R; sem a maior operação só +1,6R (stress +0,5R): **passou raspando**.
- Reserva 84 trades, +34,8R, PF 1,83, DD 7,3R (3,7%); stress +31,3R; sem a maior +22,5R.
- Placebo (mesmas saídas, stop e lados; entradas embaralhadas no tempo dentro de cada fase; 20 sorteios; semente 12345). Mediana de netR/PF: dev +33,5R / 1,80; val −3,4R / 0,81; reserva +0,4R / 1,01. Placebo ≥ real: 0/20 no dev, 3/20 na val e 0/20 na reserva.
- Leitura: a regra bate o placebo com folga no dev e na reserva. Na validação a margem é fina: 3 de 20 placebos empataram ou ganharam, e o resultado depende de poucas operações. Atenção: as saídas do placebo ainda são a troca de cor da própria regra, então parte do ganho do placebo vem da saída. É CANDIDATA, não estratégia aprovada. Falta acompanhamento prospectivo, outro ativo e custos reais. Também é parente do L13 (Heikin Ashi) e do TV90 (Open Close Cross): conferir a correlação de sinais antes de somar.

Script do placebo: /tmp/claude-0/-home-user-tradernova/d6b2f965-ed66-506f-874a-a205f7b4083c/scratchpad/r4t/placebo.py (fora do repo).
