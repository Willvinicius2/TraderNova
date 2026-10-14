# Sinais persistidos (Etapa 2)

Contrato único de um sinal e o caminho que ele percorre até a ficha no app. Só sinais de **pesquisa ou teste**: nenhuma estratégia está aprovada (`strategyApprovals` vazio), então não existe modo `alert` na prática, e nenhuma ordem é enviada.

## Contrato (`lib/tradernova/signal-record.ts`)
- **`publicId`**: UUID v4 opaco (`newPublicSignalId`). É o único identificador que aparece em links (`?aba=robo&sinal=<uuid>`, `tradernova://signal/<uuid>`) e não concede acesso por si só.
- **`dedupKey`**: `estratégia@versão|provedor|instrumento|timeframe|lado|signalTime` (`signalDedupKey`). Serve só para não gravar o mesmo sinal duas vezes e **nunca** vai para links. Contém `:`/`|` de propósito, para não ser aceita como ID.
- **Modos**: `research` (rótulo "Pesquisa"), `test` ("Teste") e `alert` (reservado; sem estratégia aprovada não é emitido).
- **Estados** (`resolveSignalView`): `active`, `expired`, `invalidated`, `not-found`, `invalid-id`, `unauthorized`. A rota acrescenta `source-unavailable` (com `reason`: `not-configured`, `unreachable` ou `invalid-response`). Um ID desconhecido nunca cria nem substitui um sinal.
- O motor no navegador (`manualOpportunity`) usa o mesmo contrato: devolve `publicId` e `dedupKey` separados. O campo `id` antigo (`T1:T1-E0X0:<candle>`) foi removido porque o `:` era recusado pelo link do mobile. Essas oportunidades vivem só na memória da tela e a lista deduplica por `dedupKey`; elas só ganham ficha quando um registro com aquele `publicId` for persistido. Hoje o motor do navegador não emite nada (sem aprovação) e quem grava registros é o worker.
- Sessões salvas (`tradernova-forward-*` no localStorage) nunca guardaram esse id (usam candidato, preset e `lastSignalTime`); portanto nada precisa de migração e as sessões antigas continuam válidas.

## Fluxo
```
worker (research) -> signals/*.jsonl (armazém em arquivo)
   -> servidor de leitura do worker  GET http://127.0.0.1:8790/signals/:id
   -> app: GET /api/signals/:id  (app/api/signals/[id]/route.ts)
   -> ficha (components/tradernova/signal-sheet.tsx) na aba Robô
```
- **Worker** (`npm run worker`): além de gravar, sobe um servidor `node:http` só em `127.0.0.1` (porta `--http-port` / `TRADERNOVA_WORKER_HTTP_PORT`, padrão `8790`; `--no-http` desliga; `worker:once` nunca abre porta). Expõe apenas `GET /signals/:id`: 200 registro, 404 desconhecido, 400 ID inválido, 405 outros métodos. Lê o arquivo a cada requisição (sem cache) e não envia CORS: quem consulta é o servidor web.
- **Rota `/api/signals/[id]`** (somente GET, `Cache-Control: no-store`): valida o UUID, lê pelo adaptador escolhido por ambiente, valida o registro com `signalRecordSchema` e devolve `{state, record?}`. Registro malformado, outro `publicId`, erro HTTP, corpo grande demais ou tempo esgotado (3 s) viram `source-unavailable`, nunca um sinal. Sem a variável abaixo, responde `503 source-unavailable/not-configured`: nunca há exemplo ou fixture no lugar. A autorização por usuário ainda não existe (`unauthorized` não sai hoje); o ponto de encaixe está em `lookupSignal(..., authorize)`.
- **Ficha**: abre quando a página carrega com `sinal=<id>` (força a aba Robô) e mostra carregando, ativo (ativo, direção, fonte, timeframe, estratégia/versão, geração, validade com contagem, entrada, stop, alvo, evidências e selo do modo), expirado, invalidado (com motivo), não encontrado ("Sinal não encontrado. Nenhum sinal foi criado no lugar."), ID inválido e fonte indisponível ("A fonte de sinais não está conectada neste ambiente."). O texto digitado em `sinal` nunca é exibido. A busca antiga em `tradernova-demo-v1` foi removida; os exemplos de demonstração do Diário continuam locais, mas já não geram `?sinal=`.

## Variáveis de ambiente
| Variável | Onde | Efeito |
|---|---|---|
| `TRADERNOVA_SIGNAL_SOURCE_URL` | app web | URL base do worker (ex.: `http://127.0.0.1:8790`). Ausente ou não http/https: fonte não conectada. |
| `TRADERNOVA_WORKER_HTTP_PORT` | worker | Porta do servidor de leitura (padrão 8790). |

O app roda no runtime do Cloudflare (workerd): variáveis do shell **não** chegam à rota por padrão. Use um arquivo `.env` na raiz (ignorado pelo git) ou `CLOUDFLARE_INCLUDE_PROCESS_ENV=true` junto com a variável.

## Testar localmente (Windows / PowerShell)
Terminal 1:
```powershell
npm run install:ci   # uma vez
npm run worker
```
Terminal 2 (uma das duas formas):
```powershell
# A) arquivo .env na raiz, com a linha: TRADERNOVA_SIGNAL_SOURCE_URL=http://127.0.0.1:8790
npm run dev

# B) variáveis só nesta sessão
$env:CLOUDFLARE_INCLUDE_PROCESS_ENV = "true"
$env:TRADERNOVA_SIGNAL_SOURCE_URL = "http://127.0.0.1:8790"
npm run dev
```
Abra `http://localhost:5173/?aba=robo&sinal=<uuid>` com um `publicId` de `worker-data\signals\*.jsonl`. Um UUID desconhecido mostra "não encontrado"; sem a variável, "fonte não conectada". Também dá para consultar direto: `Invoke-RestMethod http://localhost:5173/api/signals/<uuid>`.

## Ainda não existe
Supabase substituirá o armazém em arquivo (a rota passa a usar outro adaptador de `SignalSource`); login/autorização por usuário; hospedar o worker; push; sinais `alert`.

## Testes
`tests/signal-record.mjs` (contrato), `tests/signal-route.mjs` (rota com `fetch` simulado, modelo da ficha, servidor de leitura do worker em porta efêmera e regressão do ID do motor), `tests/worker.mjs` e `mobile/tests/site.mjs` (deep link só com UUID).
