# TraderNova — auditoria e testes de estratégias

Data: 28/09/2026. Versão de trabalho: 0.6.

## Conclusão

O piloto web/mobile foi revisado, recebeu correções e passou nos testes automatizados descritos abaixo. **Não há estratégia aprovada para operar.** As novas famílias N3 e N4 foram testadas com custos e reprovaram. O aplicativo de produção solicitado ainda depende de validação operacional e de serviços não conectados. A instalação web no iPhone está preparada. O login Expo e o vínculo do projeto foram concluídos; a assinatura Apple foi adiada pelo usuário.

## Revisão módulo por módulo

| Módulo | Resultado da revisão | Limite verificável |
| --- | --- | --- |
| Navegação e temas | Seis áreas, três temas e desenho original preservados; TypeScript aprovado | Teste físico no iPhone ainda pendente |
| Mercado cripto | REST/WebSocket, histórico, preço e indicadores revisados; bid/ask confirmados no navegador após ajuste de relógio | Kraken spot; não representa o futuro/CFD da mesa |
| Ouro, Nasdaq, EURUSD, USDJPY | Quatro símbolos OANDA via TradingView e estados de falha cobertos por testes | Consulta visual; estes quatro contratos não alimentam o motor local |
| Indicadores | Dez leituras calculadas na mesma série; testes de causalidade, aquecimento e lacunas aprovados | Incluem candle em formação na tela; POC não implementado |
| Radar N1 | Regra, sincronismo das duas séries, janela, expiração, pausa, deduplicação e exportação revisados | Estratégia reprovada; observação experimental com a tela aberta |
| Motor de estratégias anteriores | Aprovação continua obrigatória; nenhum alerta operacional liberado | Zero estratégias aprovadas; a ausência de sinais é esperada |
| Plano de risco | Compra/venda, ticks, custos e arredondamento testados; alvo líquido não positivo agora é recusado | Usuário precisa informar contrato linear, tick e custos; não calcula margem ou risco conjunto das duas pernas |
| Laboratório | O backtest T3 foi executado pela interface: 32 operações, +0,34%, PF 1,04 e DD 4,02% | Resultado retrospectivo insuficiente para aprovação |
| Simulação forward | Entradas por cotações observadas e limites testados; validação da recuperação local reforçada | Só roda com tela aberta; não recupera movimentos perdidos durante desconexão |
| Diário e exportação | Registros locais separados de exemplos; exportação do diário não libera mais o blob imediatamente | Sem sincronização por conta; exportação nativa física ainda não testada |
| Alertas | Preferência da conta passou a controlar também os avisos N1, forward e motor manual | Sem push remoto ou acompanhamento com o app fechado |
| Conta e assinatura | Preferências funcionam localmente; estados de preparação preservados | Supabase/login, cobrança e restauração de compras não conectados |
| iPhone web | Manifesto standalone, ícones, metadados Apple e instruções de instalação; área segura superior corrigida | Precisa de internet; não é IPA/TestFlight |
| iPhone nativo | WebView mantém a interface do site; TypeScript, testes e exportação iOS passam; perfil TestFlight preparado | Exportação JavaScript não equivale a um IPA assinado; distribuição ainda em preparação |

## Defeitos corrigidos

1. **Horário da fonte:** o relógio do computador estava aproximadamente 34 segundos adiantado. A proteção de 30 segundos descartava cotações recentes. O app agora estima o horário da Kraken pelo ping/pong, ancora a passagem do tempo em relógio monotônico, rejeita amostras lentas e associa a resposta ao pedido correto. Mantém o timestamp original da cotação e bloqueia novos sinais sem sincronização recente. O cache REST preserva a idade dos dados apesar de diferenças entre relógios. Tentativas e watchdog usam tempo monotônico.
2. **Alvo sem ganho líquido:** uma entrada 100, stop 98, alvo 100,25, tick 0,25, tick value 5, custo 10 e slippage 1 produzia “ganho” de −15. Agora o cálculo mostra erro e não produz plano. O caso válido 100/98/104, custo 2, retorna quantidade 1, risco 52 e ganho líquido planejado 68.
3. **Sessão simulada inválida:** uma base diária salva como 1 para capital 100.000 era aceita. A leitura agora reconcilia caixa e patrimônio e valida a base diária reconstruível. Posições que atravessam meia-noite preservam a marca observada e verificam o limite inferior em caixa; isso não é proteção contra adulteração arbitrária do armazenamento local.
4. **Início antes de sincronizar:** criação da sessão forward adiada até conferir o horário de mercado.
5. **Exportação mobile:** revogação imediata do blob do diário podia competir com a leitura assíncrona da ponte nativa; a liberação foi adiada. A correção remove a corrida identificada por inspeção, mas ainda requer teste físico de compartilhamento.
6. **Preferência de alertas:** ligada aos módulos novos, além dos exemplos antigos.
7. **Diário vazio:** o botão de explorar redirecionava para o radar sem abrir o fluxo antigo de registro. Agora gera uma ficha explicitamente artificial e permite exercitar a revisão e o diário local.
8. **Clareza e iPhone:** texto obsoleto do mercado corrigido, preços artificiais identificados, instruções específicas de instalação e proteção da área superior da tela.

A calibração de tempo segue a [documentação oficial do ping/pong Kraken](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/ping).

## Estratégias e resultados

