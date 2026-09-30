# Revisão do contrato round 6

Revisão somente leitura do exportador e do importador offline.

## Riscos concretos

- **Comissão: resolvido no parser, custo continua bloqueado.** A versão atual exige `commission_status=unknown` e o literal `unknown_requires_broker_confirmation`; `commission` não é convertido em zero ou número. Saída mantém blocker e `approval.costs=false`.
- **Escaping CSV: parser coberto por fixtures sintéticas, interoperabilidade pendente.** Testes cobrem duas serializações plausíveis via `csv.writer`, mas não fixture real do `FileWrite`; o parser decide a remoção pela presença de wrapper residual no símbolo. `actual_mt5_fixture_verified=false`. Validar arquivo real com vírgula, aspas e Unicode antes de confiar na importação. Exportador usa `CP_UTF8` para CSV e metadata; parser lê UTF-8 estrito com BOM opcional.
- **Encoding: alinhado estaticamente.** Exportador abre CSV e metadata com `CP_UTF8`; parser decodifica ambos como UTF-8 estrito. Amostra MT5 real ainda pendente.
- **Relógio do tick não é UTC:** `tick.time_msc`/`tick.time` vêm do tick do servidor; exportador marca `tick_time_server_unverified`, e `utcClockApproved=false`. Não converter para UTC nem alinhar por esses valores sem prova de sincronização; manter importado como relógio de servidor, aprovação UTC falsa.
- **Snapshot perde precisão:** preços são arredondados a `digits`, spread a `digits`, spread_points a 2 casas; outras escalas a 8/10 casas. Importação não recupera precisão original. Detectar/registrar valores serializados e evitar declarar tick size/value ou spread mais precisos que a exportação; identidade financeira usa o valor textual capturado.
- **Identidade de conta parcialmente coberta:** login/fase não são coletados; parser conserva `account_server` como claim não verificado. Agora registra bloqueadores para `BTCUSD`/`ETHUSD` ausentes e lista extras. `execution-target.json` ainda tem servidor/fase nulos, então não há comparação possível; não promover claim a verificado.
- **Sessões: ausência registrada como bloqueador.** CSV/metadata não exportam horários de negociação, pausas ou feriados; a saída inclui `sessions_missing`.
- **Seleção/status: resolvido no parser.** `selected=false` gera blocker; status não-`ok` e `unavailable_fields` também bloqueiam. Zeros permanecem valores observados e não significam comissão zero.

## Critérios mínimos do parser

1. Bytes lidos com limite, UTF-8 estrito (BOM opcional), header e número exato de colunas/campos, sem duplicatas ou CSV malformado.
2. Preservar valores nas duas representações cobertas pelas fixtures; pendente fixture real de `FileWrite` com delimitador, aspas e Unicode. Hashes preservam os bytes de entrada.
3. Distinguir valores numéricos de estados desconhecidos; falha de parse deve ser explícita. Não inferir comissão zero; manter comissão, UTC, custos/feed/financeiro e estratégia não aprovados.
4. Manter timestamp do tick como horário de servidor não certificado; saída marca UTC não aprovada e sessões ausentes como blocker.
5. Verificar símbolos requisitados, server claim, `status`, `selected`, `unavailable_fields`, escalas e coerência bid/ask/spread; diferenças e ausências geram bloqueios sem autoaprovação.
6. Importação e gravação local offline, sem sobrescrever entradas/saídas existentes. Metadata exige chaves, mas parser ainda não valida semanticamente valores como `read_only=true` e `utcClockApproved=false`; conflito permanece visível em metadata e approvals seguem falsas.

## Estado observado

`execution-target.json` fica em `research/validation/execution-target.json`, não em `tools/`. Importador e fixtures foram revisados estaticamente; nenhum código foi executado nesta revisão. O achado anterior de comissão era falso para a versão atual. Fixtures cobrem duas serializações sintéticas, não saída real do MT5.



