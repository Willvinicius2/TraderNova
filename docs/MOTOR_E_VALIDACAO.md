# Motor, simulações e pesquisa histórica

## Fluxo decidido pelo usuário

- **Robô:** somente estado da busca, sinais, motivo de cada sinal, entrada, stop loss e take profit. Sem formulário nem criação de exemplos. Alertas para operação manual exigem aprovação específica da estratégia/fonte/ativo/período e acompanhamento prospectivo concluído.
- **Laboratório:** escolher uma das três estratégias prontas; iniciar Backtest ou Simulação em tempo real. Parâmetros pertencem ao protocolo de pesquisa e não são editáveis pelo usuário na tela.
- **Estratégias:** candidatas, resultados da triagem e validadas. As 18 combinações desta rodada foram reprovadas. O registro de aprovação permanece vazio.
- Preservados componentes, geometria, navegação e três temas do site aprovado.

## Histórico reproduzível

`research/protocol.json` foi escrito antes da execução desta rodada. Fontes: 150 arquivos mensais Binance Spot, incluindo agosto/2024 para aquecimento, com checksum SHA-256 oficial. São 273.960 candles (73.056 M15 e 18.264 H1 por ativo); não há lacunas nas seis séries. Microssegundos desde janeiro/2025 são convertidos para milissegundos. O manifesto publica URLs, hashes e cobertura; o cache bruto fica fora do Git.

Reprodução: `npm run research:download`, depois `npm run research:run`. Python usa apenas biblioteca padrão; Node transpila o mesmo motor TypeScript que a interface usa. Não há Python alternativo calculando sinais. Resultado completo em `research/RESULTADOS.md` e `public/research/`.

O backtest de um clique usa BTC/USDT H1 e a janela final fixa mar–ago/2026. Baixa uma amostra verificada por SHA-256 e **recalcula** as operações no navegador. O estudo de 18 combinações inclui três estratégias × três ativos × M15/H1; as janelas são desenvolvimento de 12 meses, validação de seis meses e avaliação final retrospectiva de seis meses. O período final já foi citado nos chats: não é holdout intocado. Nenhum parâmetro foi otimizado ou escolhido depois de ver os resultados. Comprar e manter com os mesmos custos aparece como referência, com exposição diferente da estratégia.

Compras spot apenas, uma posição, unidades fracionárias, sem alavancagem. Capital reiniciado em 10.000 USDT por janela, risco planejado até 0,5%; dimensionamento inclui custos previstos no stop e limita a compra ao caixa disponível. Sinal no fechamento e entrada na abertura seguinte; aquecimento de 200 candles; sinal anterior à janela não gera entrada. Stop e alvo são fixos, stop ATR 1,5/1,5/2 para T1/T2/T3, alvo 2R, duração máxima 8/12/20 candles. Quando abertura determina um gap pelo alvo, ele tem precedência; nas demais ambiguidades intrabar, o stop vem primeiro. Gaps adversos podem exceder o risco planejado. Trades são liquidados no fim da janela e não atravessam cortes da avaliação.

Custos base: taxa 10 bps e slippage 2 bps por lado; stress 15 e 5 bps. São hipóteses, não tarifa da conta MT5. Métricas monetárias usam USDT; o drawdown mede marcação **no fechamento do candle**, incluindo custo de liquidação estimado, sem capturar o pior movimento intrabar. Não verifica regras da mesa, swaps, funding, lote mínimo, limite de notícias ou impostos. PF sem perdas é indefinido, não infinito.

Triagem exige em validação e final: 100 trades, resultado positivo, PF≥1,20, DD≤15%; final também positivo em custos elevados. Esses filtros não provam significância estatística, robustez em mercados futuros nem independência das 18 combinações. Passar apenas habilitaria pesquisa prospectiva, nunca aprovação automática para operar.

## Simulação prospectiva

Preset inicial: BTC/USD Kraken H1, uma posição de compra, conta fictícia de 100.000 USD, risco até 0,5%, custos estimados iguais ao backtest. Não equivale a Binance BTC/USDT nem ao CFD da mesa.

Busca somente candles fechados, contínuos e recentes. Entradas usam bid/ask recebido depois do fechamento, dentro de 30 segundos, e depois do início da sessão. Não usa abertura passada para simular entrada retroativa. Indicadores são compartilhados com o backtest. Stops, alvos e tempo são avaliados nas cotações observadas. Posição aberta continua a ser gerida com cotação recente mesmo que falte histórico para novo sinal. Dados velhos não geram entradas. Não reabre na mesma cotação após encerrar uma posição.

Usuário informou banca 100 mil, perda diária 3 mil e total 10 mil. O simulador usa esses limites, piso total fixo 90 mil e referência diária ao patrimônio no primeiro processamento do dia UTC. Não representa certificação da regra The5ers. Limite diário pausa até o próximo dia; limite total permanece bloqueado. Entradas são reduzidas ao risco restante; gaps podem exceder limites. Pausar ou ocultar a aba interrompe observações; retomar usa a próxima cotação, sem reconstruir supostas execuções durante a interrupção. A sessão e posição abertas são restauradas do armazenamento local e permanecem pausadas até continuar. Exportação JSON inclui sessão, operações e preset. Não há motor em segundo plano, conta conectada ou ordens enviadas.

## Alertas manuais

Registro vazio em `paper-engine.ts`; aprovação exige fonte/ativo/período exatos, data vigente e forward test aprovado. `RobotWorkspace` consome exclusivamente registros aprovados, exibe busca ativa ou espera pela fonte, deduplica por estratégia/fechamento e mostra alerta na tela com preços, evidências dos indicadores e validade. Cotações anteriores ao sinal e dados atrasados são bloqueados. Nenhum alerta operacional será emitido pelos estudos reprovados. A simulação usa alerta distinto, rotulado como entrada fictícia.

## Contrato da mesa

O usuário identificou uma mesa provavelmente The5ers, sem informar programa/servidor. Seus limites declarados permanecem a referência local; não foram substituídos pelos de um programa presumido. Para avaliar a conta real: obter histórico/exportação do MT5, símbolo, tamanho de contrato, tick, lote mínimo/passo, spread, comissão, swap, horário de reinício e base exata dos limites. O site continua com sete ativos de mercado; somente cripto tem dados numéricos neste motor.

Fontes primárias: [arquivos Binance](https://github.com/binance/binance-public-data), [tarifas spot](https://www.binance.com/en/fee/trading), [especificações The5ers](https://the5ers.com/asset-specifications/), [exportação MT5](https://www.metatrader5.com/en/terminal/help/trading/market_watch), [risco de sobreajuste em backtests](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).

## Verificação

Testes determinísticos cobrem causalidade, RSI idêntico ao original, ausência de vendas, limites das janelas, custo nos dois lados, dimensionamento, reconciliação da curva, gaps, ambiguidades, barras duplicadas, cotações anteriores ao sinal, restauração de posição, saída por risco com histórico bloqueado e bloqueio de alertas sem aprovação. Os fixtures são sintéticos **apenas nos testes do software**, separados dos resultados históricos reais. A rodada completa foi executada localmente. O build e a compilação verificam integração; não houve teste solicitado em navegador/aparelho nem observação prospectiva longa nesta etapa.
