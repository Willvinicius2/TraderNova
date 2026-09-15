# TraderNova 0.2 — Conexão de mercado

Atualização: 15/09/2026.

## Implementado

- Mercado real é o modo inicial, com Bitcoin selecionado e gráfico M1.
- Kraken Spot: BTC/USD, ETH/USD e SOL/USD. São pares spot cotados em USD; não USDT e não CFDs do MT5.
- Uma conexão pública WebSocket v2 por aba visível, com OHLC dos três pares no período escolhido e ticker para variação em 24 horas e bid/ask.
- Candles M1, M5, M15 e H1; números e candle em formação usam o mesmo fechamento recebido pelo canal OHLC.
- Atualização visual agrupada a cada 200 ms no máximo, destacando alta/baixa. Nenhuma geração artificial de movimentos.
- Histórico inicial pela API REST, com até 240 candles retornados ao app. Volume da Kraken é cumulativo: atualizações substituem a barra, sem somar o volume novamente.
- Histórico atrasado não sobrescreve um candle que já contém mais negócios/volume recebidos ao vivo. Troca de ativo/período cancela a leitura anterior e rejeita respostas antigas.
- Estado visível de conexão, horário de recebimento e falta de atualização. Heartbeat mantém a conexão, mas não altera o horário do último preço. O selo “Ao vivo” exige atualização OHLC recente e candle da janela atual.
- Reconexão com espera progressiva de 5 a 30 segundos e pequena variação aleatória. Histórico solicitado novamente ao reconectar.
- Ao ocultar a aba ou sair de Mercado, a conexão é encerrada; ao voltar, reconecta e ressincroniza. Não há motor de mercado em segundo plano.
- EMA20, RSI14 e ATR14 calculados nos candles recebidos, incluindo o candle aberto. São indicadores visuais; não são sinais validados.
- XAUUSD, NAS100, EURUSD e USDJPY ficam sem cotação em modo real até conectar uma fonte identificada. O modo Demonstração continua separado.
- Falha de rede nunca substitui dados reais por números sintéticos.

## Verificações realizadas

`node tests/live-market.mjs`: contratos de eventos, preço/candle sincronizados, volume cumulativo, deduplicação, histórico atrasado, virada de candle, mensagens inválidas, limites de reconexão, estados offline/desatualizado, lista de parâmetros permitidos, coalescência de requisições, cache e falha do provedor. As chamadas HTTP dos testes são controladas; não simulam validação do mercado.

`node tests/core.mjs`: verificações anteriores do motor demonstrativo preservadas.

`pnpm exec tsc --noEmit`: tipos da aplicação.

A tentativa direta de HTTP e WebSocket para a Kraken não recebeu dados neste ambiente de execução (timeout). Portanto, o fluxo completo com pacotes reais no aparelho do usuário não foi confirmado nesta entrega. O app mostra seu estado de conexão sem afirmar que o feed está ativo na ausência de dados.

## Limites

A fonte pública depende da rede, disponibilidade e permissões do provedor no local do usuário. Pode haver intervalos sem negócios. O app não promete atualização em um número fixo de milissegundos nem latência de execução. “Recebido há” mede tempo desde o recebimento local; não é latência de ponta a ponta.

O horário de início de uma barra não é a hora do último negócio. Candles abertos não podem ser usados como candles encerrados no futuro motor de estratégias. Cotações spot não equivalem automaticamente às da corretora de execução. Os sinais, o diário e o backtest existentes continuam demonstrativos.

## Próximo passo: ouro e Nasdaq

Identificar corretora/mesa, servidor e nomes exatos dos instrumentos. Conectar feed autorizado de leitura e histórico correspondente; mapear moeda, tick size, sessões e atrasos. O aplicativo não pede chave de negociação e não envia ordens.

## Consumo

Sem chamadas de IA ou Supabase por atualização. Uma conexão por aba visível. O histórico é buscado por ativo/período e após reconexão; cache em memória de 15 segundos e requisições simultâneas unificadas no servidor. Os dados recebidos não são armazenados no Supabase nesta versão. A existência de múltiplas abas abertas cria múltiplas conexões.

## Fontes oficiais consultadas

- [Endpoints e recomendações de conexão](https://docs.kraken.com/exchange/guides/websockets/introduction).
- [OHLC por evento de negociação](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/ohlc).
- [Ticker, variação e bid/ask](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/ticker).
- [Histórico OHLC e candle ainda aberto](https://docs.kraken.com/api-reference/market-data/get-ohlc-data).
