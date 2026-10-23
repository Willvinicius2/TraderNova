# Rodada 9 (23/10/2026, protocolo lab-v4)

15 itens restantes da FILA.md em 4 agentes, mais o agente de dados (ouro e Nasdaq 100). Notas em `notes/r9-*.md`.

| Estratégia | Veredito | Observação |
|---|---|---|
| L37 Dual Momentum | Reprovada na validação | Positiva, mas negativa sem a maior operação. |
| L38 ROC com volatilidade-alvo | **Candidata no BTC** | Placebo 0/20 nas três fases. Reprova em EURUSD, USDJPY, ETH, SOL, ouro e Nasdaq. |
| L39 Relative Vigor Index | Reprovada na validação | |
| L40 Balance of Power | Candidata fraca no BTC | Placebo empata na reserva (7/20). Reprova nos outros ativos. |
| L41 Choppiness como interruptor | Reprovada na validação | Opera os dois lados; ficou perto de zero. |
| L42 Reversão com regime SMA200 | Reprovada na validação | |
| L43 Regime de ATR | Reprovada na validação | |
| L44 Votação de 5 indicadores | Reprovada na validação | |
| L45 Virada do mês | Reprovada na reserva | Efeito some em 2023–2026. |
| L46 Fim de semana | Reprovada na validação | |
| L47 Compra após queda forte (e r1) | Reprovadas | Repique menor que o custo. |
| L48 CCI com divergência | Reprovada na validação | |
| L49 Fair Value Gap (ICT) | Reprovada na validação | |
| L50 Rompimento da nuvem Ichimoku | Reprovada na validação | Depende de uma operação. |
| L51 Rompimento de canal ATR após contração | Reprovada na validação | |

## Ouro (XAUUSD) e Nasdaq 100 (NAS100)
Dados novos (manifestos em `dados/`, scripts em `dados/scripts_r9/`, entradas em protocol.json fixadas antes de qualquer teste).
Todas as candidatas do laboratório rodaram nos dois com os mesmos parâmetros (`_cross_XAUUSD.json`, `_cross_NAS100.json`):
- Passam nas 3 fases: TV72 CUSUM e TV74 RVI no ouro; L04 TSMOM, TV32 Lorentzian e TV74 RVI no Nasdaq.
- **Mas o placebo no próprio ativo (`placebo_ativo.py`) derruba todas:** entradas ao acaso com o mesmo lado e saídas
  ganham parecido na validação (TV74: 9/20 no ouro; L04: 19/20 no Nasdaq; TV32: 9/20; TV72: 12/20). São regras
  "só compra" em ativos que subiram de 2011 a 2025; a vantagem é estar comprado, não a regra. A meta não foi atingida.
- As 135 regras da triagem rodaram nos dois: nenhuma passa (`results/triagem/_cruzado.json`).

## Placar
150 estratégias no laboratório, 1.707 scripts na triagem. Nenhuma regra passa em um ativo fora de cripto com vantagem
acima do placebo. Acompanhamento em papel das regras de cripto segue até 22/11 (`PAPEL.md`).
Lição: a partir de agora, o placebo no ativo cruzado faz parte do teste cruzado (não só no BTC).
