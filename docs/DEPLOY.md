# Deploy da Fase 1 (banco, worker e site)

Três passos tiram o TraderNova do computador. Os três usam só planos **gratuitos** e nenhum ativa cobrança (AGENTS.md). Cada passo indica o que só o Will pode fazer.

## 1. Banco: aplicar as migrações no Supabase (issue #14)

**Feito em 21/10/2026.** As quatro migrações da Fase 1 (`202609150001`, `202610190001`, `202610200001` e `202610210001`) estão aplicadas no projeto real, registradas com as mesmas versões dos arquivos. O RLS foi conferido no banco: `anon` não lê nenhuma tabela e `authenticated` não grava sinais. O advisor de segurança está sem avisos. Os comandos abaixo continuam valendo para migrações futuras.

Projeto: `TraderNova` (ref `cnlvasvvmlfwzcecduhy`, plano gratuito).

**Will:** reautorize a integração do Supabase no Claude, ou copie a *connection string* em Project Settings → Database (modo *Session*, com a senha do banco).

Com a string de conexão:

```bash
export TRADERNOVA_MIGRATIONS_DATABASE_URL='postgresql://postgres.cnlvasvvmlfwzcecduhy:<senha>@aws-0-<região>.pooler.supabase.com:5432/postgres'
npm run db:migrate            # lista o que falta, não aplica nada
npm run db:migrate -- --apply # aplica em ordem e registra em supabase_migrations.schema_migrations
```

O script é o mesmo que o CI usa no Postgres descartável (`npm run test:rls`), e a segunda execução precisa dizer "Nenhuma migração pendente.". O registro é a tabela do Supabase CLI, então o painel e a integração enxergam o mesmo histórico.

Depois de aplicar, pegue em Project Settings → API:
- a **service_role key**, que vai só para a VM do worker;
- uma chave de servidor para a web (`TRADERNOVA_SUPABASE_READ_KEY`). Na Fase 1 é a service_role ou uma *secret key* nova; na Fase 2 a rota passa a usar o token do usuário.

Nenhuma dessas chaves vai para o navegador, para o app ou para o git.

## 2. Worker 24/7 numa VM gratuita (issue #15)

Um processo cobre BTC/ETH/SOL em M15 e H1 (cerca de 100 MB de RAM). Opções sem custo:

| Opção | Observação |
|---|---|
| Oracle Cloud Always Free (VM Ampere ou AMD micro) | Recomendada: sempre gratuita e com folga de memória. Pede cartão para verificação, sem cobrança no plano Always Free. |
| Google Cloud e2-micro (us-west1, us-central1 ou us-east1) | Gratuita dentro do free tier; 1 GB de RAM. |
| Seu próprio computador ligado | Sem cadastro, mas para quando o PC desliga. |

**Will:** crie a VM (Ubuntu 24.04) e me passe o acesso, ou rode os comandos abaixo nela.

```bash
# Node 24 (NodeSource) e git
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt-get install -y nodejs git
# Instalação do serviço (clona em /opt/tradernova, instala dependências, cria /etc/tradernova/worker.env)
git clone --depth 1 https://github.com/Willvinicius2/TraderNova.git /tmp/tn && sudo bash /tmp/tn/deploy/worker/install.sh main
sudo nano /etc/tradernova/worker.env   # preencher TRADERNOVA_SUPABASE_SERVICE_KEY
sudo bash /opt/tradernova/deploy/worker/install.sh main
journalctl -u tradernova-worker -f
```

O serviço (`deploy/worker/tradernova-worker.service`) roda com usuário dinâmico e sistema de arquivos somente leitura, exceto `/var/lib/tradernova`, onde ficam os candles. Ele reinicia sozinho em caso de falha e encerra limpo com `systemctl stop`. Para atualizar, rode o `install.sh` de novo com o ref desejado.

A aba Robô confirma que deu certo: o painel "Worker de pesquisa" mostra **Ativo** para cada par, lido de `worker_status`.

## 3. Publicar o site (issue #17)

Hoje o app de celular abre `https://tradernova.willvinicius.chatgpt.site/` (`mobile/src/site.ts`). O build de produção (`npm run build`) gera um Worker do Cloudflare em `dist/server/`, conferido localmente com `npm start`.

| Opção | O que muda |
|---|---|
| Continuar no endereço atual (`chatgpt.site`) | Nada no app. **Will** republica pelo mesmo caminho usado antes e cadastra as variáveis abaixo, se esse host aceitar variáveis de servidor. |
| Cloudflare Workers, plano gratuito | Endereço novo `*.workers.dev` (ou domínio próprio). O app precisa trocar `SITE_URL` e gerar um novo build. |

Para o Cloudflare (**Will** cria a conta gratuita e faz login com `npx wrangler login`):

```bash
npm run build
npx wrangler secret put TRADERNOVA_SUPABASE_URL --config dist/server/wrangler.json
npx wrangler secret put TRADERNOVA_SUPABASE_READ_KEY --config dist/server/wrangler.json
npx wrangler deploy --config dist/server/wrangler.json
```

Variáveis do servidor web:

| Variável | Valor |
|---|---|
| `TRADERNOVA_SUPABASE_URL` | `https://cnlvasvvmlfwzcecduhy.supabase.co` |
| `TRADERNOVA_SUPABASE_READ_KEY` | chave de servidor (passo 1) |

Sem elas o site funciona e mostra "fonte não conectada", sem inventar nenhum sinal.

## Conferência final da Fase 1

1. `npm run db:migrate` diz "Nenhuma migração pendente.".
2. `journalctl -u tradernova-worker` mostra `ciclo_concluido` para os 6 pares/intervalos.
3. `/api/worker-status` no site publicado responde `state: ok` com os 6 itens em `ativo`.
4. Quando um sinal de pesquisa for registrado (`sinal_registrado` no log), `/?aba=robo&sinal=<public_id>` abre a ficha lida do Supabase.
