# Open interest acquisition — N11

Aquisição de métricas públicas Binance USD-M para BTCUSDT, ETHUSDT e SOLUSDT. Somente warmup 31/12/2021 e desenvolvimento 2022–2024 foram baixados/lidos. Nenhum resultado, preço de retorno, sinal ou PnL foi calculado.

| Símbolo | ZIP verificados / esperados | Dias ausentes | Linhas raw | OI inválido | Off-grid excluídos | Duplicatas timestamp | Pontos 5m ausentes | H1 exatos presentes / esperados | Série normalizada |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 1097 / 1097 | 0 | 315805 | 450 | 0 | 0 | 131 | 26253 / 26304 | 315355 pontos |
| ETHUSDT | 1097 / 1097 | 0 | 315805 | 194 | 0 | 0 | 131 | 26277 / 26304 | 315611 pontos |
| SOLUSDT | 1097 / 1097 | 0 | 315788 | 183 | 2 | 0 | 151 | 26275 / 26304 | 315602 pontos |

A auditoria diária marca intervalos de 300 s ausentes e pontos inválidos; valores OI não positivos ou não finitos, timestamps fora da grade exata de 300 s (inclusive frações de segundo) e timestamps duplicados são excluídos somente da série normalizada, sem arredondar, truncar ou interpolar. Os ZIPs raw permanecem intactos no cache ignorado `research/cache/goal-seven/open-interest/raw/`; arrays JSON normalizados ficam em `research/cache/goal-seven/open-interest/normalized/`.
## Revisão da regra de timestamp
Série SOL anterior, antes desta correção: SHA-256 `2fbb5cb2b8ea7ffee36dd66458037ef2c3bd9146720b05b4f5f27b97e6b84d8f`. A regra anterior não exigia alinhamento de `create_time` à grade de 300 s. A regra agora exclui qualquer timestamp com segundos não divisíveis por 300 ou fração de segundo. Foram identificados para exclusão `2024-04-02T02:30:02Z` e `2024-04-02T06:00:01Z`; os ZIPs raw permanecem inalterados.

`create_time` é texto sem timezone no schema do CSV. A auditoria comparativa da tarefa principal encontrou timestamp REST oficial = create_time interpretado UTC + 300 s em 11/11 amostras sobrepostas por ativo (33 total, BTC/ETH/SOL; 2026-09-27). A amostra REST 00:00 exigiria o arquivo do dia anterior, fora daquela comparação. Isso apoia UTC como convenção de trabalho, mas não prova regra estável nem atraso de publicação para todos os anos; point-in-time permanece bloqueado. A normalização aqui mantém o create_time sem deslocamento; observation-end +300 s pertence à integração principal. A cobertura warmup inclui create_time de 31/12/2021; a primeira falta H1 observada é 07/03/2022 15:55 UTC, não no warmup. Arquivos pós-2024 aparecem apenas no resumo de listagem; não foram baixados nem lidos.

`python scripts/download-goal-open-interest.py --verify` verifica somente arquivos locais.
