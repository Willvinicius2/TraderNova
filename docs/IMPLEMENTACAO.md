# TraderNova — Base 0.1

Criada em 15/09/2026. Base web responsiva; não é um aplicativo já publicado nas lojas.

## Entregue
- Sete ativos demonstrativos: XAUUSD, NAS100, BTCUSD, ETHUSD, SOLUSD, EURUSD, USDJPY.
- Navegação mobile com Mercado, Robô, Estratégias, Testes, Diário e Conta.
- Candles determinísticos por ativo e período. EMA20, ATR14 e RSI14 calculados sobre os candles sintéticos.
- Alertas internos de compra/venda com link para a ficha, validade de 60 segundos, revisão e prevenção de registro duplicado. Link `?sinal=<id>` recupera o exemplo no mesmo dispositivo.
- Seis candidatas especificadas. Nenhuma foi implementada e validada no mercado. Métricas ainda não medidas permanecem vazias.
- Testador local EMA9/21, separado da S1, com custo em R, stop ATR, alvo configurável, saída por tempo, próximo candle, tratamento conservador de ambiguidade e gaps.
- Resultado sintético: R líquido, trades, acerto, curva e drawdown de patrimônio fechado. Não inclui risco intratrade, ticks, especificações de contrato, dimensionamento monetário, sessões, atraso humano ou separação de amostra. Não usar para validar estratégias reais.
- Replay visual de candles, sem sobreposição de operações do teste.
- Diário, sinais e último resultado demonstrativo persistidos apenas no navegador, com exportação JSON. Não são dados sincronizados ou conta real.
- Manifesto e ícones para experiência web instalada quando o navegador permitir. Sem service worker de cache, offline, push ou instalação nativa garantida.
- Migração Supabase com isolamento por usuário, contratos, versões, relatórios, sinais, diário, dispositivos e permissões de assinatura. Preparada; não aplicada nem verificada em banco real.
- Adaptador de leitura HTTP isolado, verificação de fonte recente e contrato de permissões Pro. Não conectado à interface de demonstração.

## Limites e próximo ciclo
1. Informar corretora/mesa e contrato exato de XAUUSD/Nasdaq. Não pedir senha de negociação.
2. Conectar Supabase Auth e aplicar a migração em um projeto de desenvolvimento. Verificar políticas com usuário A, usuário B e anônimo; testar tentativas de autopromoção de assinatura/estratégia antes de conectar o app. A interface atual não solicita login Supabase.
3. Conectar provedor somente de leitura e mapear instrumento, servidor, tick size, moeda e tipo de volume. Não substituir CFD por spot ou futuro sem identificação.
4. Implementar worker Python persistente fora do Supabase, com cache local, fila limitada, uma estratégia S1 e dados causais. O Supabase é banco/distribuição, não o motor contínuo.
5. Testar S1 em histórico real com custos, atraso humano, regras de sessão, dados fora da amostra, validação temporal e acompanhamento. Não converter resultados sintéticos em “validada”.
6. Publicar sinais pelo servidor e entregar push com deduplicação por signal_id e expiração. Toque abre a ficha; o preço/fonte deve ser revalidado antes da revisão. Alertas com app fechado não funcionam nesta base.
7. Integrar diário autenticado e migração explícita dos exemplos locais, conservando o marcador demo e evitando importação automática como operações reais.
8. Para lojas: decidir entre empacotamento nativo e cliente Expo/React Native; implementar distribuição, assinatura do app, links, push, acessibilidade e compras verificadas pelo servidor. Usar a política vigente de cada loja ao preparar a submissão. As regras, custos e aprovação das lojas não estão resolvidos nesta entrega.
9. A estrutura de assinatura reserva mensal/anual e proveniência apple/google/web; preços, produtos, recibos, restauração, cancelamento e webhooks idempotentes são pendentes. Clientes não podem escrever entitlements.

## Consumo
O modo demonstrativo calcula tudo no navegador, sem API de mercado, IA ou serviço pago. Nenhuma contratação foi realizada. Isso não constitui garantia de hospedagem ou dados gratuitos no futuro. Ao conectar: sete ativos, snapshots agrupados, retenção curta, métricas de uso, teto de orçamento, cache e nenhuma chamada de LLM por tick. Backtests extensos devem ser jobs limitados fora do navegador e fora das funções de curta duração.

## Estrutura
- `app/page.tsx`: fluxos e composição da interface.
- `app/globals.css`: tema e breakpoints.
- `lib/tradernova/domain.ts`: catálogo, tipos e indicadores demonstrativos.
- `lib/tradernova/backtest.ts`: modelo de teste técnico em R.
- `lib/tradernova/integrations.ts`: limites da integração e contrato futuro.
- `supabase/migrations/202609150001_base.sql`: esquema inicial preparado.
- `tests/core.mjs`: verificações matemáticas e de estado; não é validação financeira.
- `docs/ESPECIFICACAO_ORIGINAL.md`: plano recebido, preservado como referência.

## Referências verificadas
O desenho de autenticação, grants e RLS segue a documentação oficial do [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security). O adaptador usa a [API REST do Supabase](https://supabase.com/docs/guides/api). As políticas SQL ainda precisam ser executadas e testadas com dados isolados antes de produção.
