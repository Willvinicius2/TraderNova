# N15: emissão de stablecoins e capacidade de compra

**Reprovada no desenvolvimento.** O lucro base não resistiu aos custos de stress, e o fator de lucro base ficou abaixo de 1,20. Nenhuma regra ou limite foi alterado depois do resultado.

A hipótese usa o crescimento da oferta nominal de USDT+USDC como possível ampliação da capacidade de compra de BTC. A [definição de SplyCur](https://gitbook-docs.coinmetrics.io/network-data/network-data-overview/supply/current-supply) inclui unidades emitidas visíveis no ledger, inclusive saldos que podem ser ilíquidos. Não equivale a depósitos novos destinados a comprar BTC. O [estudo de Liao e Caramichael](https://www.federalreserve.gov/econres/ifdp/files/ifdp1334.pdf) descreve que stablecoins também podem receber demanda por proteção durante estresse cripto; esse mecanismo alternativo pode invalidar a direção proposta.

Regra registrada no commit `8068bd9` antes das séries: comprar BTC quando a soma de SplyCur de `usdt` e `usdc` supera seu valor sete dias antes, exigindo oito dias consecutivos completos e preço diário atual de cada stablecoin entre US$0,99 e US$1,01. Usa os tickers parentais da fonte sem somar também seus componentes. Mudanças históricas de cobertura de redes e vintages não estão comprovadas. Entrada D+73h para rótulo D, stop 3%, até 72h por posição, risco 0,25%, exposição máxima 1x e nenhuma reentrada na hora de saída.

O catálogo antigo retornou HTTP400 por parâmetro não suportado; resposta preservada. O endpoint documentado `catalog-all-v2` confirmou disponibilidade pública dos dois indicadores. Uma única consulta de série retornou 289.486 bytes: 1.218 dias completos por stablecoin, sem duplicatas. Os quatro testes sintéticos passaram e o freeze antecedeu os 623 gatilhos. Gatilhos durante uma posição aberta são ignorados; não são operações adicionais.

| Cenário | Operações | Retorno líquido | Fator de lucro | DD conservador | Perda diária máxima |
|---|---:|---:|---:|---:|---:|
| Base | 239 | +1,9160% | 1,0620 | 4,1319% | 1,1317% |
| Stress | 239 | −0,8604% | 0,9720 | 4,3881% | 1,0864% |

Não houve violação da conta nem flags de lacuna ativa. O motor usou limites conservadores de mark para 741 eventos base e 740 stress; não são preços de settlement diretamente observados. Uma condição na fronteira final não foi executada. A conferência pós-teste verificou os 13 hashes do freeze, os hashes dos detalhes, contagem de operações, ordem temporal e conciliação da soma de PnLs com o saldo.

Estudo apenas em desenvolvimento 2022–2024, com informação histórica exploratória e custos de USD-M que não certificam o contrato The5ers. **Nenhuma avaliação de 2025–2026, nenhum ajuste para resgate, nenhuma aprovação.** A meta permanece 0/7. A N13 continua na fila independente sem alteração de seus arquivos de código.

Evidências: `stablecoin-liquidity-{protocol,data-manifest,freeze,sample,results}.json`; detalhes no cache com hashes vinculados ao resultado. A pequena consulta de metadados e seu erro anterior também permanecem registrados.
