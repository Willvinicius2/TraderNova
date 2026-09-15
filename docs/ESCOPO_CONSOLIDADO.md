# TraderNova — decisões consolidadas

Consolidado em 15/09/2026 a partir dos chats **Modelos mobile TraderNova** e **Sugestões para projeto MetaTrader**, do plano de lojas anexo e do código recuperado do site.

## Decisões vigentes

1. **Sete ativos:** XAUUSD, Nasdaq 100, BTCUSD, ETHUSD, SOLUSD, EURUSD e USDJPY. Substituem a expansão antiga para 22 ativos.
2. **Três temas:** Essencial Dark (verde), Nova Lab (roxo), Claro & Direto (azul). Seguir o sistema é adicional.
3. O motor informa cenário, estratégia, entrada, stop e alvo; o usuário revisa e decide manualmente no MT5. Não há envio de ordens nem conta de negociação conectada.
4. Separar candidatas, testes e aprovadas. Nenhuma estratégia está aprovada.
5. Preparar Android/iPhone e assinaturas futuras, começando pelo piloto. Recursos dependentes de infraestrutura não devem parecer ativos antes da integração.
6. **Preservar exatamente o modelo visual do site aprovado** no aplicativo: mesmos componentes, cores, ícones, cards e navegação.

## Código e paridade

| Área | Web recuperada | Mobile desta etapa |
| --- | --- | --- |
| Cripto | Kraken REST/WebSocket | Mesmo site na WebView |
| Quatro outros ativos | Widgets TradingView/OANDA | Mesmos widgets do site |
| Indicadores | 10 sobre a série cripto | Mesma implementação do site |
| Temas | 3, preferência no navegador | Mesmos 3 temas, preferência na WebView |
| Alertas/diário | Exemplos locais | Mesma interface e armazenamento na WebView |
| Notificações | Sem push integrado | Deep links preparados; push pendente |
| Laboratório | Histórico/replay/exportação | Mesmo laboratório; compartilhamento JSON nativo |
| Conta/assinaturas | Contratos iniciais | Piloto, sem cobrança |
| Backend | Migração Supabase existente | Integração pendente |

O mobile usa Expo e React Native WebView para abrir a publicação original. Não recria a interface nem duplica o motor. Depende de conexão; armazenamento da WebView e do navegador são separados e ainda não sincronizam pela conta. A referência recuperada do site é `130f8a0`, com histórico Git preservado. Enviar código ao GitHub não atualiza a publicação existente no Sites.

## Estudo histórico relatado nos chats

O último relato descreveu 18 combinações BTC/ETH/SOL em M15/H1, arquivos Binance de setembro/2024 a agosto/2026 e avaliação final março/agosto de 2026. Informou que todas ficaram negativas e nenhuma candidata foi aprovada. **Os arquivos completos não vieram no código recuperado e o estudo não foi reproduzido nesta tarefa.** Esse relato não é um selo de validação. O estudo de compras spot não é equivalente ao teste curto do motor atual, que também simula vendas.

## Próximas integrações

- Definir corretora/contrato do Nasdaq e alimentar o motor com ouro/índices/forex; fonte e horário rastreáveis.
- Supabase Auth, banco e permissões por usuário; revisar/aplicar a migração no ambiente escolhido. Nunca embarcar chave de serviço no app.
- Motor separado, versões, parâmetros, custos, período e operações reproduzíveis; histórico suficiente e avaliação fora da amostra antes de aprovar.
- Push remoto APNs/FCM; registros de sinal no servidor e abertura após login com validade atual.
- Assinaturas mensais/anuais: produtos/preços das lojas, compra/restauração e recibos no servidor. Preços e benefícios não definidos.
- Testes físicos, certificados, contas, privacidade/exclusão e materiais das lojas antes de publicar comercialmente.
- VTuber/live de Bitcoin e ouro: ideia comercial registrada como expansão futura; não implementada nesta etapa.

## Custos

Nenhuma infraestrutura paga, cobrança, conta de loja ou serviço de negociação foi ativado. Estimativas antigas de gratuidade são hipóteses de piloto, não garantia de custo atual.
