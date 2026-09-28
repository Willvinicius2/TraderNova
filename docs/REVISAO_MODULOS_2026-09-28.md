> Revisão posterior e situação atual: [Auditoria 0.6](AUDITORIA_FINAL_2026-09-28.md).

# Revisão TraderNova · piloto 0.5

## Entrega desta rodada

Preservados os três temas, as interfaces web/mobile e os sete ativos: XAUUSD, NAS100, BTCUSD, ETHUSD, SOLUSD, EURUSD e USDJPY. Referência de mesa informada: The5ers. Sem conexão de conta ou envio de ordens.

| Módulo | Implementado e verificado | Limite atual |
| --- | --- | --- |
| Mercado | Sete ativos na interface; cripto com REST/WebSocket e recuperação | Ouro, Nasdaq e FX via widgets; motor sem feed desses quatro contratos |
| Radar | Nova regra causal N1 ETH/BTC, duas pernas, quotes recentes, janela de 60s, deduplicação, pausa e exportação | Experimental e reprovada na triagem; Kraken spot é proxy, não contrato da mesa; roda com a tela aberta |
| Detalhe | Entradas bid/ask observadas, direção por perna, beta, alvo e invalidação conjuntos, prazo máximo e explicação | Níveis conjuntos não são ordens stop individuais; o radar não administra saídas reais |
| Risco | Planejador dos sete ativos: ticks, valor do tick, custos, slippage e lote arredondado para baixo | Especificações informadas pelo usuário; somente contrato linear; não calcula margem ou risco conjunto de pares |
| Estratégias | Inventário das famílias anteriores e duas novas famílias sem renomear variantes | N1 rejeitada; N2 depende de funding/perpétuo e não possui métricas |
| Laboratório | Testes e relatórios anteriores preservados; novo backtest N1 reproduzível com duas pernas | Sem estratégia aprovada; estudo retrospectivo não equivale à validação prospectiva |
| Diário | Histórico local de hipóteses N1, revisão/ignorar e exportação JSON; diário antigo preservado | Sem sincronização entre celular e navegador; não registra posição real |
| Mobile | WebView com visual original, retorno Android, exportação, temas e recuperação de falhas | Bundles Android/iOS preparados; APK/IPA e aparelho físico não verificados |
| Conta | Preferências locais | Login próprio, Supabase e sincronização ainda não conectados |
| Alertas | Avisos dentro da tela ao observar condição nova | Sem push com app fechado ou worker contínuo |
| Assinaturas | Estado de preparação preservado | Sem cobrança, lojas ou produtos ativados |

## Testar agora

1. Abrir o endereço publicado no navegador do celular ou PC.
2. Entrar em **Robô → Testar exemplo de sinal**. A ficha artificial é identificada e não é misturada ao histórico de preços reais.
3. Conferir as duas pernas, alvo conjunto, invalidação, regras completas e exportação.
4. Deixar o radar aberto para observar fechamentos H1. Ausência de condição é um resultado normal. Pausar interrompe novas observações.
5. Abrir **Estratégias** para ver a reprovação de N1 e os dados faltantes de N2; **Diário** para decisões locais.
6. Em **Planejar entrada e risco**, preencher o tick e valor de tick do contrato real; conferir compra/venda, stop, alvo e orçamento.

No aplicativo nativo, `cd mobile; npm run start:go` inicia explicitamente Expo Go, evitando selecionar por engano uma development build que ainda não foi instalada. O aparelho precisa alcançar o servidor. Os bundles de `npm run export` não são APK/IPA. O endereço publicado continua disponível no navegador mobile sem depender do PC.

## Evidência e próximos requisitos

- Suite raiz `npm test`: oito grupos, incluindo causalidade, fontes, timestamps, expiração e risco por tick.
- TypeScript web e mobile; testes mobile e export Android/iOS/web.
- Novo backtest e autoteste em `scripts/research-pairs.mjs`; resultados e fontes em `research/NOVAS_FAMILIAS.md` e `public/research/novel-study.json`.
- Critérios de aprovação antigos preservados. Nenhuma aprovação adicionada para completar a interface.
- Para sinais operacionais dos sete ativos: feed executável dos símbolos da mesa, custos reais, avaliação independente e observação prospectiva. N2 requer um perpétuo com pagamentos de funding, que não pode ser presumido como disponível na The5ers.
- Para produção comercial nativa: teste em aparelho, identidade/sincronização, push, certificados e distribuição. Java/Android SDK não estavam disponíveis neste computador; não foi gerado APK local.

Conclusão: piloto de pesquisa e interfaces ampliados; não constitui produto final de sinais validados.
