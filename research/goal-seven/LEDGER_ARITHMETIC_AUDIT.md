# Conferência aritmética do testador — 29/09/2026

As **1.120 operações** de N14 e N15, nos cenários base e stress, passaram na reconciliação decimal separada do executor. O auditor não importa o motor de simulação nem recalcula sinais históricos. Confere os SHA-256 dos registros antes de ler as operações.

Foram conferidos comissão nas duas pontas, PnL líquido incluindo o funding registrado, risco planejado de 0,25% do saldo anterior, limite de exposição de 1×, perda planejada até o stop, sequência temporal sem posições sobrepostas, quantidade de operações, saldo final, retorno e fator de lucro. Tolerância absoluta: 0,000001. O drawdown informado supera o limite inferior reconstruído apenas com saldos de operações encerradas nos quatro casos.

O teste sintético existente `tests/goal-execution-v4.py` também passou novamente: compras/vendas, custos, gaps, funding e ausência de dados. Nenhuma alteração foi feita no executor congelado ou na fila N13 em execução.

Essa conferência **não reconstitui funding a partir dos eventos originais nem comprova a trajetória intrabar**, preços executáveis, publicação histórica ou equivalência contratual. Não constitui revisão independente por outro avaliador. Os resultados econômicos e as reprovações de N14/N15 permanecem iguais; **0/7 estratégias aprovadas**.

Evidência: [ledger-arithmetic-audit.json](ledger-arithmetic-audit.json). Reprodução local, sem chamadas de IA ou rede:

```powershell
python scripts/audit-goal-ledger.py research/goal-seven/miner-pressure-results.json research/goal-seven/stablecoin-liquidity-results.json
python tests/goal-execution-v4.py
```

O auditor aceita outros arquivos de resultados com o mesmo contrato de registro. Ele apenas verifica consistência contábil; jamais promove automaticamente uma estratégia.
