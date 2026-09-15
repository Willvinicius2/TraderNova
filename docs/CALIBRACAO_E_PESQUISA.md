# Calibração de mercado e pesquisa de estratégias

Atualização: 15/09/2026. Preserva os sete instrumentos, ícones, três temas e melhorias concorrentes de consulta externa.

## Correções de dados

- Histórico Kraken ampliado de 240 para até 720 candles. Validação explícita de fonte, ativo, período, OHLC, ordem temporal e horário antes de incorporar a resposta.
- Enquanto o WebSocket está recente, REST verifica o histórico aproximadamente a cada 60 segundos. Sem atualizações do canal, o ativo selecionado é consultado a cada 15 segundos e os demais a cada 30 segundos, sujeitos ao tempo da fonte. Há timeout, cancelamento e rejeição de respostas de outro período. O servidor mantém cache de 15 segundos e unifica requisições simultâneas do mesmo par/período.
- REST e WebSocket usam volumes cumulativos: não somar mensagens repetidas nem sobrescrever candle com menos negócios/volume. Um REST recebido recentemente não transforma candle antigo em informação ao vivo.
- Estados distinguem “Ao vivo”, “Atualização periódica”, falta de atualização, pausa e ausência de rede. O status ao vivo depende de evento OHLC recente e candle do período atual; heartbeat não é preço.
- Preço principal, linha EMA 20 do gráfico e cards nativos usam a mesma série. Leituras: EMA 20/50/200, SMA 20, RSI 14, ATR 14, ATR %, MACD 12/26/9, Bollinger 20 com 2 desvios padrão populacionais e Donchian dos 20 candles anteriores. Aquecimento insuficiente aparece como ausência de valor.
- Cards incluem candle em formação e identificam fonte/período. Lacunas são informadas; não geramos preços para preenchê-las.

## Ouro, Nasdaq e forex

O gráfico externo e o painel de análise técnica usam o mesmo símbolo OANDA e período escolhido no app. O gráfico abre com SMA e Stochastic RSI; parâmetros ficam na legenda do provedor. A barra de período interna foi ocultada para evitar divergência em relação ao seletor do app.

Os estudos externos não equivalem necessariamente às fórmulas e períodos dos dez cards nativos. A análise externa usa os padrões publicados pelo provedor; a interface não afirma identidade numérica nem sincronização atômica entre widgets. Carregar o painel não comprova preço recente. A leitura de atraso e sessão permanece na fonte.

TradingView não fornece os valores dos widgets como API para o motor. Testes automáticos de XAUUSD, NAS100, EURUSD e USDJPY continuam dependendo de histórico autorizado do contrato correto. Os painéis são consulta visual, não uma integração numérica com a corretora do usuário.

## Três candidatas executáveis

Estas regras são hipóteses locais para pesquisa; as referências explicam os indicadores, não comprovam rentabilidade das combinações.

| Código | Condição no fechamento | Stop padrão | Limite padrão |
|---|---|---|---|
| T1 | EMA 9 cruza EMA 21; compra acima, venda abaixo | 1,5 × ATR 14 | 8 candles |
| T2 | Pullback EMA 20/50; inclinação EMA 50 em 3 candles; toque EMA 20; candle de retomada; RSI 14 entre 50–65 na compra ou 35–50 na venda | 1,5 × ATR 14 | 12 candles |
| T3 | Fechamento rompe o canal dos 20 candles anteriores, com filtro EMA 50 | 2 × ATR 14 | 20 candles |

Alvo inicial de 2 R e custo total estimado por trade configurável. A versão T2 usa um só período e não implementa o filtro H1 da hipótese anterior S1. As seis hipóteses S1–S6 continuam identificadas como etapas futuras.

## Como os experimentos são calculados

- Fonte real: BTC/USD, ETH/USD e SOL/USD spot da Kraken. Fonte artificial separada e explicitamente selecionada; erro de rede não aciona simulação automaticamente.
- Usa apenas candles encerrados, ao menos 260, sendo 200 de aquecimento. Histórico com lacunas é rejeitado. Entradas acontecem na abertura seguinte ao sinal, uma posição por vez.
- Stop e alvo derivados do ATR disponível no sinal. Se ambos aparecem no mesmo candle, usa stop; gap que atravessa stop executa na abertura pior. Saída por tempo ou fim da amostra fica identificada.
- Custos descontados em R por operação. R é risco inicial teórico, sem tamanho de posição ou conversão para lucro monetário. Vendas são hipóteses sobre preços spot, não ordens reais nem garantia de disponibilidade de venda descoberta.
- Resultado líquido, trades, taxa de acerto, fator de lucro, expectativa e drawdown em R. Drawdown é calculado após encerramentos; não inclui flutuações intratrade. Fator de lucro fica sem valor quando não há perdas.
- Replay usa o ativo, período e candles do próprio relatório. Últimos 12 experimentos guardados localmente no navegador, sem sincronização entre dispositivos. A exportação JSON inclui parâmetros, operações, amostra e SHA-256 para reprodutibilidade.
- Nenhum resultado move automaticamente a estratégia para “Validada”. A API OHLC oferece no máximo 720 candles recentes, incluindo o candle aberto: cerca de 12 horas em M1 antes de descontar aquecimento. É necessário histórico maior, custos reais e avaliação fora da amostra para avançar na validação.

## Verificação e limites

Os testes automatizados usam entradas controladas para conferir fórmulas, aquecimento, causalidade das três candidatas, execução na abertura seguinte, custos, stops ambíguos, gaps, persistência e coerência de fonte/período. A consulta HTTP autorizada à API publicada retornou candles reais de BTCUSD/M15 da Kraken antes desta atualização. Isso comprova a integração REST nesse momento; não é uma medição contínua do WebSocket ou uma inspeção dos widgets no aparelho.

Recepção visual dos widgets e atualização do WebSocket no dispositivo ainda precisam ser acompanhadas em uso. Não declarar “100% ao vivo” pela aprovação de testes numéricos ou carregamento de iframe.

## Referências

- [Kraken: histórico OHLC, limite e candle aberto](https://docs.kraken.com/api-reference/market-data/get-ohlc-data).
- [Kraken: OHLC por eventos de negociação](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/ohlc).
- [TradingView: limites de acesso aos dados dos widgets](https://www.tradingview.com/widget-docs/faq/data/).
- [TradingView: gráfico com estudos](https://www.tradingview.com/widget-docs/widgets/charts/advanced-chart/demos/technical-analysis/).
- [Fidelity: EMA](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/ema), [RSI](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/RSI) e [ATR](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/atr).
- [TradingView: canais de Donchian](https://www.tradingview.com/support/solutions/43000502253-donchian-channels-dc/).
