# TraderNova

Base mobile web do laboratório de sinais com revisão humana. Mercado com integração pública à Kraken Spot para BTC/USD, ETH/USD e SOL/USD. Sinais, diário e testes ainda demonstrativos; sem envio de ordens ou cobranças.

## Desenvolvimento
Node 22.13+ e pnpm (usar a versão declarada em package.json). Instale preservando pnpm-lock.yaml. `pnpm dev` inicia o desenvolvimento; `pnpm build` gera a versão de produção. A hospedagem deste projeto é gerenciada por Sites.

## Verificações
`node tests/core.mjs` verifica propriedades do motor e estados críticos.
`node tests/live-market.mjs` verifica a integração de dados com eventos e HTTP controlados.
`pnpm exec tsc --noEmit` verifica tipos.

## Status funcional
Abra Mercado para acompanhar a conexão de BTC, ETH e SOL. Use M1/M5/M15/H1 e confira fonte e atualização. Na aba Robô, gere um exemplo, clique em “Analisar”, faça a revisão e consulte o Diário. No Laboratório, execute a simulação para calcular resultados sobre dados sintéticos. Estratégias de mercado e suas métricas continuam não validadas.

Ouro/Nasdaq/forex da corretora, integração Supabase, worker Python, autenticação de aplicação, push, compras e aplicativos Android/iOS são próximas etapas. Leia `docs/MERCADO_AO_VIVO.md` para o status 0.2 e a limitação da verificação de conexão externa. Leia `docs/IMPLEMENTACAO.md` para detalhes e limites. A migração Supabase não foi aplicada automaticamente.
