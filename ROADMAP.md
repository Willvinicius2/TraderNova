# TraderNova — Roadmap de entrega

Atualizado em 19/10/2026. Cada fase tem um épico no GitHub com as tarefas como sub-issues; marque as tarefas lá e este arquivo acompanha a cada fase concluída. Equipe e responsabilidades em [`docs/EQUIPE.md`](docs/EQUIPE.md).

## Onde estamos (auditoria de 19/10/2026)

O projeto não começa do zero. O que já existe e funciona, com `npm test` verde:

| Área | Situação | Reaproveitar? |
| --- | --- | --- |
| Interface web (7 ativos, 3 temas, abas Mercado/Robô/Estratégias/Laboratório/Diário/Conta) | Pronta e aprovada visualmente | Sim, preservar o visual (AGENTS.md) |
| Mercado ao vivo cripto (Kraken REST + WebSocket) e 10 indicadores | Pronto, com testes | Sim |
| Ouro, Nasdaq e forex | Só widgets visuais TradingView/OANDA | Sim para consulta; o motor precisa de dados autorizados |
| Motor de sinais, backtest e simulação em tempo real (paper) | Pronto, causal, com testes | Sim, é o núcleo |
| Pesquisa: cripto v1/v2/v3, ouro v1 e ouro H1 v2 | Reproduzível, **0 de 5 estratégias aprovadas** | Sim: protocolos, scripts e dados de referência |
| Contrato de sinal (`SignalRecord`), rota `/api/signals/:id` e ficha | Pronto | Sim |
| Worker de ingestão Kraken com armazém JSONL | Pronto, só local | Sim; falta hospedar e gravar no banco |
| Migração Supabase (RLS, entitlements, diário) | Escrita, nunca aplicada nem testada | Parcial: `signals` não bate com o contrato atual |
| Projeto Supabase `TraderNova` (gratuito) | Existe e está ativo; acesso ao banco pela integração falha | Sim, após reautorizar |
| App mobile (Expo + WebView) | Pronto para build; sem APK gerado | Sim |
| CI | Modelo em `docs/`, não ativado | Sim |
| Repositórios `TradingWill` (vazio) e `-Will-IA-Trader-Pro` (rascunho antigo) | Sem código útil | Não |

**Conclusão:** o produto é um laboratório de sinais sólido que roda só no computador e no navegador. O que falta para ser "entregue" é infraestrutura real (banco, worker hospedado, publicação), conta do usuário, notificações, lojas e, acima de tudo, estratégias que passem na validação. As fases abaixo seguem essa ordem.

## Regras que valem para todas as fases

- Nada de execução de ordens, credencial de corretora ou senha no app.
- Nenhuma infraestrutura paga, cobrança ou publicação em loja sem aprovação explícita do Will.
- Sinais são de pesquisa até haver estratégia aprovada pelo protocolo; a interface nunca finge o contrário.
- Critérios de aprovação não mudam depois de ver resultados.
- Todo PR passa no CI (`npm test`, typecheck, lint, mobile).

## Fases

### Fase 0 — Organização
Épico [#1](../../issues/1). Roadmap, equipe, labels e issues. **Concluída com este PR.**

### Fase 1 — Fundação de produção
Épico [#2](../../issues/2). Sinais saem do arquivo local e passam a viver no Supabase, gerados por um worker hospedado.

| # | Tarefa | Precisa do Will |
| --- | --- | --- |
| [#9](../../issues/9) | Ativar CI no GitHub Actions | |
| [#10](../../issues/10) | Migração v2: `research_signals` alinhada ao `SignalRecord` | |
| [#11](../../issues/11) | Adaptador Supabase de leitura para `/api/signals` | |
| [#12](../../issues/12) | `SignalStore` Supabase no worker | |
| [#13](../../issues/13) | Testes de RLS em Postgres local | |
| [#14](../../issues/14) | Recuperar acesso ao banco e aplicar migrações | Sim |
| [#15](../../issues/15) | Hospedar o worker 24/7 | Sim (escolher opção gratuita) |
| [#16](../../issues/16) | Worker com vários pares/intervalos | |
| [#17](../../issues/17) | Publicar a versão web atualizada | Sim |
| [#18](../../issues/18) | Saúde do worker visível na aba Robô | |

**Saída:** um sinal de pesquisa gerado pelo worker hospedado aparece na ficha do site publicado, lido do Supabase.

### Fase 2 — Conta do usuário
Épico [#3](../../issues/3). Login (link mágico), autorização por usuário, diário e preferências sincronizados, exclusão de conta (LGPD). Tarefas [#19](../../issues/19)–[#23](../../issues/23).

**Saída:** mesma conta no celular e no computador com o mesmo diário; usuário B não lê dados do A (teste automatizado).

### Fase 3 — Pesquisa de estratégias
Épico [#4](../../issues/4). Meta de cinco estratégias distintas validadas. Protocolo v4 congelado, contrato da mesa, histórico autorizado de ouro/Nasdaq/forex, três famílias novas, forex, forward test de 30+ dias e registro de aprovação. Tarefas [#24](../../issues/24)–[#32](../../issues/32).

Esta fase **começa em paralelo à Fase 1** (protocolo e famílias novas não dependem da infraestrutura); o forward test depende do worker hospedado.

**Saída:** cada aprovada tem protocolo prévio, aprovação fora da amostra e forward test concluído. Se nenhuma passar, o registro honesto fecha a fase e o produto segue como laboratório.

### Fase 4 — Alertas e notificações
Épico [#5](../../issues/5). Push com Expo Notifications, envio pelo servidor com dedup e expiração, central de alertas. Tarefas [#33](../../issues/33)–[#35](../../issues/35).

**Saída:** notificação com o app fechado no Android, sem duplicata, abrindo a ficha certa.

### Fase 5 — App nas lojas
Épico [#6](../../issues/6). APK interno testado em aparelho, iOS/TestFlight (conta paga, só com aprovação), documentos legais, materiais das lojas e acessibilidade. Tarefas [#36](../../issues/36)–[#40](../../issues/40).

**Saída:** APK instalado e testado pelo Will; envio às lojas só com aprovação.

### Fase 6 — TraderNova Pro (opcional)
Épico [#7](../../issues/7). Planos e compras com recibos no servidor. Tarefas [#41](../../issues/41)–[#42](../../issues/42). Só começa com decisão do Will.

## Ordem e paralelismo

```
Fase 0 ─► Fase 1 ─► Fase 2 ─► Fase 4 ─► Fase 5 ─► (Fase 6)
            └──► Fase 3 (em paralelo desde já; forward test usa o worker da Fase 1)
```

## Decisões pendentes do Will

1. Reautorizar a integração do Supabase ou redefinir a senha do banco ([#14](../../issues/14)).
2. Onde hospedar o worker ([#15](../../issues/15)).
3. Onde publicar o site ([#17](../../issues/17)).
4. Dados do contrato da mesa e exportação MT5 ([#25](../../issues/25), [#26](../../issues/26)).
