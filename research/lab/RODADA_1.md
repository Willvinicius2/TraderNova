# Rodada 1 (21/10/2026): conclusão

20 estratégias publicadas e inéditas no projeto, 5 famílias, 26 execuções contando 6 refinamentos, BTCUSD Bitstamp. Tabela completa em `RELATORIO.md`.

- **3 CANDIDATAS** passaram em desenvolvimento, validação e reserva com custo base e stress. Nenhuma está aprovada para sinal real:
  - **L07 Estocástico de Lane (D1, só compra):** a mais estável (PF ~1,5 nas três fases, segue positiva sem a maior operação), mas rende pouco: ~7 operações e ~1R por ano. DSR 0,22.
  - **L12 Rompimento de Keltner (H4, compra e venda):** positiva nas três fases, mas na reserva o drawdown foi 40R (~20% com 0,5% de risco), acima do limite de perda total de 10% da conta, e sem a maior operação a reserva quase zera (+2,8R). Exigiria risco por operação bem menor.
  - **L04 Momentum de 60 dias (D1, só compra):** na validação depende de uma operação (sem ela, −3,6R). Na prática é "ficar comprado quando o BTC sobe há 60 dias". DSR 0,03.
- **17 reprovadas.** 13 brilharam no desenvolvimento e quebraram na validação: o período 2016–2020 foi de alta forte e as versões "só compra" pareciam ótimas só por estarem compradas. Pivôs e MFI reprovaram no desenvolvimento, passaram após refinamento e quebraram na validação. Sazonalidade de horário e VWAP não passaram nem no desenvolvimento, mesmo com 2 refinamentos cada.

## Mudanças para a rodada 2 (protocolo lab-v2, registrar antes de rodar)

1. Exigir que a estratégia supere uma exposição comprada equivalente (benchmark) no desenvolvimento, para não premiar "estar comprado na alta".
2. Exigir resultado positivo sem a maior operação em cada fase e drawdown em % dentro do limite da conta (10% total, 3% diário).
3. Rodar em mais de um ativo assim que houver dados acessíveis (ouro, EURUSD, ETH); a rede atual só permitiu o BTC via GitHub.
4. Calcular o DSR só entre combinações do mesmo tempo gráfico e escolher pelo Sharpe, como apontaram os agentes.
5. Acompanhamento prospectivo (simulação em tempo real) das 3 candidatas a partir de agora.
