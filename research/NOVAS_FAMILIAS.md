# Novas famílias de pesquisa — N1 e N2

Gerado em 28/09/2026. **Nenhuma candidata está validada ou aprovada.** O arquivo consumível da interface é `public/research/novel-study.json`. Estas hipóteses são distintas dos sinais direcionais do catálogo; não autorizam ordens, alertas operacionais ou promessa de retorno.

## Inventário e separação

- Cripto T1–T3, em `lib/tradernova/research.ts` e `research/protocol.json`: tendência/EMA, pullback e Donchian; a rodada histórica e calibrações não aprovaram nenhuma combinação.
- Catálogo S1–S6 em `lib/tradernova/domain.ts`: pullback de tendência, rompimento/reteste, POC, varredura de liquidez, oferta/demanda e faixa de abertura. S3 e S6 dependem de dados específicos.
- Ouro G1–G5, em `research/gold-v1-protocol.json` e `research/gold-h1-v2-protocol.json`: pullback, faixa inicial, Bollinger, varredura e divergência RSI; todos reprovados nas rodadas existentes.
- FX em `scripts/backtest_fx_families.py`: tendência, breakout, reversão à média **univariada**, RSI e abertura. N1 é uma carteira relativa ETH/BTC com duas pernas e hedge causal; N2 depende de pagamentos de funding efetivos. Nenhuma das duas é uma versão de parâmetro dessas famílias.

## N1 — reversão relativa ETH/BTC

**Tese.** O resíduo da relação de log-preços ETH/BTC pode reverter após um desvio; vende-se uma perna e compra-se a outra em proporção estimada apenas com dados passados. A OLS local serve para construir um hedge aproximado, **não comprova cointegração** nem estabilidade futura do beta. A literatura clássica de pares é uma motivação de pesquisa, não evidência específica para ETH/BTC ([NBER](https://www.nber.org/papers/w7032)).

**Protocolo fixo exploratório.** Em cada fechamento H1 `t`, estimar `log(ETH)=α+β·log(BTC)` nas 120 barras completas de `t−120` a `t−1`. Calcular `σ` amostral dos resíduos dessa janela; `z` de `t−1` usa o mesmo ajuste e `z` de `t` é fora da janela. Exigir `0,1≤β≤5` e `σ>10⁻⁶`. Quando `z` passa de `≤−2` para `(−2,0)`, comprar ETH e vender BTC; quando passa de `≥2` para `(0,2)`, fazer o inverso. Executar no **open seguinte**. Distribuir notional bruto total em `1:β`, congelando α, β e σ durante a operação. Após fechar uma barra, agendar saída no open seguinte quando o z congelado atinge a média, chega a `−3` para posição comprada no spread ou `+3` para vendida, ou após 24 barras. Sem reentrada imediata durante uma saída. O encerramento na última abertura da janela é administrativo.

**Dados e custos.** Caches Binance spot BTCUSDT e ETHUSDT H1 sincronizados, de agosto/2024 (aquecimento) a agosto/2026, provenientes dos arquivos públicos e auditados pelo SHA-256 do manifesto local. A janela avaliada vai de 01/09/2024 a 01/09/2026 exclusivo. Capital fictício de 10.000 USDT, exposição bruta de 100% do patrimônio por posição e nenhuma alavancagem adicional. Cada execução de cada perna usa taxa de 0,10% sobre o preço preenchido mais slippage adverso de 0,02%. Não houve busca de parâmetros ou seleção posterior. Código reproduzível: `node scripts/research-pairs.mjs --self-test` e `node scripts/research-pairs.mjs`. Origem e formato: [Binance Public Data](https://github.com/binance/binance-public-data/blob/master/README.md).

| Operações | Líquido sobre capital inicial | Fator de lucro | Drawdown marcado |
| ---: | ---: | ---: | ---: |
| 313 | −54,36% | 0,449 | 55,45% |

**Conclusão limitada.** Esta regra fixa perdeu dinheiro nessa triagem; não há base para promovê-la a estratégia aprovada. O mesmo histórico já foi visto em outras pesquisas do projeto, portanto não é holdout intocado. A venda spot é hipotética: faltam disponibilidade de empréstimo, juros, margens, liquidação, lote mínimo e impacto reais. O drawdown usa marcação nos fechamentos com liquidação estimada, não pior percurso intrabar. Binance spot/USDT não equivale ao feed Kraken USD nem ao contrato da the5. Ruptura da relação e mudança de beta são riscos centrais. Para investigar outra hipótese de pares, registrar uma regra nova previamente e colher avaliação cronológica e prospectiva, sem rebatizar esta perda.

## N2 — carry de funding com hedge spot

**Tese.** Para o mesmo ativo, comprar spot e vender perpétuo em noção semelhante pode receber funding quando a taxa liquidada é positiva para a ponta vendida. O hedge de direção é aproximado; base, execução, liquidação e risco de venue permanecem. Funding é uma transferência entre posições compradas e vendidas no perpétuo, e só se aplica à posição aberta no instante de liquidação. A periodicidade e a taxa podem mudar ([Binance Futures](https://www.binance.com/en/support/faq/detail/360033525031)).

**Estado: aguardando dados; sem backtest e sem métricas.** Os caches locais contêm candles **spot** e não incluem histórico de funding realizado, preços de negociação/mark do perpétuo ou detalhes executáveis de margem. Não se pode inferir carry com OHLC spot nem atribuir funding futuro conhecido retrospectivamente. A [API oficial de futuros USDⓈ-M](https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) documenta histórico em `GET /fapi/v1/fundingRate` e preços mark. Uma triagem futura precisa juntar por timestamp esses eventos aos dados spot/perpétuo, calcular pagamento somente quando a posição estaria aberta, e descontar taxas, slippage, base, capital/margem e custo de oportunidade. O filtro de entrada deve usar apenas informação disponível no momento. Parâmetros e limites serão congelados antes de examinar resultados. A possibilidade de negociar perpétuo na conta indicada também depende do contrato da plataforma, ainda não estabelecido aqui.

## Integridade da triagem

O script verifica SHA-256, contagem, cobertura e continuidade H1 de ambos os caches antes de calcular resultados. O autoteste cobre exclusão do candle atual da regressão, direção do cruzamento e custos nas duas pernas. `validated:false` e os status no JSON representam pesquisa; nenhum número é prova de rentabilidade futura.

## Novas avaliações na revisão 0.6

N3 calendário semanal e N4 rotação transversal foram testadas sem reciclar EMA/Donchian ou a regressão N1. Ambas reprovaram em validação e período retrospectivo recente. Ver [N3](calendar/RELATORIO.md) e [N4](rotation/RELATORIO-N4.md), com protocolo congelado, resultados de stress, fontes e reprodução. Nenhuma aprovação operacional foi adicionada.
