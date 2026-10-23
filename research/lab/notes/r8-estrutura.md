# r8-estrutura (rodada 8, lab-v4, BTCUSD)

Nenhuma das quatro passou: todas REPROVADA_VALIDACAO. A reserva não foi aberta. Pelo protocolo, uma estratégia que já viu a validação não pode ser refinada, então não há _r1/_r2.

## L33_chandelier — Chandelier Exit (LeBeau) como sistema
- Fontes: StockCharts ChartSchool (Chandelier Exit) e o Pine everget "Chandelier Exit" (porte em /home/user/labdata/pine/deepentropy.../chandelier-exit.ts).
- Regra: linha de compra = maior máxima (ou fechamento) de n − mult·ATR(n); linha de venda no espelho. As linhas só apertam. A direção vira quando o fechamento cruza a linha oposta. exit=flip para e inverte; exit=trail usa a linha como stop móvel, que é o uso original de LeBeau.
- Diferença do L01 Supertrend: a âncora é o extremo de n candles, não o (máx+mín)/2 do candle. Diferença do TV10 SAR: não há aceleração. É parente próximo do Supertrend, mas a regra central é outra.
- Grade: n {11,22,44} × mult {2,3,4,5} × src × exit × side, em H1/H4/D1 (288 combinações).
- Escolhido: D1 n=44, mult=3, hl, flip, both. DSR=0,002.
- Dev: 72 trades, +287,9R, PF 7,03, DD 4,5%, 5/5 anos. Val: 45 trades, −3,0R, PF 0,91 (stress −5,4R).
- Interpretação: no desenvolvimento a estratégia surfou as grandes tendências do BTC com stop curto. Em 2021–22 essa vantagem sumiu, e o DSR baixo já sugeria sorte na escolha.

## L34_wide_range_bar — reversão após Wide Range Bar
- Fontes: LuxAlgo (Wide-range bar) e dotnettutorials (WRB). A regra fechada foi montada por mim a partir da definição, porque a fonte não traz um sistema completo.
- Regra: o range passa de k × a média dos 20 candles anteriores e o fechamento fica no terço extremo (CLV ±0,5). O sinal vai contra o WRB. Filtros opcionais: movimento estendido (SMA50) e candle de confirmação. Stop além do extremo + 0,25·ATR, alvo de 1–2R, saída por tempo em 10 candles.
- Grade: 96 combinações × 3 tempos gráficos = 288.
- Escolhido: D1 k=2, ctx=ext, confirmado, alvo 2R, both. DSR=0,0.
- Dev: 35 trades, +6,7R, PF 1,40, 4/5 anos. Val: 11 trades, −5,1R, PF 0,43.
- Interpretação: a vantagem no desenvolvimento era pequena e com poucas operações, e não se sustentou.

## L35_market_structure — Market Structure HH/HL
- Fontes: daytradingtoolkit (higher high/higher low), crosstrade e a teoria de Dow.
- Regra: pivôs com p candles de cada lado, confirmados p candles depois (sem repintura). Com estrutura HH+HL (1 ou 2 ciclos), a estratégia compra quando o HL é confirmado (confirm) ou quando o preço passa da máxima do candle de confirmação (trigger). O stop fica abaixo do HL. A saída vem no fechamento abaixo do último fundo confirmado; alvo opcional de 2R. Short no espelho.
- Diferença do TV33: lá a entrada é o rompimento do topo; aqui a entrada é no recuo (HL), e a saída é a perda do fundo.
- Grade: 64 combinações × 3 tempos gráficos = 192.
- Escolhido: D1 p=2, cycles=1, confirm, sem alvo, só compra. DSR=0,058.
- Dev: 37 trades, +81,3R, PF 5,32, 4/5 anos. Val: 21 trades, −16,0R, PF 0,10.
- Interpretação: foi escolhida a versão só compra, e ela quebrou na baixa de 2022. É o padrão "só ganha surfando a alta".

## L36_hurst_switch — Hurst como interruptor
- Fontes: mql5 HurstExponentRegimeSwitch (R/S, bloco mínimo 8, 6 dobras, EMA5, limiares 0,55/0,45), LuxAlgo (Hurst) e backtrader (estimador).
- Regra: H por R/S nos W retornos passados. O viés do R/S em amostra curta foi corrigido subtraindo a mediana do estimador num passeio aleatório simulado (semente fixa, sem dados do BTC). Sem essa correção, o H do BTC fica perto de 0,57, igual ao de um passeio aleatório, e os limiares publicados perdem sentido. Com H ≥ 0,5+band, entra em rompimento de Donchian N (saída em N/2). Com H ≤ 0,5−band, entra por z-score ±2 contra a SMA N (alvo na média). No meio, não abre posição. Stop k·ATR.
- Grade: 72 combinações × 3 tempos gráficos = 216.
- Escolhido: H4 W=128, band=0,03, N=20, k=3, só compra. DSR=0,0.
- Dev: 130 trades, +65,5R, PF 2,38, 4/5 anos. Val: 62 trades, −8,3R, PF 0,72 (stress −10,5R).
- Interpretação: o H em janela curta é muito ruidoso, e o interruptor não trouxe vantagem fora da amostra.

Motor: nenhum bug encontrado. Uma limitação: `trail` é um array único para os dois lados. No L33 o trail é montado pela direção do indicador e vale NaN no candle da virada.
