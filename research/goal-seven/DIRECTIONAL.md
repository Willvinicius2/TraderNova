# N5 e N6: primeira rodada da meta de sete

**As duas regras reprovaram no desenvolvimento. Nenhuma conta como validada.**

Auditoria posterior identificou uma limitação na v1 preservada: funding alguns milissegundos após o início da hora podia gerar crédito incerto na entrada ou omissão de débito possível na saída. Os números e fontes originais abaixo não foram sobrescritos nem certificados; continuam reprovados. A [política v2](EXECUTION_V2.md) corrige o caso para novas pesquisas, antes de qualquer desempenho N11.

Os protocolos, gerador, executor e fontes foram registrados em `directional-freeze.json` antes da primeira execução de desempenho. `directional-results.json` mantém os números completos e hashes dos arquivos de operações. Reproduzir em uma cópia preservada: `python tests/goal-signals.py`, `python tests/goal-execution.py`, `python scripts/run-goal-directional.py prepare`, depois `development`. O runner recusa sobrescrever resultados ou misturar arquivos diferentes do snapshot. Não apagar o registro para tentar novamente com parâmetros favoráveis.

## Regras e fonte

- **N5, fluxo agressor:** compra após desequilíbrio de compras agressoras na vela spot H1, variação de preço pequena e volume suficiente. Usa volume cotado, sem EMA ou rompimento. Prioridade previamente fixa BTC → ETH → SOL; uma posição na família. Stop de 1%; duração máxima de duas horas.
- **N6, transmissão BTC → altcoin:** compra ETH ou SOL após salto do BTC e resposta pequena do seguidor na mesma H1 encerrada. Prioridade ETH → SOL; sem hedge ou ranking de retornos. Stop de 1,5%; duração máxima de duas horas.

O sinal usa apenas candles spot encerrados. A entrada usa a abertura seguinte do perpétuo USD-M; a saída por tempo é duas horas depois. Cada família usa capital fictício de USDT 100.000, risco planejado de 0,25% por entrada e exposição bruta máxima de 100%. Quantidades contínuas são uma aproximação de pesquisa; regras históricas de lote e acesso à conta não foram certificadas.

Taxa/slippage por execução: 5/2 pontos-base no cenário base; 10/5 no stress. Funding realizado é descontado. Eventos antigos sem preço mark exato usam limite adverso do candle mark H1. A v1 excluía créditos em stops intrabar e eventos exatamente no rótulo da abertura, mas não cobria toda a incerteza da hora de entrada/saída, conforme auditoria acima. Custos são cenários, não uma tabela certificada do broker.

## Resultados: desenvolvimento 2022–2024

| Família/cenário | Operações | Líquido | PF | DD conservador | Decisão |
|---|---:|---:|---:|---:|---|
| N5 base | 251 | −9,951% | 0,472 | 10,044% | Reprovada |
| N5 stress | 175 | −10,058% | 0,334 | 10,103% | Reprovada |
| N6 base | 78 | −4,489% | 0,485 | 5,395% | Reprovada |
| N6 stress | 78 | −5,857% | 0,363 | 6,236% | Reprovada |

N5 atingiu o limite conservador da conta fictícia; novas entradas foram interrompidas, sem reiniciar o capital. Isso explica contagens diferentes entre custos base e stress. N6 teve drawdown menor, mas perdeu dinheiro e não atingiu as 100 operações mínimas. Drawdown baixo sozinho não aprova a estratégia.

Os quatro caminhos não atravessaram lacunas de dados enquanto havia posição aberta. Há lacunas em outras partes das fontes; elas permanecem documentadas e não foram interpoladas. A marcação usa um envelope conservador de máximas/mínimas, não um caminho intrabar observado nem uma promessa de stop garantido.

**As janelas 2025 e janeiro–agosto/2026 não foram usadas para resgatar essas regras.** Não houve busca de outro limiar, inversão de sinal ou seleção do ativo com melhor retorno após o resultado. Datas já examinadas em pesquisas anteriores não são holdout intocado.

## Verificação independente

Os testes cobrem causalidade e prioridade dos sinais, custo nas duas pontas, reconciliação entre caixa e operações, gaps, dados faltantes e funding no instante da entrada/saída. Uma revisão independente encontrou um crédito de funding ambíguo no instante da saída; a correção e regressões foram concluídas antes da primeira execução histórica.

Motivação e limitações econômicas: [IDEIAS.md](IDEIAS.md). Fonte dos arquivos: [Binance Public Data](https://github.com/binance/binance-public-data/blob/master/README.md). Critérios completos: [protocol.json](protocol.json).
