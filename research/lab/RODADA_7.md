# Rodada 7 (22/10/2026): blocos 13, 14, 15 e 17 da fila do TradingView

16 scripts do TradingView testados por 4 agentes, no BTCUSD, com o protocolo **lab-v4**. O lab-v4 foi registrado antes desta rodada: na validação e na reserva, a queda máxima de 10% também precisa valer no custo stress.

O bloco 16 (específicos do BTC: Mayer Multiple, CME Gap, Pi Cycle, Weis Wave) ficou para depois. Essas regras não dão para levar a outro ativo, e a meta pede passar em dois.

## Resultado

**1 CANDIDATA e 15 reprovadas** (14 na validação; TV95 Market Profile no desenvolvimento, mesmo com 2 refinamentos).

**TV85 AI Trend Navigator [K-Neighbor] (Zeiierman)**, H4, compra e venda:

| Fase | Operações | Resultado | PF | Queda máxima |
|---|---|---|---|---|
| Desenvolvimento | 68 | +194,4R | 5,91 | 3,3% |
| Validação | 29 | +9,7R | 1,54 | 4,4% |
| Reserva | 70 | +39,4R | 1,89 | 4,5% |

A vantagem é frágil:

- **Depende de uma operação:** sem a maior operação, a validação fica em só +0,12R.
- **Placebo (mediana):** +45,8R no desenvolvimento, −2,5R na validação e +11,5R na reserva. A regra bateu o placebo na maioria dos sorteios.
- **Outros ativos:** reprova no EURUSD (reserva −19,7R) e no USDJPY (negativa sem a maior operação).
- **Como opera:** é um seguidor de tendência lento, que vive de poucas tendências grandes.

## Destaques das reprovadas

- **TV101 Rex:** passou na validação no custo base (+6,6R, PF 1,20), mas perdeu no stress (−0,13R).
- **TV86 e TV87 (ML):** os originais têm defeitos. A "regressão logística" do TV86 tem o peso fixo em zero. O kNN do TV87 sempre escolhe o próprio fechamento, o que vira uma SMA. Os dois foram reproduzidos fielmente e reprovaram.
- **Seleção "só compra":** a maioria das escolhidas continuou sendo "só compra", mesmo com "both" na grade.

## Placar acumulado

- Estratégias testadas no laboratório: 119.
- Candidatas no BTC: 11.
- Aprovadas: 0.
- Nenhuma candidata passou no EURUSD nem no USDJPY.

## Próximo passo

A fila do TradingView (TV36–TV103) terminou, exceto o bloco 16. As próximas rodadas vão para a lista de ideias de `FILA.md`, priorizando regras que operam dos dois lados ou que têm filtro de regime.
