# Inventário de dados — objetivo de sete estratégias

Auditoria somente de leitura em 28/09/2026. Arquivos de origem em `research/cache/` são locais/ignorados pelo Git; o export MT5 está fora do repositório. Isto descreve dados e histórico pesquisado, sem validar estratégias.

## Fontes e cobertura local

| Ativo/fonte | Arquivos e mercado | Granularidade/cobertura | Campos e limitações |
|---|---|---|---|
| BTCUSDT, ETHUSDT, SOLUSDT — Binance Spot | `research/cache/manifest.json`; OHLCV spot | M15 e H1 de 2024-08-01 a 2026-09-01 (inclusive até 31/08); 73.056 M15 e 18.264 H1 por ativo | OHLC e volume negociado do candle; sem bid/ask histórico, funding, swap ou taxas observadas por fill. Spot não é perp nem contrato da mesa. |
| Mesmos três símbolos — Binance Spot v3 | `research/cache/v3/manifest.json`, `research/cache/v3/{BTC,ETH,SOL}USDT-1h.json` | H1 de 2021-12-01 a 2026-09-01; 41.639 barras por ativo; há lacuna comum documentada em 23/03/2023 (duas horas ausentes, sem interpolação) | OHLCV spot; sem bid/ask ou funding. V3 usou desenvolvimento 2022–24, validação jan/2025–fev/2026 e retrospectiva mar–ago/2026, esta já conhecida. |
| EURUSD — HistData | `research/cache/histdata/EURUSD2010_15`, `EURUSD2019`, `EURUSD2020_21`, `EURUSD2024` | CSV agregados M15/H1/H4. Há dados de M1 subjacentes para 2010–15, 2019, 2020–21 e 2024. Os quatro manifests registram 2.192.148, 372.470, 741.717 e 372.379 minutos; gaps registrados e barras incompletas excluídas. | OHLC do lado Bid; timezone original EST fixo UTC−5 (sem DST), convertido para UTC. Sem spread, Ask ou volume real; `spread=0` no derivado significa ausência, não custo zero. Feed indicativo externo, não cotação executável da mesa. |
| EURUSD — HistData bruto | `research/cache/histdata-raw/` | Manifest registra anos 2010–25 e meses jan–ago/2026 (M1), além dos arquivos normalizados listados acima. | ZIPs preservam hash/URL, mas a coleta está marcada incompleta; há dados ainda não convertidos em CSV agregado (inclusive 2016–18, 2022–23 e 2025–ago/2026). |
| NSXUSD / Nasdaq-100 — HistData | `research/cache/histdata-raw/` | Manifest contém M1 Bid OHLC para 2010–13. Existe também ZIP 2014 na pasta, mas não consta do manifesto verificado. Não achei série normalizada. | Sem spread, Ask ou volume real; sem confirmação de equivalência com NAS100, feed/horário/contrato do usuário. Não tratar `NSXUSD` como NAS100 executável. |
| XAUUSD — Five Percent Online via MT5, export somente leitura | `D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration/XAUUSD_{M15,H1,H2,H4,H6,H12}.csv`; `market_metadata.json` | M15: 99.999 barras, 21/06/2022–10/09/2026; H1: 99.999, 20/08/2009–10/09/2026; H2 67.993, H4 34.089, H6 22.801, H12 11.426, estes quatro de 11/06/2004 a 10/09/2026. Metadados indicam CFD, contrato 100 oz/lote, passo/tick 0,01. | OHLC, tick_volume, spread e real_volume em colunas. Candle não tem caminho intrabar/ticks; real_volume pode não significar negócios centralizados em CFD. Spread é coluna da barra, não histórico de bid/ask completo; swap e comissões históricas não disponíveis. Metadados pontuais indicam spread flutuante e swaps long/short −89,1, rollover triplo quarta; não generalizar esse snapshot. Horário MT5 nativo: diferença de relógio observada de 10.772 s em 10/09/2026, não interpretar labels como UTC confiável. |
| XAUUSD — pesquisas salvas | `research/cache/gold-v1/`, `research/cache/gold-h1-v2/`, `public/research/gold-v1*.json`, `public/research/gold-h1-v2*.json` | M15 v1 usou 22/06/2022–10/09/2026; H1 v2 teve desenvolvimento 2010–15. | São resultados/simulações grandes, não fontes de cotação adicionais. Custos foram cenários fixos; não há swap histórico executável. Documentação registra reprovação das famílias pesquisadas. |

Não encontrei no cache séries locais adicionais para NAS100, nem barras de futuros perpétuos de cripto com funding. Scripts relevantes: `scripts/download-history-v3.py`, `scripts/import_histdata.py`, `scripts/download_histdata.py`, `scripts/export_mt5_history_readonly.py`, `scripts/run_gold_research.py`, `scripts/run_gold_h1_research.py`, `scripts/backtest_fx_families.py`, `tests/calibration-research.mjs`, `tests/calibration-v3.mjs`. Os manifests de Binance documentam OHLCV; o protocolo FX documenta M1 Bid OHLC sem spread/volume real.

## O que já foi examinado e janelas fechadas por rodada

