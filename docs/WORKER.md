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
| `--pairs` (lista, ex. `BTCUSD,ETHUSD,SOLUSD`) | `TRADERNOVA_WORKER_PAIRS` | valor de `--pair` |
| `--intervals` (lista, ex. `15,60`) | `TRADERNOVA_WORKER_INTERVALS` | valor de `--interval` |
| `--signal-store` (`file` ou `supabase`) | `TRADERNOVA_WORKER_SIGNAL_STORE` | `file` |
| `--no-http` | - | servidor de leitura ligado |
| `--once` | - | laço |

## Vários pares em um processo
`npm run worker -- --pairs BTCUSD,ETHUSD,SOLUSD --intervals 15,60` cria um worker por combinação (6 aqui), cada um com seus arquivos e checkpoint, no mesmo formato de antes. As consultas à Kraken rodam em sequência a cada rodada. A falha de um par é registrada no log com o `symbol` dele e não interrompe os outros; em `--once` o código de saída é 1 se qualquer combinação falhou.

## Saúde do worker (heartbeat)
Ao fim de cada ciclo, com ou sem sucesso, o worker grava a saúde de cada combinação: horário do ciclo, último sucesso, estado do feed e último candle fechado. Com o armazém em arquivo, vai para `worker-data/status/<provedor>_<par>_<intervalo>m.json` e o servidor local expõe `GET /status`. Com o Supabase, vai para a tabela `public.worker_status` (migração `202610200001`). A rota `/api/worker-status` lê da mesma fonte que `/api/signals` e calcula a saúde com o relógio do servidor: **ativo** (último ciclo dentro de 2 consultas + 1 min), **atrasado** (até 15 min ou 6 consultas) ou **parado**. A aba Robô mostra isso. Com o worker atrasado ou parado, o feed aparece como "último estado", nunca como ao vivo. Uma falha ao gravar a saúde só gera o aviso `saude_nao_gravada`.

## Gravar sinais no Supabase
Com `--signal-store supabase` o worker grava em `public.research_signals` em vez do JSONL. Precisa de `TRADERNOVA_SUPABASE_URL` (https) e `TRADERNOVA_SUPABASE_SERVICE_KEY` **só no ambiente** (nunca por flag, para não aparecer na lista de processos). Faltando qualquer uma, o worker encerra com código 2 (`configuracao_invalida`). Nesse modo o servidor de leitura local não sobe: a rota da web lê direto do Supabase. Os candles continuam em `--data-dir`.

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
- Vários pares/intervalos por processo com `--pairs`/`--intervals`; as consultas são sequenciais.
- Sinais apenas de pesquisa; sem push/notificação ainda.
- Armazéns de sinais: arquivo (`openFileSignalStore`, padrão) ou Supabase (`supabaseSignalStore`), ambos implementam `SignalStore`.
- O relógio do computador é a referência de "agora"; mantenha-o sincronizado.
