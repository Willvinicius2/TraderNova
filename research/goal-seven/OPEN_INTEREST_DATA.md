# Binance USD-M open interest — dados históricos

Auditoria de `IDEIAS.md` e `protocol.json`, fontes públicas oficiais e uma amostra arquivada. A aquisição da amostra foi em memória; nenhum cache do projeto foi alterado. Sem PnL, tuning ou ordens.

## Disponibilidade verificada

O arquivo oficial é publicado em `https://data.binance.vision/data/futures/um/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-YYYY-MM-DD.zip`. Verifiquei que o objeto `2021-12-01` existe (HTTP HEAD 200) para **BTCUSDT, ETHUSDT e SOLUSDT**; BTC também tem objeto em 2021-11-30. ETH/SOL retornaram 404 em 2021-11-30. Assim, a cobertura comum está comprovada **desde ao menos 01/12/2021**; não afirmo continuidade diária sem inventariar e conferir cada arquivo. O arquivo é gratuito e não exige API key na rota estática.

A amostra foi `BTCUSDT-metrics-2023-01-21.zip`, 14.678 bytes, caminho oficial acima, SHA-256 `26741cd9e8821698129050eb998698ba4672571c30012dd4e80913002c58d35c`. O `.CHECKSUM` oficial reportou exatamente o mesmo hash. Dentro do CSV há 288 timestamps únicos de `create_time`, de `2023-01-21 00:00:00` a `23:55:00`, espaçados em 300 s. A coluna é texto de data/hora; confirmar UTC com convenção/documentação da Binance e normalizar explicitamente antes do join com candles UTC.

Campos amostrados, conforme o cabeçalho oficial: `create_time`, `symbol`, `sum_open_interest`, `sum_open_interest_value`, `count_toptrader_long_short_ratio`, `sum_toptrader_long_short_ratio`, `count_long_short_ratio`, `sum_taker_long_short_vol_ratio`. O foco em OI dá quantidade agregada e valor total; os demais campos são proporções de contas/posições de top traders, todas as contas e volume taker, respectivamente. A amostra não prova cobertura nem completude para todo período/símbolo; o repositório oficial alerta que arquivos públicos podem ser atualizados/corrigidos.

O REST `/futures/data/openInterestHist` permite períodos 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h e 1d (limite 500), mas a documentação diz que só há dados do último mês. Logo, o histórico longo deve vir dos arquivos `daily/metrics`, não de uma consulta retrospectiva ao endpoint. Fontes primárias: [Binance Public Data](https://github.com/binance/binance-public-data), [exemplo oficial de métricas arquivadas](https://github.com/binance/binance-public-data/issues/211) e [documentação USDⓈ-M Open Interest Statistics](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data).

## Interpretação e limites

`sum_open_interest_value` é nocional de cotação; ele pode cair apenas porque o preço caiu, mesmo com a quantidade em aberto estável. Compare-o com `sum_open_interest` e o preço perp correspondente: uma queda simultânea de quantidade e nocional é compatível com redução de contratos/quantidade aberta; quantidade estável com nocional em queda é compatível com reprecificação. Para contratos lineares USD-M, a quantidade deve ser interpretada na unidade de contrato/ativo definida pelo instrumento; não inferir diretamente “número de posições” sem confirmar o multiplicador. A documentação nomeia os campos como OI total e valor total, mas não descreve no esquema métrico um contador de contas individuais.

OI agregado não informa se os fechamentos vieram de liquidações ou saídas voluntárias, quem perdeu alavancagem, direção líquida dos participantes ou margem utilizada. Todo contrato aberto mantém contraparte long e short; uma série de OI não revela viés direcional líquido. Volume de liquidações e preço isoladamente também não provam deleveraging. Portanto OI + preço ajuda a distinguir variação de exposição agregada de mero efeito de preço no nocional, mas não basta para afirmar “desalavancagem” causal.

Antes de usar a série como filtro/sinal, exigir manifest por símbolo/dia com checksum oficial, duplicatas/gaps e timestamps auditados; cruzar com preço e mark/index da mesma venue e frequência; documentar unidade/multiplicador; manter decisão somente após a publicação observada e testar sua disponibilidade causal. `IDEIAS.md` já fixa que novas regras/alterações devem ser congeladas como variante da mesma família. Nenhuma alteração foi proposta aqui.