- Meta anterior continua em 0 estratégias aprovadas. `research/META_CINCO_ESTRATEGIAS.md` relata cripto inicial 18 combinações sem aprovação, ouro M15 cinco famílias reprovadas e ouro H1 v2 sete configurações reprovadas no desenvolvimento. `research/CALIBRACAO_V3.md` registra que nenhuma das nove combinações T1–T3 passou adoção. Não somar presets, ativos ou timeframes como estratégias novas.
- Para candidatas do protocolo XAU H1 v2, 2010–15 foi desenvolvimento; 2016–18 (validação) e 2019–21 (reserva) não foram calculadas após reprovação no desenvolvimento. 2022–ago/2026 foi apenas diagnóstico conhecido; não é holdout intocado. Essa afirmação vale para aquelas candidatas/rodada, não para todo o histórico de XAU pesquisado fora dela.
- Os screens FX presentes referenciam EURUSD H1 de `EURUSD2010_15` como desenvolvimento e `EURUSD2020_21` como validação; existe triagem com pares e versão simétrica (`research/fx-screen-*_*.json`). 2019 e 2024 têm dados normalizados; outros anos/mês estão somente brutos no manifesto. O protocolo externo avisa que esses períodos foram usados por pesquisa anterior. Portanto não há base para chamar 2019, 2024 ou 2025–ago/2026 de período globalmente não examinado. Para NSXUSD não localizei resultado de tela no inventário; a cobertura 2010–13 continua apenas aquisição bruta não certificada.
- O ouro M15 v1 desenvolveu em jul/2022–dez/2024 e validou em 2025; o período recente e janelas finais aparecem em pesquisa anterior. Não anunciar período recente como virgem.

## Integridade verificável

Hashes abaixo são SHA-256 do conteúdo do arquivo. Binance também registra o hash de cada série no manifest v3; os três valores foram recalculados localmente e conferem. O `selection.json` da exportação MT5 registra hashes que também conferem para os CSVs listados.

| Arquivo | SHA-256 |
|---|---|
| `research/cache/v3/manifest.json` | `d2b8b4833d2e3f1d48a187fffb626339e52f9c76f744618b80ed5512440c8d93` |
| `research/cache/v3/BTCUSDT-1h.json` | `eec6d00f0a38d5658b16c53928aed72cea3f1c925c8c73850ea75888c2ced678` |
| `research/cache/v3/ETHUSDT-1h.json` | `e476a43feed4716a833cbccfc6061816d19e722a8e439da0b8ff0b90f56a1ff3` |
| `research/cache/v3/SOLUSDT-1h.json` | `33393a1c43d34808db5755e905f3c3205eb836bbff9728e047830f894bd235f4` |
| `research/cache/histdata-raw/manifest.json` | `fcbe8ccc0fbcc0e07ae920bf08cb48f012805d663225a13dfea19553ff1eb732` |
| `research/cache/histdata/EURUSD2010_15/EURUSD_H1.csv` | `590412b6303d552275235108acd89518f3c73ef86c71e0de04ab298fe58d97ac` |
| `research/cache/histdata/EURUSD2019/EURUSD_H1.csv` | `e1e667dadca514fad97af0f30db5e4c371c840a2fd2619e9b97f8bb511f6c38d` |
| `research/cache/histdata/EURUSD2020_21/EURUSD_H1.csv` | `cf30afaac482d5abef645e82c08eb98e48a4fd7c580a9aba9290637a4e10e9f8` |
| `research/cache/histdata/EURUSD2024/EURUSD_H1.csv` | `83adf52ad6788fbcfa4d7cd0af35848a58a0efdfff255d7f33bb54e5a7361347` |
| `D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration/XAUUSD_M15.csv` | `f0bb3612b16661118e30689ebf71f34b0a02914fd4565837b8cddefe8aa52583` |
| `D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration/XAUUSD_H1.csv` | `9bb7ebfe239fb62c98cc7882c1a5e3c076bbf89fbfa91e829d9457599ef9b263` |
| `D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration/XAUUSD_H4.csv` | `ae72d49637d9dacf48616a6229114ec8dfa1d6afb6fd16bcea2668e142731a58` |
| `D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration/XAUUSD_H12.csv` | `9f59f56b2586eef96c0a88e958580c2055eefd8dc4b7a14b7acaf206dfb531be` |

## Lacunas e fonte gratuita sugerida

Maior carência para uma meta de sete estratégias distintas: cobertura incompleta por ativo e ausência de custo executável observável. Em cripto, a pesquisa atual é spot; não confundir com perp nem extrapolar sem funding/taxas. Em FX/índice, HistData é um feed indicativo Bid de M1 sem spread. No ouro há OHLC/tick volume e um snapshot de spread/swap, mas não ticks Bid/Ask ou swap histórico. NAS100 carece de série normalizada e verificação de contrato. Nenhum desses dados sozinho prova resultado líquido ou drawdown intrabar baixo.

Uma busca focada na fonte primária encontrou o exportador histórico oficial Dukascopy, que informa preços Bid e Ask e volumes: [Historical Data Export](https://www.dukascopy.com/api/data/get/historical-data-export). É uma opção gratuita para construir referência independente de EURUSD/XAUUSD e verificar disponibilidade do índice NAS100 no seletor; o feed/instrumento ainda não corresponderia automaticamente ao contrato The5ers. Para qualquer fonte escolhida, congelar instrumento, sessão/fuso, granularidade, custos e hash antes de abrir janelas de avaliação.
