# N2 — carry de funding com BTC spot e short perpétuo

**Triagem retrospectiva reprovada no desenvolvimento; 0 estratégias aprovadas adicionadas.** O protocolo econômico e o motor foram congelados em [`funding-freeze.json`](funding-freeze.json) antes de abrir resultados. Cinco fixtures de causalidade, custos nas duas pernas, funding, margem e saída após risco passaram antes da execução. Reproduzir: `python tests/goal-funding.py` e `python scripts/goal_funding.py --development`. O segundo comando verifica os hashes congelados e só calcula 2022–2024.

## Dados e contrato

BTCUSDT spot H1 existente e BTCUSDT perpétuo USD-M H1, mark H1 e pagamentos realizados de funding da Binance. O [manifesto](funding-data-manifest.json) registra URLs, timestamps, SHA-256 e lacunas; os eventos REST coincidem integralmente com os ZIPs mensais oficiais. Fonte: [Binance Public Data](https://github.com/binance/binance-public-data/blob/master/README.md) e [API oficial de funding USD-M](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data). São mercado spot e contrato perpétuo da Binance em USDT. Equivalência a contrato da The5ers, outra mesa ou execução no MT5 não está estabelecida.

O `markPrice` do evento REST existe apenas desde 31/10/2023 no histórico obtido. Quando ausente, pagamento positivo usa o low do mark H1, e débito usa o high. Isso é bound condicional ao candle disponível, não cotação executável no instante. Se o mark H1 falta, não se presume crédito; a operação é inconclusiva e sai no primeiro open conjunto posterior. Há quatro lacunas de 24 horas no mark BTC H1 na janela total, registradas no manifesto. Não houve interpolação. Caches spot foram reaproveitados sem alteração.

## Regra congelada

A cada H1 fechado, a entrada exige sete dias de barras H1 observadas e contíguas e média dos **21 últimos eventos já liquidados** de funding ≥0,0001. A execução é no open H1 seguinte: compra BTC spot com notional de 45% do patrimônio e vende a mesma quantidade no perpétuo; o caixa restante financia a margem, sem empréstimo. Uma posição por vez. Encerra após 30 dias, após três fundings não positivos consecutivos ou quando o bound adverso de patrimônio perde 2% do patrimônio de entrada ou a margem chega a 10% do notional marcado. Um gatilho intrabar agenda saída no próximo open conjunto observado; não há fill inventado no limiar.

Custos por lado: base spot 10 bps de taxa + 2 bps de slippage, perpétuo 5 + 2; stress spot 15 + 5, perpétuo 10 + 5. Funding positivo no exato instante de entrada/saída ou em barra com risco intrabar de encerramento incerto não é creditado; débito possível é cobrado. O custo de financiamento do caixa próprio foi fixado em zero como hipótese. Custo de oportunidade, liquidação real, bid/ask, restrições da corretora e impacto não foram observados; por isso este teste não oferece aprovação operacional.

## Desenvolvimento, 01/01/2022 a 01/01/2025 exclusivo

| Cenário | Operações | Líquido | Fator de lucro | DD intrabar conservador | Pior perda diária |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base | 26 | +2,21% | 2,58 | 5,05% | 4,77% |
| Stress | 33 | −4,26% | 0,23 | 7,95% | 4,78% |

O cenário base teve 20 saídas por risco intrabar, uma por lacuna, quatro por 30 dias e uma administrativa; 23 das 26 operações carregam alguma incerteza registrada. No stress, 28 saídas foram por risco e 31 das 33 operações têm incerteza. Os detalhes por operação ficam em `research/cache/goal-seven/`, ignorado pelo Git. O [resultado estruturado](funding-results.json) registra os cenários e o hash do freeze.

**Falhas de gate:** 26 operações base ficam abaixo do mínimo de 100 no desenvolvimento; stress líquido é negativo; a perda diária excede 2% base e 3% stress; há lacunas e ambiguidades de observação. A janela de 2025 e a retrospectiva de jan–ago/2026 **não foram executadas**, conforme a regra de parar após falha no desenvolvimento. Não houve ajuste de parâmetro ou redução de exposição após o resultado. O histórico até agosto/2026 já foi inspecionado em outras pesquisas e não constitui holdout intocado.
