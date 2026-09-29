# N2 — carry de funding com BTC spot e short perpétuo

**Triagem retrospectiva reprovada no desenvolvimento; 0 estratégias aprovadas adicionadas.** O protocolo econômico e o motor v1 foram congelados antes da primeira execução. Uma auditoria após essa rodada encontrou três falhas de software/medição e dois gates incompletos; [código, freeze, resultados e ledgers v1](revisions/funding-v1/preservation-manifest.json) foram copiados com SHA-256 antes da correção. A [revisão v1.1 congelada](funding-freeze.json) mantém sinal, alocação, saídas, custos e fonte. Dez fixtures passaram antes da reexecução v1.1. Reproduzir: `python tests/goal-funding.py` e `python scripts/goal_funding.py --development`. O segundo comando verifica os hashes v1.1 e só calcula 2022–2024.

## Dados e contrato

BTCUSDT spot H1 existente e BTCUSDT perpétuo USD-M H1, mark H1 e pagamentos realizados de funding da Binance. O [manifesto](funding-data-manifest.json) registra URLs, timestamps, SHA-256 e lacunas; os eventos REST coincidem integralmente com os ZIPs mensais oficiais. Fonte: [Binance Public Data](https://github.com/binance/binance-public-data/blob/master/README.md) e [API oficial de funding USD-M](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data). São mercado spot e contrato perpétuo da Binance em USDT. Equivalência a contrato da The5ers, outra mesa ou execução no MT5 não está estabelecida.

O `markPrice` do evento REST existe apenas desde 31/10/2023 no histórico obtido. Quando ausente, pagamento positivo usa o low do mark H1, e débito usa o high. Isso é bound condicional ao candle disponível, não cotação executável no instante. Se o mark H1 falta, não se presume crédito; a operação é inconclusiva e sai no primeiro open conjunto posterior. Há quatro lacunas de 24 horas no mark BTC H1 na janela total, registradas no manifesto. Não houve interpolação. Caches spot foram reaproveitados sem alteração.

## Regra congelada

A cada H1 fechado, a entrada exige sete dias de barras H1 observadas e contíguas e média dos **21 últimos eventos já liquidados** de funding ≥0,0001. A execução é no open H1 seguinte: compra BTC spot com notional de 45% do patrimônio e vende a mesma quantidade no perpétuo; o caixa restante financia a margem, sem empréstimo. Uma posição por vez. Encerra após 30 dias, após três fundings não positivos consecutivos ou quando o bound adverso de patrimônio perde 2% do patrimônio de entrada ou a margem chega a 10% do notional marcado. Um gatilho intrabar agenda saída no próximo open conjunto observado; não há fill inventado no limiar.

Custos por lado: base spot 10 bps de taxa + 2 bps de slippage, perpétuo 5 + 2; stress spot 15 + 5, perpétuo 10 + 5. Funding positivo no exato instante de entrada/saída ou em barra com risco intrabar de encerramento incerto não é creditado; débito possível é cobrado. O custo de financiamento do caixa próprio foi fixado em zero como hipótese. Custo de oportunidade, liquidação real, bid/ask, restrições da corretora e impacto não foram observados; por isso este teste não oferece aprovação operacional.

## Auditoria numérica v1.1

- Uma posição sem open conjunto na borda final agora fica **não encerrada**, com líquido e fator de lucro nulos e gate bloqueado; não se reporta o patrimônio anterior como resultado final.
- O drawdown considera no mesmo H1 um pico favorável (spot high, menor entre perp/mark low) antes de um vale adverso (spot low, maior entre perp/mark high), com débitos antes dos créditos no envelope de caixa. Se faltar dado para limitar o envelope, a triagem é inconclusiva. Isso aumenta o DD estimado e não afirma uma sequência intrabar observada.
- A execução sinaliza patrimônio conservador ≤90.000 USDT ou perda diária ≥3%, exige reconciliação do capital e ≥100 operações em **base e stress**. São correções dos critérios originais, sem ajuste para melhorar performance.

## Desenvolvimento, 01/01/2022 a 01/01/2025 exclusivo — v1.1

| Cenário | Operações | Líquido | Fator de lucro | DD intrabar conservador | Pior perda diária |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base | 26 | +2,21% | 2,58 | 8,79% | 4,77% |
| Stress | 33 | −4,26% | 0,23 | 9,65% | 4,78% |

Na v1 preservada, os DDs reportados eram 5,05% base e 7,95% stress porque o pico favorável intrabar não entrava no cálculo. Operações, líquido e fator de lucro permaneceram iguais na v1.1. O capital reconciliou exatamente em ambos os cenários, e nenhuma posição ficou aberta na borda final da rodada real. O envelope permaneceu incompleto em uma lacuna ativa de dados; `accountBreach=true` nos dois cenários, inclusive pela perda diária acima de 3%.

O cenário base teve 20 saídas por risco intrabar, uma por lacuna, quatro por 30 dias e uma administrativa; 23 das 26 operações carregam alguma incerteza registrada. No stress, 28 saídas foram por risco e 31 das 33 operações têm incerteza. Os detalhes por operação ficam em `research/cache/goal-seven/`, ignorado pelo Git. O [resultado estruturado](funding-results.json) registra os cenários e o hash do freeze.

**Falhas de gate:** 26 operações base e 33 stress ficam abaixo de 100; stress líquido é negativo; DD base excede 8%; perda diária excede 2% base e 3% stress; houve breach e incerteza de lacuna/timing. A janela de 2025 e a retrospectiva de jan–ago/2026 **não foram executadas**, conforme a regra de parar após falha no desenvolvimento. Não houve ajuste de parâmetro ou redução de exposição após o resultado. O histórico até agosto/2026 já foi inspecionado em outras pesquisas e não constitui holdout intocado.
