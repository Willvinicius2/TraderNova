# TraderNova

Laboratório de sinais com revisão humana: acompanha o mercado, pesquisa estratégias e registra decisões. Web na raiz; app Android/iPhone em [`mobile/`](mobile/README.md), que embute a interface publicada. Sinais são exemplos de pesquisa: nenhuma estratégia está aprovada e o app não envia ordens nem cobra.

## Requisitos e instalação

- Node >= 22.13 (pnpm na versão de `package.json`; o instalador cuida disso).
- Instale com `npm run install:ci`. **Não use `npm install` na raiz**: o instalador preserva o `pnpm-lock.yaml` e funciona no Windows sem Bash.
- O mobile tem instalação npm própria (`mobile/package-lock.json`).

## Comandos (raiz)

| Comando | O que faz |
| --- | --- |
| `npm run dev` | Servidor de desenvolvimento em http://localhost:5173 |
| `npm run build` | Build de produção (saída em `dist/`) |
| `npm test` | Testes do motor, mercado ao vivo, fontes e calibração |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run lint` | ESLint (o `mobile/` é ignorado: tem ferramentas próprias) |

Mobile (dentro de `mobile/`): `npm ci`, `npm start`, `npm run typecheck`, `npm test`, `npm run export`.

## O que cada aba faz hoje

- **Mercado**: cotação e gráfico dos sete ativos do catálogo, com modo "Mercado real" e modo "Demonstração" (dados sintéticos fixos). Períodos M1/M5/M15/H1, estado da conexão e indicadores (EMA 20, RSI 14, ATR 14) calculados sobre a mesma série do gráfico.
- **Robô**: motor de sinais manual. Aguarda estratégias validadas; hoje nenhuma foi aprovada, então aparece "Aguardando estratégias validadas" e nenhum sinal é emitido.
- **Estratégias**: repertório de hipóteses (T1, T2, T3 e candidatas) com regras, evidências e o contador de estratégias validadas (zero). Dali é possível abrir o Laboratório com a candidata escolhida.
- **Laboratório**: backtest pronto de uma candidata sobre histórico verificado de BTC/USDT H1 (amostra versionada, conferida por SHA-256, com taxa e slippage), resultados das rodadas de calibração e da pesquisa de ouro, e simulação em tempo real (paper) com Kraken, salva neste navegador. Nada aqui valida uma estratégia.
- **Diário**: decisões registradas durante a revisão de um exemplo, salvas só neste dispositivo, com exportação em JSON. Fica vazio até haver uma revisão.
- **Conta / Preferências**: tema, espaçamento, alertas dentro do app e itens futuros (dados e conta, TraderNova Pro) marcados como pendentes.

Temas: **Essencial Dark**, **Nova Lab** e **Claro & Direto** (ou acompanhar o dispositivo).

## Fontes de dados

- **Kraken Spot** (WebSocket e HTTP públicos): BTC/USD, ETH/USD e SOL/USD. É a única fonte que alimenta o motor e a simulação em tempo real.
- **TradingView/OANDA** (widgets): XAUUSD, NAS100, EURUSD e USDJPY. Servem apenas para consulta visual; **não alimentam o motor, o robô nem os testes**. As cotações podem diferir da sua corretora no MT5.
- Pesquisa offline: arquivos públicos mensais da Binance (BTC/USDT) e amostras congeladas de ouro em `research/`.

## Scripts de pesquisa

- `npm run research:download`: baixa e confere (checksum) o histórico público da Binance para `research/cache`.
- `npm run research:run`: roda o estudo histórico do protocolo e gera os resultados em `public/research/`.
- `npm run research:calibrate`: calibração das candidatas (rodada v2).
- `npm run research:calibrate:v3`: calibração v3, com protocolo congelado.
- `npm run research:gold`: pesquisa offline de ouro (CFD) a partir de um arquivo de origem (`--source`).
- `npm run research:gold:test`: testes da execução da pesquisa de ouro.

## O que ainda não existe

- Sinais persistentes em produção: o código para Supabase, worker com vários pares e saúde do worker está pronto e testado, mas as migrações ainda não foram aplicadas no projeto real, o worker não está hospedado e não há login. Ver [`docs/SINAIS.md`](docs/SINAIS.md) e o passo a passo em [`docs/DEPLOY.md`](docs/DEPLOY.md).
- Worker de ingestão no servidor (os dados são lidos pelo navegador).
- Supabase e login: a migração em `supabase/migrations` está preparada, mas não foi aplicada.
- Notificações push (só avisos dentro do app aberto).
- Dados licenciados para ouro, índices e forex.
- Cobrança, publicação nas lojas e execução de ordens.

## Documentação

[`docs/ESCOPO_CONSOLIDADO.md`](docs/ESCOPO_CONSOLIDADO.md), [`docs/MOTOR_E_VALIDACAO.md`](docs/MOTOR_E_VALIDACAO.md), [`docs/CALIBRACAO_E_PESQUISA.md`](docs/CALIBRACAO_E_PESQUISA.md), [`docs/MERCADO_AO_VIVO.md`](docs/MERCADO_AO_VIVO.md), [`docs/IMPLEMENTACAO.md`](docs/IMPLEMENTACAO.md), [`docs/DESIGN_SYSTEM.md`](docs/DESIGN_SYSTEM.md), [`docs/VALIDACAO.md`](docs/VALIDACAO.md), [`docs/WORKER.md`](docs/WORKER.md), [`docs/DEPLOY.md`](docs/DEPLOY.md).
