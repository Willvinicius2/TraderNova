# Notificações push (Fase 4)

Preparação das issues [#33](https://github.com/Willvinicius2/TraderNova/issues/33), [#34](https://github.com/Willvinicius2/TraderNova/issues/34) e [#35](https://github.com/Willvinicius2/TraderNova/issues/35). Código e testes prontos; **nada envia notificação hoje**: falta conta Expo/EAS (projectId e FCM), login (Fase 2) e o worker hospedado chamar o envio (Fase 1). Nenhum serviço pago foi ativado.

## Regras (`lib/tradernova/push-notifications.ts`)
- **Política do servidor (`PushPolicy`)**: por padrão `allowResearch=false`. Enquanto não houver estratégia aprovada, `dispatchPush` não envia nada (pesquisa vira `research-off`, `alert` sem aprovação vira `unapproved-alert`). Ligar `allowResearch` (notificação de pesquisa rotulada e com opt-in, como prevê #34) é decisão do Will.
- **Opt-in**: preferências começam desligadas (`enabled=false`, `includeResearch=false`). Usuário sem preferências salvas não recebe nada.
- **Pesquisa x alerta**: com `allowResearch` ligado, sinal `research` sai rotulado "Pesquisa · … — Sinal de pesquisa, não é recomendação." e só para quem ligou `includeResearch`. `alert` só sai se a estratégia/versão estiver em `alertApprovals` com aprovação vigente; o registro começa **vazio**. `alert` sem aprovação não sai nem é rebaixado para pesquisa (indica erro no pipeline). `test` nunca sai.
- **Expiração**: sinal invalidado, vencido ou a menos de 15 s de vencer não é enviado. A mensagem leva `ttl` e `expiration` iguais à validade: o serviço descarta o que não for entregue a tempo.
- **Dedup**: no máximo uma notificação por (sinal, dispositivo). O envio faz *claim* antes (chave primária de `push_deliveries`); quem não consegue o claim não envia, mesmo com dois workers. Falha não é reenviada automaticamente.
- **Preferências por ativo e estratégia**: `mutedInstruments` (só o catálogo de 7 ativos) e `mutedStrategies`.
- **Payload**: título, corpo com referência/stop/alvo no formato do ativo e validade no horário de Brasília, `data.url = tradernova://signal/<uuid>`. Nunca leva `dedupKey` nem instrução de ordem.
- **Token inválido**: resposta `DeviceNotRegistered` do Expo desliga o aparelho (`enabled=false`).
- **Central de alertas**: `alertCenterItems` lista os últimos sinais com o estado da ficha (ativo/expirado/invalidado). A tela ainda não existe; ela entra no visual atual da aba Robô, nos três temas.

## Banco (`supabase/migrations/202610200101_push_notifications.sql`)
- `push_devices` (já existia): ganha `enabled`, `disabled_reason`, `updated_at` e exige token Expo em android/ios.
- `notification_preferences`: uma linha por usuário, RLS (cada um só a sua).
- `push_deliveries`: (sinal, dispositivo) único, status `claimed`/`sent`/`failed`. Só `service_role`.
- Testes: `supabase/tests/rls-push.sql`, rodados por `node scripts/test-rls.mjs` depois de `rls.sql`.

## Servidor
`lib/tradernova/supabase-push.ts`: `loadPushTargets` (aparelhos ligados + preferências) e `supabasePushDeliveryStore`. Junto com `createExpoPushSender` e `dispatchPush`, o worker chamaria assim depois de gravar sinais novos:

```ts
const targets = await loadPushTargets(cfg);
await dispatchPush({signals: novos, ...targets, now: Date.now(), store: supabasePushDeliveryStore(cfg), send: createExpoPushSender({fetch})});
```
Ligado no worker por `worker/push.ts` quando o armazém é o Supabase (`--signal-store supabase`): roda depois de gravar sinais novos e do checkpoint, e uma falha de push só gera o aviso `push_falhou`. Com a política padrão, um lote só de sinais de pesquisa nem consulta aparelhos (`push_resultado` com `skipped: research-only`). O serviço Expo Push é gratuito; `EXPO_ACCESS_TOKEN` é opcional.

## App (`mobile/`)
- `expo-notifications` com canal Android `sinais`. Permissão **nunca** é pedida na abertura: o site manda `{type:'push-register'}` pela ponte (depois do login e do opt-in) e recebe a resposta no evento `tradernova-push` (`granted` com token, `denied` ou `unavailable`). O site grava o token em `push_devices` com a sessão do usuário.
- Toque na notificação (app aberto ou fechado) abre a ficha só se `data.url` for `tradernova://signal/<uuid v4>`.
- Sem `extra.eas.projectId` (conta Expo não vinculada) o registro devolve `unavailable/not-configured`.

## Pendente (precisa do Will ou de outra fase)
1. Vincular o app a uma conta Expo (`eas init`) e configurar FCM (Android) / APNs (iOS, conta paga) — gratuito no Android.
2. Login (Fase 2) e a tela de preferências/central no site, chamando `push-register`.
3. Worker hospedado (Fase 1, #15); a chamada a `dispatchPush` já está ligada.
4. Teste em aparelho Android real: notificação com app fechado, sem duplicata, abrindo a ficha certa.

## Testes
`tests/push-notifications.mjs` (regras, payload, dedup, corrida entre workers, lotes de 100, cliente Expo e adaptador Supabase com `fetch` simulado) e `mobile/tests/site.mjs` (toque e token).