Não foram renomeadas variantes existentes para chamá-las de novas. N3 usa calendário; N4 usa ranking transversal com uma posição. Elas são diferentes das técnicas EMA/Donchian/pullbacks, de N1 (regressão de duas pernas) e de N2 (funding).

| Família | Avaliação | Resultado líquido | Decisão |
| --- | --- | --- | --- |
| N1 — relação ETH/BTC | Triagem anterior, 313 operações | −54,36%; PF 0,45; DD 55,45% | Reprovada |
| N2 — funding spot/perpétuo | Especificação | Sem histórico completo de funding/perpétuo; sem métricas | Não testada; não validada |
| N3 — calendário BTC | 2025 / jan–ago 2026 | −24,92% / −13,64% | Reprovada |
| N3 — calendário ETH | 2025 / jan–ago 2026 | −37,33% / −17,60% | Reprovada |
| N3 — calendário SOL | 2025 / jan–ago 2026 | −57,44% / −19,51% | Reprovada |
| N4 — rotação BTC/ETH/SOL | 2025 / jan–ago 2026 | −6,35% / −18,59% | Reprovada |

N4 ganhou +242,98% no desenvolvimento 2022–2024, mas perdeu nas avaliações posteriores. O ganho no período de desenvolvimento não sustenta aprovação. O stress elevou as perdas. Não foi ajustado parâmetro após observar os resultados para fabricar uma aprovação.

N3/N4: dados Binance spot H1 conferidos por SHA-256; taxa/slippage base por execução de 10/2 bps e stress de 15/5 bps; desenvolvimento 2022–2024, avaliação cronológica em 2025 e período recente jan–ago/2026. Foram registrados protocolos antes destas execuções. O histórico recente já havia sido visto em outros estudos do projeto, portanto **não é um holdout intocado**. São triagens exploratórias, não validação prospectiva nem teste dos contratos da The5ers. Nenhuma aprovação operacional foi adicionada.

Reprodução e detalhes: [N3](../research/calendar/RELATORIO.md), [N4](../research/rotation/RELATORIO-N4.md), [famílias N1/N2](../research/NOVAS_FAMILIAS.md). Protocolos, scripts, critérios e resultados foram preservados no repositório; resumos e JSON estão na área Estratégias do aplicativo.

## Verificações executadas

- `npm test`: oito grupos do motor, incluindo novas regressões de relógio, cache, risco e recuperação de sessão.
- TypeScript web `tsc --noEmit`: aprovado.
- Mobile: `npm run typecheck`, `npm test` e `npm run export`: aprovados; exportação Android/iOS/web, sem afirmar compilação nativa.
- Autotestes `research/calendar/run-calendar.mjs --self-test` e `research/rotation/run-rotation.mjs --self-test`: aprovados.
- Navegador: cotações bid/ask, ficha artificial, erro de risco líquido e cálculo válido, execução do backtest. Troca BTC/ETH e H1 conferida; o painel externo de ouro carregou. A criação e revisão de uma ficha artificial do diário foram exercitadas, com persistência após recarregar. Os três temas foram selecionados e a preferência de alertas foi verificada. A captura automática do download no navegador de teste não confirmou o arquivo; compartilhamento/download físico no iPhone permanece pendente.

## Testar no iPhone

Abra [TraderNova](https://tradernova.willvinicius.chatgpt.site/) no Safari → Compartilhar → Adicionar à Tela de Início. Se aparecer, mantenha “Abrir como App da Web” ligado. A aba Conta contém o roteiro. Depois: Robô → Testar exemplo de sinal → conferir e exportar a ficha; testar o planejador com valores de exemplo; visitar Estratégias, Laboratório e Diário.

A versão nativa usa Expo SDK 57. O Expo Go comum da App Store não atende este SDK; não foi prometido como instalador. O usuário informou possuir Expo e Apple Developer. O perfil `testflight` usa distribuição de loja para iPhone físico. O projeto foi vinculado a `@willvinicius/tradernova-mobile` (ID `f9e6ee09-4b87-47b7-a9b1-a1cbc3ca2a53`). Conta Free com 0/15 builds iOS usados foi conferida. A tentativa não interativa parou na configuração de certificado/perfil, antes da compilação; não há IPA gerado. O usuário decidiu concluir a autenticação/assinatura Apple depois. O comando preparado é `npx eas-cli@24.8.0 credentials:configure-build --platform ios --profile testflight`, dentro de `mobile/`; depois, será possível solicitar build e envio para TestFlight. Nenhum TestFlight ou teste físico foi declarado como concluído. [Instalação web Apple](https://support.apple.com/guide/iphone/open-as-web-app-iphea86e5236/ios), [ambiente Expo iOS](https://docs.expo.dev/get-started/set-up-your-environment/?device=physical&mode=expo-go&platform=ios), [build Expo](https://docs.expo.dev/build/setup/).

## O que impede o OK de produção

- Ausência de estratégia aprovada em avaliação independente, custos executáveis e acompanhamento prospectivo.
- Ausência de feed operacional dos quatro ativos externos e especificações de contrato para dimensionamento real.
- Backend de identidade/sincronização e push ainda não conectados.
- Distribuição nativa assinada e teste físico do iPhone ainda não concluídos.

O OK atual se aplica aos testes técnicos do piloto e às correções verificadas. Não se aplica a rentabilidade, sinais operacionais ou produto comercial integralmente finalizado.
