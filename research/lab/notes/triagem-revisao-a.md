# Revisão da triagem: agente a

Data: 23/10/2026. Regras: philakone-ema-swing H4, kalman-hull-kijun D1, sma-dma-crossing-signal D1, adaptive-friction-filter D1, traders-reality-main D1, zero-lag-garch-bands-nal D1.

## Como foi feito

- **Pine original:** não achei o código de nenhum dos seis em /home/user/labdata/pine/ nem no GitHub (a busca de código do GitHub está bloqueada nesta sessão e a web não mostra repositório com esses scripts). As páginas do TradingView abrem só com a descrição, sem o código. Por isso comparei cada .ts com a descrição pública do autor.
- **Dado futuro:** li o código. Fiz também um checar_lookahead no estilo do outro laboratório (`research/ferramentas/estatistica.py` no ramo j6qdm4): 40 cortes ao acaso no BTCUSD, e o sinal (compra, venda ou nada) no último candle do corte tem que ser igual ao do histórico completo. Deu 0 divergências nas 6 regras.
- **Vizinhos:** rodei `vizinhos.py`. Ele também varia entradas que não mudam o sinal (lineWidth, transparências, offsets de rótulo, SMAs 30/50/100/200 que só aparecem no desenho), e essas variantes dão sempre o mesmo resultado do padrão. Por isso contei só os parâmetros que entram no sinal.
- **Parâmetros fixos no código:** fiz uma cópia do bundle em `research/cache/lab/tri/lci_rev_a.mjs` em que os comprimentos fixos leem `REV_A` (o clone não foi editado). Os scripts estão no scratchpad `rev_a/` (`viz_manual.py`, `garch_regime.mjs`, `look.mjs`). Variei assim:
  - Philakone: as EMAs 8, 13, 21 e 55, ±20%.
  - Traders Reality: a janela de 10 candles e o multiplicador de volume 2×, ±20%.
  - SMA DMA: confirmBars=1 e 3, porque ±20% de 2 arredonda para 2.
- **Duplicatas:** comparei a posição (compra ou venda) candle a candle com as outras regras que passaram, no mesmo TF. Nenhuma das seis é duplicata: a maior concordância é 0,92 (kalman-hull-kijun com sma-dma-crossing-signal). Todas são seguidoras de tendência e por isso concordam 0,7 a 0,9 com as outras dessa família.

## philakone-ema-swing H4 | Buy Condition / Sell Condition

- **Fonte:** "Philakone 55 EMA Swing Trading", de prosum_solutions (TradingView tOKp5kg4). O código não foi encontrado. A descrição fala da estratégia da 55 EMA, com alertas Buy/Sell Condition e plotshape.
- **Port:** compra quando a EMA 21 cruza a 55 com EMA8>EMA13 e EMA21>EMA55; venda é o espelho. Bate com a descrição. A versão Pine tem opção de outro tempo gráfico, que não é usada no padrão.
- **Dado futuro:** não há. O cruzamento usa só i e i-1.
- **Vizinhos (8 variantes: 8, 13, 21 e 55, ±20%):** BTC 3/8, ETH 7/8, SOL 3/8. No BTC, a EMA 21=17 e a EMA 55=44 ou 66 deixam a validação negativa.
- **Veredito: DUVIDOSA.** Os vizinhos só passam na maioria em um ativo (ETH), e o resultado depende de 21/55 exatos.

## kalman-hull-kijun D1 | Kalman Hull Kijun Long / Short

- **Fonte:** "Kalman Hull Kijun [BackQuant]" (TradingView 0E5xrn6O). O código não foi encontrado. A descrição é: Kalman, depois passo tipo Hull, depois o ponto médio de Donchian no período Kijun. Os alertas são de **estado** (o preço acima ou abaixo da base) e, segundo o autor, servem como regime, não como gatilho.
- **Port:** segue a descrição. O estado do Kalman é compartilhado entre as 4 chamadas do candle, como com o `var` array do Pine.
- **Dado futuro:** não há.
- **Ressalva da triagem:** como o alerta vale em todo candle, o backtest volta a entrar logo no candle seguinte a um stop. Na prática a regra é "preço acima ou abaixo da base" com stop de 2×ATR.
- **Vizinhos (6 que importam):** BTC 6/6, ETH 6/6, SOL 4/6.
- **Veredito: APROVADA_REVISAO.**

## sma-dma-crossing-signal D1 | BUY indication / SELL indication

- **Fonte:** "SMA DMA Crossing Signal / SMA DMA Market Signals", de tradingqueen18 (TradingView nVVlLRkq). O código não foi encontrado. As notas de versão descrevem o que o .ts faz:
  - compra no cruzamento da DMA rápida (SMA 28) sobre a lenta (SMA 28 deslocada 14);
  - 2 fechamentos de confirmação, buffer de 0,25×ATR e DMA rápida subindo;
  - compra de recuperação depois de uma venda;
  - venda por fraqueza do preço ou cruzamento de baixa;
  - sinais só em candle fechado, alternando compra e venda.
- **Ressalvas:**
  - O autor chama a SELL de "indicação de fraqueza" (sair ou vender). A triagem a usa como entrada vendida.
  - Na descrição de 2024, a DMA lenta lê o D1 por padrão. Em D1 isso é igual ao gráfico.
