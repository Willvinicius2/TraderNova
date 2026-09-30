# Fontes gratuitas para N17/N20 — 30/09/2026

Pesquisei fontes primárias. O inventário já cobre tendências, rompimentos, reversão, calendário e N16–N20; não proponho troca de indicador como hipótese inédita. Isso é pesquisa de dados, não aprovação: candidatos continuam aguardando dados; zero estratégias aprovadas.

## N20 — CPI-surpresa: sinal econômico possível, ainda não executável

- **Actual e timestamp:** [arquivo BLS de releases CPI](https://www.bls.gov/bls/news-release/cpi.htm) tem releases preservados desde 1994, e cada PDF contém os valores publicados, além de avisos sobre revisão sazonal. Exemplo real pequeno: release de 15/01/2025, CPI core mensal dez/2024 = **+0,2%**; headline 12 meses = **2,9%** ([PDF BLS](https://www.bls.gov/news.release/archives/cpi_01152025.pdf)). A própria página BLS documenta que índices SA podem ser revisados cinco anos. Use o vintage PDF, não séries atuais revisáveis, para actual.
- **Consenso PIT:** [Cleveland Fed Inflation Nowcasting](https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting) fornece nowcasts diários desde 2014, contudo é modelo do Fed regional, não mediana de consenso de mercado. A visualização histórica pode ser consultada; não confirmei arquivo público baixável de valores com timestamp de cada dia/versão. Fonte oficial prova série e cadência, mas não reconstrói, sozinha, o consenso observável antes de cada release. Proposta conservadora: congelar regra para **nowcast**, abandonando o rótulo “surpresa de consenso”, apenas após obter export histórico versionado/arquivado; o candidato atual não deve ser alterado silenciosamente.
- **Preço/execução:** sem feed gratuito primário encontrado para EURUSD M5 com bid/ask histórico. OHLC de terceiro ou spot de referência não prova execução. Congelar decisão no fechamento da primeira barra M5 pós-release; entrada no primeiro bid/ask registrado depois; custo completo + spread e slippage observados, stop e saída originais. Bloqueio: consenso PIT e preço FX executável ainda ausentes. CPI é mensal; janela efetiva é pequena.

## N17 — ETF BTC: primário não equivale a fluxo diário PIT

- [iShares IBIT](https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf) publica holdings CSV e shares outstanding/NAV correntes; produto começou em jan/2024. Páginas abertas confirmam holdings (BTC) e dados correntes, não um arquivo gratuito completo de shares outstanding diário com hora de publicação e versões. Relatórios SEC/N-PORT permitem checagem de patrimônio/ações em datas reportadas, porém são periódicos e atrasados; não servem para sinal diário sem look-ahead.
- **Não confundir:** variação de AUM ou BTC em holdings mistura fluxo, preço e taxa; não reproduz criação/resgate líquido sem shares/basket e timestamp. Farside é agregador, não fonte primária. Não consegui verificar fluxo diário primário histórico PIT gratuito que cubra o conjunto de ETFs necessário aos parâmetros N17.
- Regra original pode ficar congelada (z-score 60 observações, EMA20, preço BTC, entrada após publicação, stop 1 ATR, horizonte 120h); registrar snapshot bruto no instante e cobrar spread, taxa, funding se perpétuo e slippage. Sem arquivo histórico e sem cotação executável, N17 fica **bloqueado por disponibilidade**, não reprovado.

## Hipótese econômica inédita? Nenhuma adicionada

A única via útil seria uma variante de N20 baseada em nowcast, mas ainda é troca do dado/sinal da família macro-surpresa, não mecanismo novo. N17 é demanda de ETF publicada, já registrada. Evitei inflar a contagem com mudanças de limiar/indicador.

## Conclusão operacional

N20 tem arquivo oficial de actual PIT; confirmação não cobre consenso nem preço de execução. N17 tem dados correntes do emissor e registros regulatórios periódicos, sem fluxo diário arquivado demonstrado. Falta de fonte não é teste negativo nem reprovação: nenhum retorno foi calculado. URLs acima verificadas em 30/09/2026. Nenhuma operação financeira foi executada.
