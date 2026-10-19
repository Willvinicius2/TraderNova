# Equipe TraderNova

Papéis especialistas que constroem o projeto. Cada papel é executado por um agente Claude com sua própria thread no projeto "nova" (ou por uma pessoa, quando houver), sempre a partir de uma issue do [ROADMAP](../ROADMAP.md). O Will é o dono do produto: aprova decisões marcadas `precisa-will`, revisa PRs e é a única pessoa que opera a conta da mesa.

## Como a equipe trabalha

- **Uma issue, um responsável, um PR.** O papel dono da issue abre o PR; outros papéis revisam quando a issue toca a área deles.
- **Labels mostram quem atua:** `area:*` define o papel dono; `ativo:*` chama o especialista do ativo; `precisa-will` bloqueia até decisão do Will.
- **Threads paralelas** só para áreas que não editam os mesmos arquivos ao mesmo tempo (ver "Frentes paralelas").
- **Regras do projeto** (AGENTS.md) valem para todos: preservar o visual e os três temas, nada de ordens, nada pago sem aprovação, critérios de pesquisa congelados.

## Papéis

### 1. Coordenação de produto
Mantém o roadmap, prioriza issues, consolida o relatório de cada fase e encaminha decisões ao Will.
Labels: `épico`, `area:docs`. Fases: todas.

### 2. Especialista em mercado financeiro e mesa proprietária
Contratos (CFD, spot, futuro), custos reais (spread, comissão, swap), sessões e horários, regras da mesa The5ers (perda diária/total, notícias). Traduz o contrato da conta do Will em parâmetros do motor.
Labels: `area:mercado`. Issues-chave: #25, #27, #32.

### 3. Estrategista quant
Desenha famílias de estratégia distintas, escreve protocolos congelados antes dos resultados, controla sobreajuste (contagem de variantes, janelas fora da amostra) e decide aprovação/reprovação pelo protocolo.
Labels: `area:pesquisa`. Issues-chave: #24, #27–#31.

### 4. Especialistas por ativo
Conhecem a microestrutura e as fontes de dados de cada mercado e revisam toda pesquisa e integração do seu ativo.
- **Cripto (BTC, ETH, SOL):** Kraken/Binance, funcionamento 24/7, funding. Label `ativo:cripto`.
- **Ouro (XAUUSD):** CFD da mesa, sessões Londres/NY, sensibilidade a notícias e juros. Label `ativo:ouro`.
- **Índices (NAS100):** CFD vs. NDX à vista, abertura de NY, gaps. Label `ativo:nasdaq`.
- **Forex (EURUSD, USDJPY):** spread por sessão, rollover/swap, eventos de bancos centrais. Label `ativo:forex`.

### 5. Gestão de risco e conformidade
Risco por operação e conjunto, limites da mesa, linguagem do produto (pesquisa, não recomendação de investimento), privacidade/LGPD e textos legais.
Labels: `area:risco`. Issues-chave: #23, #24, #32, #38.

### 6. Engenharia do motor e backtest
Motor TypeScript compartilhado entre interface, worker e pesquisa; causalidade, custos, execução na abertura seguinte; testes determinísticos.
Labels: `area:motor`. Issues-chave: #27, #32.

### 7. Engenharia de dados
Ingestão (worker), armazenamento de candles, qualidade (lacunas, fuso, checksum), históricos autorizados e forward test.
Labels: `area:dados`. Issues-chave: #12, #15, #16, #26, #31.

### 8. Backend e Supabase
Migrações, RLS, Auth, adaptadores de leitura/escrita, envio de push pelo servidor, recibos.
Labels: `area:backend`. Issues-chave: #10–#14, #19–#21, #33–#34, #42.

### 9. Front-end e interface
Abas do app, estados honestos (carregando, indisponível, expirado), integração com a conta e alertas, sem alterar o visual aprovado.
Labels: `area:frontend`. Issues-chave: #18, #19, #21, #22, #35, #40.

### 10. Design e UX
Guardião do design system e dos três temas (Essencial Dark, Nova Lab, Claro & Direto), acessibilidade e materiais das lojas.
Labels: `area:design`. Issues-chave: #22, #35, #39, #40.

### 11. Mobile
App Expo/WebView, deep links, push nativo, builds EAS e testes em aparelho.
Labels: `area:mobile`. Issues-chave: #33, #36, #37.

### 12. DevOps e QA
CI, deploy do site e do worker, monitoramento, testes de RLS e regressão.
Labels: `area:devops`, `area:qa`. Issues-chave: #9, #13, #15, #17, #18.

## Frentes paralelas

Podem rodar ao mesmo tempo, cada uma em sua thread, porque mexem em arquivos diferentes:

| Frente | Papéis | Arquivos principais |
| --- | --- | --- |
| Infra de sinais (Fase 1) | Backend, Dados, DevOps | `supabase/`, `lib/tradernova/signal-*`, `worker/`, `.github/` |
| Pesquisa de estratégias (Fase 3) | Quant, Mercado, Ativos, Risco, Motor | `research/`, `scripts/`, novas estratégias em `lib/tradernova/` |
| Conta e interface (Fase 2, depois da Fase 1) | Front-end, Design, Backend | `app/`, `components/` |
| Mobile e lojas (Fases 4–5) | Mobile, Design, Risco | `mobile/` |

Mudanças no motor compartilhado (`paper-engine.ts`, `backtest.ts`, `indicators.ts`) passam por um único dono por vez (Engenharia do motor) para não haver conflito entre frentes.
