# TraderNova

Base mobile web do laboratório de sinais com revisão humana. Modo exclusivamente demonstrativo, sem conexão à corretora, sem ordens e sem cobranças.

## Desenvolvimento
Node 22.13+ e pnpm (usar a versão declarada em package.json). Instale preservando pnpm-lock.yaml. `pnpm dev` inicia o desenvolvimento; `pnpm build` gera a versão de produção. A hospedagem deste projeto é gerenciada por Sites.

## Verificações
`node tests/core.mjs` verifica propriedades do motor e estados críticos.
`pnpm exec tsc --noEmit` verifica tipos.

## Status funcional
Abra o app e use “Testar alerta de compra”. Clique em “Analisar”, faça a revisão de exemplo e consulte o Diário. No Laboratório, execute a simulação para calcular resultados sobre dados sintéticos. Estratégias de mercado e suas métricas continuam não validadas.

Integração Supabase, cotações reais, worker Python, autenticação de aplicação, push, compras e aplicativos Android/iOS são próximas etapas. Leia `docs/IMPLEMENTACAO.md` para detalhes e limites. A migração Supabase não foi aplicada automaticamente.
