# Worker de ingestão (Etapa 3)

Processo local, **somente sinais de pesquisa**: não envia ordens, não usa credenciais de corretora e não usa dados sintéticos fora dos testes.

## O que faz
1. Consulta o OHLC público da Kraken (REST) para **um** par/intervalo por vez (BTCUSD, ETHUSD ou SOLUSD; 15 ou 60 min), reaproveitando `parseKrakenHistory`.
2. Grava só candles **fechados** (`open_time + intervalo <= agora`). A última linha da Kraken (candle aberto) nunca é gravada; fica só em memória para o motor ter a abertura do candle seguinte.
3. A cada novo fechamento, com o feed `ao_vivo`, chama `evaluatePaperEngine` (regras e presets inalterados). Cada leitura `buy` vira um `SignalRecord` com `mode: 'research'`. `strategyApprovals` continua vazio, então **nunca** há `alert`.
4. Sinal só é gravado dentro da janela de entrada do motor (fechamento + 30 s); fora dela é descartado com log `sinal_descartado`. Por isso, logo após a virada do candle o worker consulta a cada 5 s até avaliar.

## Como rodar
```bash
npm run install:ci          # uma vez
npm run worker              # laço contínuo (Ctrl+C encerra após terminar o ciclo atual)
npm run worker:once         # um ciclo; código de saída 1 se a consulta falhar
npm run worker -- --pair ETHUSD --interval 15 --poll-seconds 20
```
PowerShell:
```powershell
npm run install:ci
$env:TRADERNOVA_WORKER_PAIR = "BTCUSD"; $env:TRADERNOVA_WORKER_DATA_DIR = "C:\tradernova-dados"
npm run worker
npm run worker -- --log-file logs\worker.jsonl
```
Opções (flag > variável de ambiente > padrão):

| Flag | Variável | Padrão |
|---|---|---|
| `--pair` | `TRADERNOVA_WORKER_PAIR` | `BTCUSD` |
| `--interval` (15 ou 60) | `TRADERNOVA_WORKER_INTERVAL` | `60` |
| `--poll-seconds` (5 a 600) | `TRADERNOVA_WORKER_POLL_SECONDS` | `30` |
| `--data-dir` | `TRADERNOVA_WORKER_DATA_DIR` | `worker-data` |
| `--log-file` | `TRADERNOVA_WORKER_LOG_FILE` | (só stdout) |
| `--http-port` (1 a 65535) | `TRADERNOVA_WORKER_HTTP_PORT` | `8790` |
| `--no-http` | - | servidor de leitura ligado |
| `--once` | - | laço |

## Leitura de sinais por HTTP
No laço contínuo (`npm run worker`, nunca em `--once`) o worker abre um servidor somente leitura em `127.0.0.1` (sem CORS) com **uma** rota: `GET /signals/:id` (200 registro, 404 desconhecido, 400 ID inválido, 405 outros métodos). Lê o JSONL do disco a cada chamada. Porta ocupada encerra o worker com código 2 (use `--http-port` ou `--no-http`). Quem consome é `/api/signals/[id]` do app; ver [`SINAIS.md`](SINAIS.md).

## Como o TypeScript é executado
`node worker/cli.mjs` registra `worker/ts-loader.mjs` (hooks do Node) que transpila `.ts` com o pacote `typescript` já instalado e resolve imports sem extensão e o alias `@/`. Escolhido porque `--experimental-strip-types` não resolve os imports sem extensão de `lib/`. Zero dependências novas; os testes usam o mesmo carregador.

## Dados (`worker-data/`, ignorado pelo git)
```
candles/kraken-spot_BTCUSD_60m.jsonl      candles fechados, um JSON por linha, ordem crescente
checkpoints/kraken-spot_BTCUSD_60m.json   lastClosedOpenTime, lastSuccessAt, lastEvaluatedOpenTime
signals/kraken-spot_BTCUSD_60m.jsonl      SignalRecord (contrato lib/tradernova/signal-record.ts)
```
- Deduplicação por `open_time`. Candle "corrigido" para um `open_time` já gravado: **mantém o primeiro** e registra `candle_corrigido_ignorado` (a evidência de sinais já emitidos não muda depois do fato).
- Lacunas são registradas (`lacuna_detectada`). O motor bloqueia qualquer lacuna, então o worker avalia só a cauda contígua; abaixo de 201 candles o estado é `historico_insuficiente`.
- Checkpoint é gravado de forma atômica (arquivo `.tmp` + rename). Ao reiniciar: carrega o armazém e o checkpoint e consulta a Kraken com `since` = último fechamento. Linha final truncada por queda de energia é ignorada.
- Sinais: chave de deduplicação separada do ID público (UUID); reavaliar o mesmo candle após reinício não cria segundo registro.

## Estados do feed
| Estado | Condição (nesta ordem) |
|---|---|
| `desconectado` | nunca houve consulta com sucesso, ou a última falhou |
| `atrasado` | último sucesso há mais de 3 consultas (3 x poll), ou candle fechado mais novo com `open_time` mais velho que 2 x intervalo |
| `historico_insuficiente` | menos de 201 candles fechados contíguos |
| `ao_vivo` | demais casos |

Fora de `ao_vivo` o worker **não avalia nada** e registra `avaliacao_ignorada` com o motivo. Nenhuma execução é inventada após interrupção.

## Logs
Uma linha JSON por evento em stdout (e no arquivo, se configurado): `ts, level, event, provider, symbol, interval`, mais `feed_state`, `candle_open_time`, `strategy`, `strategy_version` e contadores quando aplicável. Não há segredos.

## Limites
- A Kraken devolve no máximo 720 candles recentes; lacunas maiores que isso não são recuperáveis.
- Um par/intervalo por processo (rode vários processos com `--data-dir` diferente se precisar).
- Sinais apenas de pesquisa; sem push/notificação ainda.
- Supabase não está integrado: o armazém em arquivo (`openFileSignalStore`, implementa `SignalStore`) é o adaptador até lá.
- O relógio do computador é a referência de "agora"; mantenha-o sincronizado.
