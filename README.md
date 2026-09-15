# TraderNova

Base mobile web do laboratório de sinais com revisão humana. Mercado com integração pública à Kraken Spot para BTC/USD, ETH/USD e SOL/USD. Ouro, Nasdaq, EURUSD e USDJPY exibem cotações, gráficos e análise técnica via widgets TradingView/OANDA. Laboratório com três estratégias candidatas sobre histórico Kraken ou dados artificiais identificados. Sinais do robô e diário continuam demonstrativos; sem envio de ordens ou cobranças.

## Desenvolvimento
Node 22.13+ e pnpm (usar a versão declarada em package.json). Instale preservando pnpm-lock.yaml. `pnpm dev` inicia o desenvolvimento; `pnpm build` gera a versão de produção. A hospedagem deste projeto é gerenciada por Sites.

## Verificações
`node tests/core.mjs` verifica propriedades do motor e estados críticos.
`node tests/live-market.mjs` verifica a integração de dados com eventos e HTTP controlados.
`node tests/market-sources.mjs` verifica símbolos, períodos e recuperação dos widgets.
`node tests/calibration-research.mjs` verifica indicadores, causalidade das três candidatas, execução e histórico de resultados.
`pnpm exec tsc --noEmit` verifica tipos.

## Status funcional
Abra Mercado para acompanhar a conexão de BTC, ETH e SOL. Use M1/M5/M15/H1 e confira fonte e atualização. O gráfico nativo e dez leituras usam a mesma série; consultas periódicas recuperam dados quando o canal ao vivo está indisponível. Na aba Robô, gere um exemplo, clique em “Analisar”, faça a revisão e consulte o Diário. Em Estratégias, escolha T1, T2 ou T3 e prepare um teste no Laboratório. Escolha histórico real ou simulação, informe custos e consulte resultados, replay da própria amostra e exportação JSON. Os últimos 12 experimentos ficam neste navegador. Nenhuma estratégia é validada automaticamente.

Leia `docs/CALIBRACAO_E_PESQUISA.md` para a atualização de dados e pesquisa, parâmetros, referências e limites.

Dados próprios da corretora para o motor de estratégias, integração Supabase, worker Python, autenticação de aplicação, push, compras e aplicativos Android/iOS são próximas etapas. Leia `docs/MERCADO_AO_VIVO.md` para o status 0.3 e a limitação da verificação de conexão externa. Leia `docs/IMPLEMENTACAO.md` para detalhes e limites. A migração Supabase não foi aplicada automaticamente.
