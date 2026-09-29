# N12 — atividade de transferências nativas

**Reprovada no desenvolvimento. A meta permanece em 0/7.** A contagem de transferências não antecipou resultado líquido positivo nesta regra. Não houve consulta de resultados de 2025–2026 para alterar a direção, os limiares ou a métrica.

A proposta inicial usaria valor transferido ajustado, indisponível na fonte gratuita examinada. Antes de consultar qualquer série, sinal ou desempenho, a substituição por **contagem de transferências positivas (`TxTfrCnt`)** foi registrada no [protocolo](onchain-count-protocol.json). É a mesma família N12, com uma proxy materialmente diferente; a proposta e o erro de acesso anteriores permanecem preservados. A [definição do produtor](https://gitbook-docs.coinmetrics.io/network-data/network-data-overview/transactions/transfers) não equipara transferências a compras líquidas ou demanda econômica.

A regra compra o perpétuo de BTC ou ETH quando a atividade diária supera estritamente o percentil 70 das 90 observações anteriores, excluindo a atual. Mantém precedência BTC/ETH, stop de 2%, duração máxima de 12 horas, risco de 0,25% do saldo e exposição máxima de 100%. Para não pressupor o encerramento/publicação no rótulo diário, a decisão fica em D+72h e a entrada em D+73h. Esse atraso é uma convenção conservadora prévia; não prova a disponibilidade histórica de versões ainda não revisadas.

## Desenvolvimento: 2022–2024

| Métrica | Base | Stress |
|---|---:|---:|
| Operações encerradas | 593 | 277 |
| Retorno líquido | −9,7213% | −10,1324% |
| Resultado sobre US$100.000 | −US$9.721,26 | −US$10.132,36 |
| Fator de lucro | 0,7742 | 0,5956 |
| Drawdown conservador máximo | 9,9553% | 10,3596% |
| Maior perda diária conservadora | 0,9855% | 0,7801% |
| Violação do limite da conta simulada | Não | Sim |
| Flags de dados durante a execução | 0 | 0 |

Foram 593 dias com condição de entrada, selecionando BTC em 365 e ETH em 228. No cenário base, as 593 operações foram concluídas; no stress, novas entradas foram bloqueadas após violar o limite da conta. O retorno inclui comissão, slippage e funding efetivo; não representa retorno bruto nem operação comprovadamente executável na The5ers. Os dois cenários perderam dinheiro e excederam o respectivo limite de drawdown. Os [resultados completos](onchain-count-results.json) apontam os registros de operações e seus hashes.

## Integridade e limites

As duas séries contêm 1.218 dias cada, incluindo aquecimento, sem lacunas, duplicatas ou valores inválidos. A aquisição pediu somente a métrica, sem preços ou observações de 2025 em diante. Os preços de negócio e de marcação têm 26.304 barras H1 por ativo no desenvolvimento; 120 barras mark ausentes nos arquivos mensais foram recuperadas dos [arquivos diários oficiais](MARK_GAPS.md), com checksums, sem interpolação ou alteração dos arquivos originais.

Os [hashes foram congelados](onchain-count-freeze.json) antes de contar condições ou calcular desempenho. Seis testes do gerador e três de integração verificaram percentil anterior, sequência temporal, recibos, prioridade, entrada/saída e reprovação por dados incompletos. O [executor v3](EXECUTION_V3.md) passou nas regressões sintéticas e não cancela uma entrada retrospectivamente pela ausência da barra mark contemporânea.

A revisão independente posterior conferiu os 16 hashes do congelamento, as 2.436 observações brutas contra as séries normalizadas e o PnL dos dois registros de operações, sem encontrar divergências. As últimas saídas foram em 20/12/2024 às 06h UTC no base e 31/05/2023 às 05h UTC no stress; o segundo permaneceu bloqueado após a violação.

O histórico consultado hoje pode ter revisões e não contém recibos originais. Um futuro teste prospectivo precisaria vincular cada observação à versão e aos bytes efetivamente recebidos até a decisão; um horário desacompanhado dessa prova não basta. Nenhum resultado deste estudo é validação independente, nenhum sinal foi promovido ao aplicativo e nenhuma ordem foi enviada.
