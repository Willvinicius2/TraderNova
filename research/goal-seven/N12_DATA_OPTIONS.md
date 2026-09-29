# N12 — opções de métrica diária disponíveis (metadados apenas)

## Conclusão

A métrica `TxTfrValAdjNtv` pedida pela hipótese atual não é disponibilizada no acesso Community testado (403) e não aparece nos cabeçalhos atuais dos CSVs BTC/ETH da Coin Metrics. O melhor substituto de disponibilidade para manter N12 na família de **atividade de transferências on-chain** é `TxTfrCnt`: conta transferências nativas não nulas, é diário e consta nos dois cabeçalhos. Isso é uma troca de variável, não evidência de que conte o mesmo fenômeno econômico ou preserve o mecanismo predito.

Este memo só usa documentação e metadados/cabeçalhos. Não leu observações da série, preços, retornos ou gatilhos; não altera `ONCHAIN_IDEA.md` nem o protocolo. Se escolhido, registrar `TxTfrCnt` como substituição **exclusivamente por indisponibilidade**, na mesma família N12, antes de olhar qualquer valor ou resultado. Não abre uma nova família nem autoriza comparar/procurar retrospectivamente entre métricas.

## Prova de disponibilidade e definição

Uma leitura limitada à primeira linha dos arquivos oficiais `csv/btc.csv` e `csv/eth.csv` recebeu HTTP 206 (Range) e encontrou 32 colunas em cada cabeçalho. `TxTfrCnt`, `TxCnt` e `AdrActCnt` estão presentes em ambos; `TxTfrValAdjNtv` está ausente. Nenhum conteúdo de linhas foi lido nessa verificação.

A [documentação oficial de transferências](https://gitbook-docs.coinmetrics.io/network-data/network-data-overview/transactions/transfers) define `TxTfrCnt` como a soma de transferências do intervalo diário: só transferências de valor positivo são contadas; uma transação pode conter múltiplas transferências. Para ETH, exclui transações falhas e autoenvios, inclui transferências internas e não as separa das transferências de nível superior. A métrica foi lançada como parte de NDP-EOD 1.0. A [visão geral de métricas](https://github.com/coinmetrics/docs-website/blob/master/asset-metrics/asset-metrics-overview.md) informa que métricas de rede diárias se referem às 24 horas anteriores e são computadas às 00:00 UTC.

O catálogo atual oficial Community confirma frequência `1d` e `community=true` para ambos: BTC de `2009-01-03T00:00Z` a `2026-09-27T00:00Z`; ETH de `2015-07-30T00:00Z` a `2026-09-27T00:00Z` (consulta de metadados em 2026-09-28). É cobertura anunciada pela API, não uma auditoria de continuidade ou de cada linha do arquivo. O [repositório de CSV público](https://github.com/coinmetrics/data) informa que os arquivos são gerados da oferta Community e atualizados diariamente; seus termos indicam CC BY-NC 4.0.

## Adequação e risco de revisão/PIT

`TxTfrCnt` é semanticamente mais próximo de `TxTfrValAdjNtv` que `TxCnt` (transações) ou `AdrActCnt` (endereços únicos): ambos contam transferências, mas `TxTfrCnt` não pondera por quantidade transferida, não aplica a filtragem de ruído do valor ajustado e não mede valor econômico. Assim, eventual substituição preserva o tema de atividade da família N12, mas muda materialmente a proxy e requer congelar a variável e a descrição da hipótese antes de examinar observações.

A frequência e o histórico atuais não documentam quando cada valor foi publicado pela primeira vez. Os CSVs são branches atualizados, não vintages imutáveis com horário de recebimento; a própria fonte não garante estabilidade de métricas, ativos ou layout. Valores históricos podem ser recalculados e substituir o estado anterior. Portanto, uma série baixada hoje não prova disponibilidade em `T+48h` nem suporta gate PIT retrospectivo. Para esse gate, seria necessário coletor prospectivo que preserve bytes, timestamp de recebimento UTC e revisões como vintages separadas. O Community é gratuito para uso não comercial; os termos CC BY-NC 4.0 não são uma autorização de uso comercial.

## Fontes consultadas

- [Coin Metrics — Transfers (`TxTfrCnt`)](https://gitbook-docs.coinmetrics.io/network-data/network-data-overview/transactions/transfers)
- [Coin Metrics — Asset Metrics Overview (frequência UTC)](https://github.com/coinmetrics/docs-website/blob/master/asset-metrics/asset-metrics-overview.md)
- [Coin Metrics — Community API e limites/oferta gratuita](https://github.com/coinmetrics/product-docs/blob/master/docs/packages/coin-metrics-community-data.md)
- [coinmetrics/data — arquivos CSV, atualização e licença](https://github.com/coinmetrics/data)
- [Catálogo oficial Community consultado](https://community-api.coinmetrics.io/v4/catalog-all-v2/asset-metrics?assets=btc%2Ceth&metrics=TxTfrCnt) (somente metadados)

