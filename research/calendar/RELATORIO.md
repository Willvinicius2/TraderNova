# Auditoria independente de família nova: N3 calendário cripto

Data: 28/09/2026. **Resultado: nenhuma estratégia nova passou a triagem histórica; nenhuma foi validada ou aprovada.** Este relatório cobre a família N3; N4 possui relatório separado. Alterar horários, filtrar ativos ou acrescentar indicadores depois de ver estas perdas constituiria outra hipótese e não recuperaria esta validação.

## Hipótese, distinção e fundamento

N3 mantém posição comprada spot de segunda 00h UTC a sábado 00h UTC e fica em caixa no restante da semana. A decisão de calendário é conhecida antes da entrada; não usa EMA, pullback, Donchian, faixa de abertura, POC, varredura, zona, RSI, reversão pós-choque, pares ETH/BTC ou funding. O estudo [Hansen, Kim e Kimbrough](https://arxiv.org/abs/2109.12142) documenta periodicidade de volatilidade e liquidez em BTC/ETH, enquanto [Liu e Tsyvinski](https://www.nber.org/papers/w24877) relatam diferenças de retorno por dia em amostras históricas; nenhum deles demonstra que **esta regra** tem lucro líquido. A exclusão de sábado/domingo também diminui tempo exposto, exigindo comparação com comprar e manter.

## Protocolo congelado antes dos resultados

O [protocolo](protocol.json) fixa uma única regra e três ativos, sem otimização. Fonte: caches Binance Spot H1 auditados pelo manifesto `research/cache/v3/manifest.json`, derivados dos [arquivos oficiais](https://github.com/binance/binance-public-data/blob/master/README.md). SHA-256: BTC `eec6d00f0a38d5658b16c53928aed72cea3f1c925c8c73850ea75888c2ced678`; ETH `e476a43feed4716a833cbccfc6061816d19e722a8e439da0b8ff0b90f56a1ff3`; SOL `33393a1c43d34808db5755e905f3c3205eb836bbff9728e047830f894bd235f4`. Cobertura de 01/12/2021 a 31/08/2026, com a única lacuna conhecida em 24/03/2023 13h UTC. Uma posição afetada é encerrada na primeira abertura observada, sem candle inventado.

Cada janela começa com 10.000 USDT fictícios; posição integral spot, sem venda ou alavancagem. Compra na abertura de segunda após o fechamento contíguo de domingo 23h; venda na abertura de sábado. Sem stop intrabar. Taxas e slippage adverso aplicados no preço preenchido em cada ponta: base 0,10% + 0,02%; stress 0,15% + 0,05%. Patrimônio e drawdown são marcados nos fechamentos, com liquidação estimada; risco intrabar pode ser maior. O benchmark compra e mantém o ativo durante toda a janela com os mesmos custos de início/fim, mas assume mais horas de exposição.

Desenvolvimento: 2022–2024, incluindo três avaliações anuais. Validação cronológica: 2025. Período final retrospectivo: janeiro–agosto/2026, calculado uma vez após salvar protocolo e triagem 2025. Critérios pré-fixados: pelo menos 2 de 3 anos positivos no desenvolvimento por ativo; ≥140/45/25 operações em desenvolvimento/validação/final; base e stress positivos em validação e final; PF ≥1,20 e DD ≤20% nessas duas janelas; ao menos 2 dos 3 ativos devem passar todos os itens. O período final já foi consultado em estudos anteriores do projeto: **não é holdout intocado entre pesquisas**, nem o resultado é validação prospectiva.

## Resultados líquidos

| Ativo | Desenvolvimento 2022–24 | Validação 2025 (51 trades) | Stress 2025 | PF / DD 2025 | Final jan–ago/2026 (34 trades) | Stress final | PF / DD final | Triagem |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| BTCUSDT | +19,95% | −24,92% | −30,80% | 0,78 / 43,44% | −13,64% | −18,21% | 0,80 / 36,71% | Reprovada |
| ETHUSDT | −41,90% | −37,33% | −42,24% | 0,79 / 57,06% | −17,60% | −21,96% | 0,78 / 46,89% | Reprovada |
| SOLUSDT | −59,81% | −57,44% | −60,77% | 0,65 / 62,40% | −19,51% | −23,77% | 0,76 / 48,65% | Reprovada |

O ano de 2022 foi fortemente negativo: BTC −59,30%, ETH −60,45%, SOL −92,24%. Os três ativos tiveram 156 operações no desenvolvimento e dois anos positivos em 2023–2024, mas o conjunto ficou frágil; só BTC terminou 2022–2024 positivo. Na validação de 2025, todos perderam mais que comprar e manter na mesma janela (benchmark BTC −6,56%, ETH −11,18%, SOL −34,31%). No final retrospectivo, o benchmark foi BTC −10,56%, ETH −17,16%, SOL −17,51%; N3 também não mostrou vantagem líquida. Os contadores de operações passaram, porém lucro, PF e drawdown falharam em todos os ativos. **Passaram a triagem: 0 de 3.**

## Reprodução e limites

Arquivos: `run-calendar.mjs`, `screen.json` e `result.json`, preservados nesta pasta do repositório. Executar `node research/calendar/run-calendar.mjs --self-test`, depois `--phase=screen` e `--phase=final`; a fase final verifica SHA-256 do protocolo e das séries contra o arquivo da triagem. O autoteste confere calendário, execução e custos em preços constantes. A estratégia não foi simulada no contrato MT5/the5; não há spread executável, regras de perda diária da mesa, capital conjunto, indisponibilidade de exchange, ordens reais ou forward test. O desfecho mantém `validated:false` e não altera `forwardPassed` de qualquer estratégia do aplicativo.
