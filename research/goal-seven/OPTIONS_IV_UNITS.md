# N13 — unidade documentada do campo `iv`

## Resultado

**Não foi possível confirmar a escala percentual apenas pela documentação oficial consultada.** A Deribit documenta o campo de negócio `iv` como a volatilidade implícita da opção correspondente ao preço do negócio, tipa-o como número e mostra `45.91` num exemplo. A definição, porém, não diz se esse valor está em pontos percentuais, se deve ser dividido por 100, ou se a convenção é anualizada. Assim, a afirmação “45.91 significa 45.91% a.a., equivalente a σ=0.4591” é plausível e coerente com a apresentação usual de IV, mas **não está explicitamente confirmada pelo contrato documental do campo**.

O `mark_iv`, `bid_iv` e `ask_iv` da API de ticker também são definidos como IV associada ao mark/bid/ask, sem escala expressa. Esses são campos de cotação/mark e não substituem o `iv` do negócio para N13.

## Fontes primárias consultadas

- A [especificação oficial de `public/get_last_trades_by_currency_and_time`](https://docs.deribit.com/api-reference/market-data/public-get_last_trades_by_currency_and_time) documenta `result.trades.iv` como IV do preço da opção e o exemplo JSON contém o número `45.91`; não atribui unidade nem fator de escala ao número.
- A [especificação oficial de `public/ticker`](https://docs.deribit.com/api-reference/market-data/public-ticker) define `bid_iv`, `ask_iv` e `mark_iv` como IV dos respectivos preços, também sem unidade ou fator de escala.
- O [guia oficial de coleta de dados de opções](https://docs.deribit.com/articles/options-data-collection-best-practices) distingue campos de IV de trades, tickers e mark-price streams, mas não resolve a escala de `result.trades.iv`.

Nenhuma série, trade ou endpoint foi consultado nesta checagem. Até a Deribit documentar a escala explicitamente, o parser não deve tratar `iv` como pontos percentuais por suposição; registre a unidade como não confirmada antes de congelar o cálculo de skew.
# Decisão metodológica antes de qualquer sinal ou PnL

A regra N13 usa apenas o sinal do skew e sua comparação com um percentil passado. Multiplicar todos os valores de IV por uma mesma constante positiva multiplica o skew e o percentil pela mesma constante, preservando a decisão. Portanto, o estudo usará a unidade nativa do campo `iv`, sem convertê-la nem afirmar percentual ao ano. Isso permite adquirir e auditar bytes sem resolver uma unidade absoluta que a regra não utiliza. Não demonstra constância histórica da semântica do campo; misturas de convenções ou revisões continuam sendo riscos de fonte. O protocolo final deve manter essa convenção antes dos testes. Esta é uma decisão de desenho do pesquisador, não uma afirmação adicional atribuída à Deribit.
