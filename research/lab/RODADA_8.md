# Rodada 8 (22/10/2026): clássicas da lista FILA.md

Nesta rodada, 4 agentes testaram 16 estratégias clássicas (L21–L36) no BTCUSD, com o protocolo lab-v4:

- **Tendência:** KAMA, inclinação de regressão, MAMA/FAMA e TII.
- **Momento:** Coppock, KST, TRIX e Ultimate Oscillator.
- **Osciladores:** DeMarker, TD Setup 9, Laguerre RSI e z-score.
- **Estrutura e regime:** Chandelier, Wide Range Bar, Market Structure e Hurst.

## Resultado

**0 candidatas.**

- **13 reprovaram na validação:** 12 já na versão original e o Ultimate Oscillator na 3ª versão.
- **1 reprovou na reserva:** TD Setup 9 com filtro de tendência (DSR 0,04).
- **2 reprovaram no desenvolvimento mesmo com 2 refinamentos:** Ultimate Oscillator nas duas primeiras versões e z-score.

O padrão das rodadas 5–7 continuou. Mesmo com "both" na grade, quase toda combinação escolhida foi **só compra** (as 4 de tendência e as 3 de momento que passaram no desenvolvimento). Essas combinações tiveram PF de 3 a 7 no desenvolvimento (2016–2020) e perderam na validação (2021–22).

## Placar acumulado

| Item | Valor |
|---|---|
| Estratégias testadas no laboratório | 135 |
| Candidatas no BTC | 11 |
| Aprovadas | 0 |
| Candidatas que passaram em EURUSD ou USDJPY | nenhuma |

## Plano para a rodada 9 (lab-v5)

A escolha no desenvolvimento passa a aceitar só combinações que operam os dois lados ("both"), ou só vendido quando a regra for assim. Combinações "só compra" no BTC continuam rodando e aparecendo no relatório, mas não podem ser escolhidas. Isso precisa ser registrado em `protocol.json` antes da rodada 9.

O motivo: em 8 rodadas, a seleção só compra no BTC 2016–2020 escolheu a alta do mercado, não a regra.
