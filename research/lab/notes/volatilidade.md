# Agente volatilidade: notas (BTCUSD, protocolo lab-v1)

Custos: base 0,10% por lado, stress 0,20%. Números em R. Formato: trades / netR / PF / DD máx.

## L09_ttm_squeeze: TTM Squeeze (John Carter)
- **Fontes:** StockCharts ChartSchool (TTM Squeeze), LuxAlgo (TTM Squeeze) e Carter, *Mastering the Trade*.
- **Regra:** o squeeze está ligado quando a Bollinger(20,2) fica dentro do Keltner(EMA20 ± kc×ATR20). No disparo (o squeeze desliga), entra na direção do momentum de Carter. O momentum é a regressão linear de 20 candles do preço menos a média entre o ponto médio do Donchian 20 e a SMA20. Saída quando o momentum perde força por 2 candles ("fade") ou cruza o zero ("zero"). Stop stop_k×ATR.
- **Calibrado:** kc {1.25, 1.5, 2.0}, min_sq {1, 6}, exit, stop_k {1.5, 2.5}, side, em H1/H4/D1 (144 combinações).
- **Veredito: REPROVADA_VALIDACAO.** Escolhida H4 kc=1.5, min_sq=1, saída no zero, stop 1.5 ATR, só compra.
  - Desenvolvimento: 140 / +179,8 / 3,51 / 6,9.
  - Validação: 45 / −13,6 / 0,57 / 22,6 (stress −16,9).
  - DSR 0,0.
- **Leitura:** o resultado excelente em 2016–2020 vem do mercado de alta do BTC com stops curtos. Na validação (2021–22) o resultado inverteu, então não há vantagem demonstrada.

## L10_williams_volbreak: volatility breakout (Larry Williams)
- **Fontes:** LuxAlgo (Volatility Breakout) e Williams, *Long-Term Secrets to Short-Term Trading* (1999).
- **Regra:** dia em UTC. Nível = abertura do dia ± k×range do dia anterior. O primeiro fechamento H1/H4 do dia além do nível entra na abertura do candle seguinte. Escolha documentada: executar em H1/H4 em vez de D1, porque em D1 seria preciso supor entrada no meio do candle. Stop sf×range do dia anterior. Saída por tempo após hold_days dias.
- **Calibrado:** k {0.3, 0.5, 0.7, 0.9}, sf {0.5, 1.0}, hold_days {1, 2, 3}, side, em H1/H4 (96 combinações).
- **Veredito: REPROVADA_VALIDACAO.** Escolhida H1 k=0.7, sf=0.5, 2 dias, só compra.
  - Desenvolvimento: 318 / +328,0 / 2,62 / 12,3.
  - Validação: 125 / −9,1 / 0,90 / 18,7 (stress −25,3).
  - DSR 0,998.
- **Leitura:** a escolha não parece sorte da grade (DSR alto) e os vizinhos eram robustos. Mesmo assim, a vantagem dependia do regime de alta de 2016–20 e não sobreviveu a 2021–22.

## L11_nr7: NR7 (Toby Crabel)
- **Fontes:** QuantifiedStrategies (NR7), LuxAlgo (NR4/NR7) e Crabel, *Day Trading with Short Term Price Patterns and ORB* (1990). O livro não foi consultado diretamente.
- **Regra:** um candle NR7 tem o menor range entre os 7 últimos. Nos `window` candles seguintes, o primeiro fechamento além da máxima (ou mínima) do NR7 entra na abertura seguinte. Isso aproxima a ordem stop de Crabel. Stop no lado oposto do NR7 (mínimo 0,5 ATR) ou 1 ATR. Saída por tempo após `hold` candles.
- **Calibrado:** window {1, 2, 3}, hold {1, 3, 6}, stop {bar, atr}, side, em H1/H4/D1 (108 combinações).
- **Veredito: REPROVADA_VALIDACAO.** Escolhida D1 window=3, hold=6, stop ATR, só compra.
  - Desenvolvimento: 111 / +43,5 / 1,74 / 8,4.
  - Validação: 34 / −0,02 / 1,00 / 9,3 (stress −1,3).
  - DSR 0,0.
- **Leitura:** na validação o resultado ficou em zero. O DSR de 0 indica que a escolha no desenvolvimento provavelmente foi sorte.

## L12_keltner_breakout: rompimento do canal de Keltner
- **Fontes:** StockSharp (Keltner Channel Breakout), BabyPips (Keltner channel) e StockCharts ChartSchool (Keltner Channels).
- **Regra:** o fechamento cruza a EMA(n) ± k×ATR(n) e a entrada é na abertura seguinte. Saída quando o fechamento volta para o outro lado da EMA central. Stop stop_k×ATR(n).
- **Calibrado:** n {20, 50}, k {1.5, 2, 2.5, 3}, stop_k {1.5, 2.5, 3.5}, side, em H1/H4/D1 (144 combinações).
- **Veredito: CANDIDATA.** Escolhida H4 n=50, k=3.0, stop 1.5 ATR, compra e venda.
  - Desenvolvimento: 122 / +270,2 / 4,57 / 5,6.
  - Validação: 53 / +9,3 / 1,26 / 9,3 (stress +5,9, PF 1,15).
  - Reserva: 143 / +45,4 / 1,39 / **40,6** (stress +29,4, PF 1,23).
  - DSR 0,028, o que gera o aviso de provável sorte na seleção.
- **Leitura:** passou no histórico, mas com ressalvas fortes. O PF caiu de 4,6 para 1,3–1,4. O drawdown da reserva (40R, cerca de 20% a 0,5% de risco) é 7 vezes o do desenvolvimento. O resultado depende de poucas operações longas e grandes (stop curto, saída na média). O DSR baixo também sugere sorte na seleção. Antes de virar sinal, precisa de acompanhamento prospectivo e custo real. Não é estratégia aprovada.

## Observações sobre o motor e o protocolo
- Nenhum bug encontrado no motor. Conferi as operações da L12: os stops são curtos (~1% do preço em 2016 no H4), o que gera R grandes; as saídas são por sinal ou stop, coerentes.
- O desenvolvimento 2016–2020 favorece muito as entradas de compra em rompimento: PFs de 2,6 a 4,6 caíram para menos de 1,3 depois. O período escolhido para calibrar está num regime de alta forte.
- O DSR ficou em cerca de 0 para L09, L11 e L12 e em 0,998 para L10. A variância usada é a dos Sharpes de todas as combinações, que misturam tempos gráficos e lados diferentes. Além disso, a escolha é feita por netR/DD e não pelo Sharpe máximo. Os dois fatores podem deixar o DSR muito baixo mesmo com t alto. Vale revisar no protocolo, mas não mexi.
- Não houve refinamentos: as três reprovadas já tinham a validação aberta, e o protocolo proíbe reajustar depois disso.
