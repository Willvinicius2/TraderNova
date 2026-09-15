# TraderNova — aparência e parâmetros visuais

A interface acompanha os dois conceitos mobile aprovados. A implementação inclui ícones para os sete instrumentos, temas, densidade e cores semânticas para gráficos, compra e venda.

## Parâmetros

`app/design-tokens.css` é a fonte central de cores, fonte, tamanhos, bordas, raios, altura mínima de controles, sombras, espaçamentos e duração das transições.

- Nova Lab (padrão): fundo `#111117`, cartões `#1C1C26`, ação roxa `#A88BFA`.
- Claro & Direto: fundo `#F5F7FA`, cartões brancos, ação azul `#4263EB`.
- `--success` e `--destructive` comunicam compra/alta e venda/queda independentemente da cor de marca.
- `--space-panel`, `--space-page` e `--space-grid` controlam o respiro da interface; o modo compacto os reduz sem encolher texto ou alvos de toque.
- `--font-interface`, `--font-size-body`, `--font-size-title`, `--radius-card`, `--radius-control` e `--control-height` permitem ajustes consistentes.
- Os breakpoints preservam a navegação inferior no celular e o menu lateral no desktop.

## Preferências

O sol/lua no cabeçalho alterna rapidamente claro/escuro. Em Conta → Do seu jeito, o usuário escolhe qualquer tema ou o modo automático que acompanha o dispositivo, além do espaçamento confortável/compacto. O tema é salvo por `next-themes` em `tradernova-theme-v1` e a densidade em `tradernova-density-v1`. Ambos são locais ao navegador; não há sincronização de conta. A inicialização do tema ocorre antes da hidratação para evitar flashes da paleta errada.

A cor da barra do navegador acompanha o token de fundo; os alertas visuais e os gráficos também seguem o tema. Sem acesso ao armazenamento, o tema/densidade continuam utilizáveis durante a sessão.

## Símbolos

`components/tradernova/asset-icon.tsx` mantém o mapeamento visual de XAUUSD, NAS100, BTCUSD, ETHUSD, SOLUSD, EURUSD e USDJPY. Ouro usa uma barra dourada; cripto usa suas marcas; forex usa bandeiras sobrepostas; Nasdaq usa um símbolo de gráfico. Os SVGs servidos localmente são decorativos e acompanham o nome/ticker legível. As cores oficiais das marcas não são alteradas pelo tema.

Origens, atribuição e licenças: `public/assets/instruments/SOURCES.txt`. O rodapé dá acesso aos créditos.

## Integração

Este trabalho foi feito em uma worktree separada (`codex/asset-symbols`) e incorpora o commit de mercado ao vivo `b39e324`. A conexão Kraken, os cálculos, o histórico e o processamento dos sinais não foram alterados. Não houve mudança de preços comerciais, regras de estratégia, validação ou publicação nas lojas.
