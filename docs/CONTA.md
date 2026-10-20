# Conta do usuário (Fase 2)

Login sem senha pelo Supabase Auth, diário sincronizado, exportação e exclusão de conta. Issues [#19](../../../issues/19), [#21](../../../issues/21), [#22](../../../issues/22) e [#23](../../../issues/23).

**Estado:** código e testes prontos; nada aplicado no Supabase real (depende de [#14](../../../issues/14)). Sem as variáveis abaixo a aba Conta continua mostrando “Supabase preparado no projeto; não conectado.” e o diário segue só no aparelho.

## Como funciona

```
Aba Conta ── e-mail ──► POST /auth/v1/otp (PKCE S256, chave publicável)
                         │
         e-mail com link + código de 6 dígitos
                         │
  link no mesmo aparelho ─► site ?aba=conta&code=…  (ou tradernova://auth?code=… no app → mesma WebView)
  código digitado        ─► POST /auth/v1/verify
                         │
       sessão (token do usuário) guardada no aparelho: tradernova-account-v1
                         │
  PostgREST com o token: journal_entries, user_preferences, rpc/export_my_data, rpc/delete_my_account
```

- **Só chave publicável no cliente.** A rota `GET /api/auth/config` devolve a URL e `TRADERNOVA_SUPABASE_PUBLISHABLE_KEY` apenas se ela for `sb_publishable_…` ou um JWT legado com `role: anon`. Uma chave secreta configurada por engano é recusada e nunca sai do servidor (teste em `tests/account.mjs`).
- **RLS decide tudo.** O cliente nunca envia `user_id`: o padrão da coluna é `auth.uid()` e as políticas exigem `auth.uid() = user_id`. Testes em `supabase/tests/rls-fase2.sql` (usuário C2 não vê nada de C1, nem pela exportação).
- **Diário.** Logado, a aba Diário mostra e grava em `journal_entries` (modo `demo`, com o retrato do sinal como foi visto). O diário local continua guardado; ele só sobe pelo botão **Importar diário deste dispositivo**, nunca automaticamente. Importar de novo não duplica (`unique(user_id, client_id)`). Sem conexão, a decisão é salva no aparelho e pode ser importada depois. A exportação JSON continua funcionando nos dois modos.
- **Exportar meus dados** chama `export_my_data()` (security invoker: só o que a RLS deixa ver) e baixa um JSON; no app, abre o compartilhamento nativo.
- **Excluir conta** pede a confirmação digitando EXCLUIR e chama `delete_my_account()`, que apaga `auth.users` do próprio usuário; diário, aparelhos, preferências e planos saem em cascata. Os dados locais do aparelho não são apagados.
- **Preferências** (tema, densidade, alertas no app): ao entrar, a conta manda; se ela ainda não tem preferências, as do aparelho sobem. Depois, cada mudança é gravada em `user_preferences` (`components/tradernova/preference-sync.tsx`).
- **Sair** encerra a sessão no servidor quando possível e sempre apaga a sessão local.

## Configurar quando o Supabase estiver acessível

1. Aplicar as migrações (inclui `202610201001_account.sql`) com `scripts/apply-migrations.mjs`.
2. Em **Authentication → URL Configuration**, adicionar às Redirect URLs:
   - `https://tradernova.willvinicius.chatgpt.site/?aba=conta`
   - `tradernova://auth`
3. Em **Authentication → Email Templates → Magic Link**, incluir o código para quem abre o e-mail em outro aparelho, por exemplo: `Seu código: {{ .Token }}` além do link `{{ .ConfirmationURL }}`.
4. Variáveis do servidor da web:

| Variável | Valor |
| --- | --- |
| `TRADERNOVA_SUPABASE_URL` | `https://<ref>.supabase.co` (já usada pela rota de sinais) |
| `TRADERNOVA_SUPABASE_PUBLISHABLE_KEY` | chave **publicável** (`sb_publishable_…`) do projeto |

O envio de e-mails usa o SMTP padrão do Supabase, com limite baixo de mensagens por hora; serve para o piloto. SMTP próprio é decisão futura e não foi ativado.

## Verificar

```bash
npm test                                   # inclui tests/account.mjs
TRADERNOVA_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:5432/postgres npm run test:rls
cd mobile && npm run typecheck && npm test && npm run export   # deep link tradernova://auth
```

## Pendências

- Aplicar no projeto real e testar o e-mail de ponta a ponta (#14).
- `/api/signals` por usuário (#20) e registro de push após login (Fase 4, `docs/NOTIFICACOES.md`).
