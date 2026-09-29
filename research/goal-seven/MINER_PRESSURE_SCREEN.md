# N14: contração da capacidade de mineração

**Reprovada no desenvolvimento. Não validada.** Uma única regra, BTC apenas, registrada no commit `e8a995e` antes da aquisição e dos gatilhos. Não foi invertida nem ajustada depois do resultado.

A hipótese é que a contração da capacidade de mineração pode acompanhar pressão financeira e venda de reservas. A [documentação primária da Coin Metrics](https://gitbook-docs.coinmetrics.io/network-data/network-data-overview/mining/hash-rate) define `HashRate` diário como uma estimativa derivada da dificuldade e da produção de blocos, em TH/s no BTC. Isso não mede vendas de mineradores: interrupções climáticas, regulação e aleatoriedade dos blocos também afetam a série. A relação entre receita por hash e rentabilidade operacional é discutida pela [Coin Metrics](https://coinmetrics.substack.com/p/state-of-the-network-issue-174); o sinal de preço proposto aqui continua sendo uma conjectura a testar.

Regra fixa: vender quando a média dos últimos sete dias de HashRate fica estritamente abaixo da média de trinta, sem filtro de preço. Os trinta valores precisam ser consecutivos. Rótulo diário D tratado como início do dia; feature termina D+24h; decisão D+72h e entrada D+73h. Stop 2%, duração máxima 12h, risco 0,25% e exposição bruta até 1x. Custos base/stress e funding conservador do executor v4, sem alterar os critérios globais.

Uma consulta pública retornou 135.369 bytes e 1.218 dias completos de setembro/2021 a dezembro/2024, sem duplicatas. A fonte e a normalização têm hashes. Os cinco testes sintéticos passaram; código, protocolo e fontes foram congelados antes de calcular 357 gatilhos de desenvolvimento. Não houve consulta de performance em 2025–2026.

| Cenário | Operações | Retorno líquido | Fator de lucro | DD conservador | Perda diária máxima | Violação da conta |
|---|---:|---:|---:|---:|---:|---|
| Base | 357 | −6,9844% | 0,7212 | 7,3710% | 0,7671% | Não |
| Stress | 285 | −10,0418% | 0,5340 | 10,2933% | 0,7409% | Sim |

O cenário base passou no teto de DD, mas perdeu dinheiro e falhou no fator de lucro. O stress perdeu dinheiro, excedeu o DD e interrompeu por violação da conta. Não há flags de lacuna de execução. Foram usados limites adversos de mark em 194 eventos de funding; isso não é cotação de liquidação observada. Conferência posterior: 12 hashes do freeze íntegros, hashes dos detalhes válidos, contagens conciliadas e soma dos PnLs igual ao resultado financeiro, com sinal short e ordem temporal coerentes.

Vintages e horários originais da fonte continuam não comprovados. Mesmo se tivesse passado, esse estudo retrospectivo não satisfaria a etapa independente/prospectiva nem certificaria custos ou contrato The5ers. A distinção econômica de uma futura família de mineração precisaria de revisão antes de contar para a meta.

Arquivos reproduzíveis: `miner-pressure-protocol.json`, `miner-pressure-data-manifest.json`, `miner-pressure-freeze.json`, `miner-pressure-sample.json` e `miner-pressure-results.json`; detalhes com hash no cache. **0/7 aprovadas; N14 encerrada sem resgate.** A fila N13 continua separada e seu código em execução não foi alterado.