- **Dado futuro:** não há. `slow` usa i-14, e com chart indefinido todos os candles contam como fechados.
- **Vizinhos (12 que importam, contando confirmBars 1 e 3):** BTC 11/12, ETH 10/12, SOL 7/12.
- **Veredito: APROVADA_REVISAO.**

## adaptive-friction-filter D1 | Bullish Trend Signal / Bearish Trend Signal

- **Fonte:** "Adaptive Friction Filter (AFF) [QuantAlgo]". Não achei o código nem a página do script.
- **Port:** a linha só anda quando |src-linha| passa de 1,5×SMA20(|Δsrc|), e então anda 0,5 da distância. Os alertas marcam a virada da direção da linha. É coerente com o nome e a descrição do .ts, mas não deu para conferir com o Pine.
- **Dado futuro:** não há.
- **Vizinhos (6: frictionMult, catchupScalar e lookback, ±20%):** BTC 1/6, ETH 2/6, SOL 6/6. No BTC e no ETH quase todos ficam com netR positivo, mas falham na validação (PF ou netR perto de 0).
- **Veredito: DUVIDOSA,** perto de reprovar. No BTC praticamente só o padrão passa.

## traders-reality-main D1 | Green Vector Candle / Red Vector Candle

- **Fonte:** "Traders Reality Main" (TradingView Etj1ixAs). O código não foi encontrado. A documentação da `Traders_Reality_Lib.calcPvsra` (TradingView 8zgJTM9u) dá a regra:
  - vela de clímax: volume ≥ 200% da média dos 10 candles anteriores, ou spread×volume ≥ o maior dos 10 anteriores;
  - verde se for de alta, vermelha se for de baixa.
- **Port:** o .ts faz exatamente isso, com a média e o máximo sobre i-1..i-10.
- **Dado futuro:** não há. A parte de sessões e níveis diários não entra nesse alerta.
- **Ressalva:** a regra depende do volume da fonte (Bitstamp para BTC, Binance para ETH e SOL). Os volumes são completos, com 3 dias sem volume no BTC.
- **Vizinhos:** os 26 de `vizinhos.py` são todos cosméticos. Os manuais (janela 8/12 e multiplicador 1,6/2,4) dão BTC 4/4, ETH 3/4, SOL 3/4. Só k=1,6 falha, no ETH e no SOL.
- **Veredito: APROVADA_REVISAO.**

## zero-lag-garch-bands-nal D1 | fechamento x linha 1

- **Fonte:** "Zero-Lag GARCH Bands | NAL" (TradingView UJgbKLG3). O código não foi encontrado. Na descrição, o autor diz: estado de alta quando fecha acima da banda superior, de baixa quando fecha abaixo da inferior, e mantém o estado entre as bandas. O script não tem alertcondition.
- **Port:** segue isso (`score` muda a cor das bandas). Não há dado futuro: a busca dos pesos GARCH usa só a janela até i, e a ZLEMA usa i-lag.
- **Regra genérica:** a linha 1 é o plot0, a **banda superior**. A regra testada é: compra quando o fechamento cruza acima da banda superior, venda quando volta abaixo dela. A compra coincide com o sinal de alta do autor. A venda não, porque o autor só fica de baixa abaixo da banda **inferior**. Logo, é um artefato da triagem: um rompimento da banda superior com saída e inversão ao voltar para dentro.
- **Vizinhos da regra genérica (8):** BTC 5/8, ETH 5/8, SOL 7/8.
- **Regra do autor (troca de regime, `garch_regime.mjs`):** no padrão, reprova no BTC (validação −2R) e no ETH e no SOL ("poucas operações"). Os vizinhos dão BTC 0/8, ETH 2/8, SOL 0/8.
- **Veredito: DUVIDOSA.** O que passa não é o sinal do autor, e o sinal do autor reprova. Se ficar, tem que ser registrada como uma estratégia nova (rompimento da banda superior), não como o indicador do autor.

## Problemas na triagem ou nas ferramentas (não corrigi)

1. `vizinhos.py` conta variantes cosméticas (largura de linha, transparência, offsets, comprimentos só desenhados), o que infla o resumo: o traders-reality-main sai 26/26 sem ter testado nada do sinal. Ele também não varia inteiros pequenos, porque 2×0,8 e 2×1,2 arredondam para 2, nem constantes fixas no código. Sugestão: descartar a variante quando os sinais ficam idênticos aos do padrão e avisar quando sobram 0 variantes.
2. Com alertas de estado, como o do Kalman, o backtest entra em todo candle, então volta a entrar logo depois de um stop. Não é bug, mas a regra vira um regime, e isso precisa estar claro no laboratório completo.
3. A regra genérica "fechamento x linha 1" pega o primeiro plot, seja qual for o significado dele (no GARCH é a banda superior, não a linha do meio).
4. Incidente meu: no começo rodei `pkill -f vizinhos.py`, que pode ter interrompido rodadas de vizinhos de outros agentes que estavam ativas naquele instante. Quem tiver um log de vizinhos cortado deve rodar de novo.
