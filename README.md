# TraderNova

Projeto web existente e aplicativo Android/iPhone em [`mobile/`](mobile/README.md). Código reunido em `D:\openclaude\TradersNova`, com histórico original preservado.

Piloto 0.5: radar experimental ETH/BTC com duas pernas, planejamento de risco por tick, diário local de hipóteses e pesquisa de pares/funding sem duplicar as famílias anteriores. Veja a [revisão módulo por módulo](docs/REVISAO_MODULOS_2026-09-28.md). N1 foi reprovada na triagem; N2 e N13 também reprovaram no desenvolvimento. Nenhuma estratégia aprovada para operar.

## Meta atual de validação

No mínimo sete famílias distintas, **0/7 aprovadas**. Painel de Estratégias/Laboratório com N16–N20, regras, dados pendentes, exportação e nove reprovações anteriores. `npm run research:status` sincroniza o painel sem IA ou backtests; `npm run research:five:test` verifica as condições de sinal com dados artificiais. Leia [protocolo e pendências](research/validation/README.md).

## Começar

```powershell
# Web, na raiz
npm run install:ci
npm run dev

# Mobile
cd mobile
npm ci
npm start
```

O instalador da raiz preserva o `pnpm-lock.yaml` e funciona no Windows sem Bash. O mobile tem instalação npm independente. Consulte [`mobile/README.md`](mobile/README.md) e [`docs/ESCOPO_CONSOLIDADO.md`](docs/ESCOPO_CONSOLIDADO.md).

## Base web

Base mobile web do laboratório de sinais com revisão humana. Mercado com integração pública à Kraken Spot para BTC/USD, ETH/USD e SOL/USD. Ouro, Nasdaq, EURUSD e USDJPY exibem cotações, gráficos e análise técnica via widgets TradingView/OANDA. Laboratório com três estratégias candidatas sobre histórico Kraken ou dados artificiais identificados. Sinais do robô e diário continuam demonstrativos; sem envio de ordens ou cobranças.

## Desenvolvimento
Node 22.13+ e pnpm (usar a versão declarada em package.json). `pnpm --version` na raiz deve imprimir 11.25.0: o pnpm global baixa essa versão sozinho para `%LOCALAPPDATA%\pnpm\.tools\pnpm`; se o wrapper falhar com "Failed to switch pnpm", apague essa pasta e rode de novo, ou instale direto com `npm install -g pnpm@11.25.0`. Instale preservando pnpm-lock.yaml. `pnpm dev` inicia o desenvolvimento; `pnpm build` gera a versão de produção. A hospedagem deste projeto é gerenciada por Sites.

## Verificações
`node tests/core.mjs` verifica propriedades do motor e estados críticos.
`node tests/live-market.mjs` verifica a integração de dados com eventos e HTTP controlados.
`node tests/market-sources.mjs` verifica símbolos, períodos e recuperação dos widgets.
`node tests/calibration-research.mjs` verifica indicadores, causalidade das três candidatas, execução e histórico de resultados.
`pnpm exec tsc --noEmit` verifica tipos.

## Status funcional
Abra Mercado para acompanhar a conexão de BTC, ETH e SOL. Use M1/M5/M15/H1 e confira fonte e atualização. O gráfico nativo e dez leituras usam a mesma série; consultas periódicas recuperam dados quando o canal ao vivo está indisponível. Na aba Robô, gere um exemplo, clique em “Analisar”, faça a revisão e consulte o Diário. Em Estratégias, escolha T1, T2 ou T3 e prepare um teste no Laboratório. Escolha histórico real ou simulação, informe custos e consulte resultados, replay da própria amostra e exportação JSON. Os últimos 12 experimentos ficam neste navegador. Nenhuma estratégia é validada automaticamente.

Leia `docs/CALIBRACAO_E_PESQUISA.md` para a atualização de dados e pesquisa, parâmetros, referências e limites.

Dados próprios da corretora para o motor de estratégias, integração Supabase, worker Python, autenticação de aplicação, push remoto e compras são próximas etapas. A base nativa Android/iOS está em mobile/; testes em aparelhos e publicação nas lojas seguem pendentes. Leia `docs/MERCADO_AO_VIVO.md` para o status 0.3 e a limitação da verificação de conexão externa. Leia `docs/IMPLEMENTACAO.md` para detalhes e limites. A migração Supabase não foi aplicada automaticamente.
