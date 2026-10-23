# r4-ehlers-tasc (rodada 4, bloco 3: Ehlers na TASC)

Ativo BTCUSD, protocolo lab-v2. Código conferido com a tradução do Pine em /home/user/labdata/pine (deepentropy, src/community). Nenhum dos scripts tem stop: uso k×ATR14 como stop de proteção. Todas reprovaram na validação; a reserva não foi aberta e o protocolo proíbe refinamento depois de ver a validação.

## TV44_trendflex: Reflex & Trendflex (e2e4; Ehlers, TASC fev/2020)
- Fonte: https://www.tradingview.com/script/6tSfPE3W-Reflex-Trendflex/ e o código traduzido `reflex-trendflex.ts`.
- Regra: Trendflex = média de (SuperSmoother − SuperSmoother[i]), i=1..N, normalizada por RMS (0,04/0,96). Compra quando cruza acima de 0, vende quando cruza abaixo, sai no cruzamento oposto.
- Grade: N {10,20,30,40}, k {2,3,4}, lado {long, both} × H1/H4/D1 = 72.
- Veredito: **REPROVADA_VALIDACAO**. Escolha H4, N=40, k=3, só compra.
- Desenvolvimento: 139 trades, +144,8R, PF 4,02, DD 5,2R. Validação: 69 trades, −19,5R, PF 0,49, DD 19,9R (stress −22,0R).
- Leitura: é um seguidor de tendência que surfou a alta do BTC de 2016 a 2020 e perdeu na lateral/queda de 2021–22. É o mesmo padrão dos outros seguidores de tendência da rodada.

## TV45_reversion_index: TASC 2026.01 The Reversion Index (PineCodersTASC)
- Fonte: https://www.tradingview.com/script/V35NeC45-TASC-2026-01-The-Reversion-Index e o código traduzido `tasc-2026-01-the-reversion-index.ts`.
- Regra: razão Σd/Σ|d| em L candles; Smooth = SuperSmoother 8, Trigger = SuperSmoother 4. Compra quando o Smooth cruza acima do Trigger com Smooth < −nível, vende no inverso com Smooth > +nível, sai no cruzamento oposto.
- Grade: L {10,14,20,30,40}, nível {0; 0,2; 0,4}, k {2,3}, lado × 3 tempos gráficos = 180.
- Veredito: **REPROVADA_VALIDACAO**. Escolha D1, L=40, nível 0, k=3, só compra.
- Desenvolvimento: 60 trades, +3,2R, PF 1,46, DD 3,8R (DSR 0,0). Validação: 40 trades, −0,2R, PF 0,97.
- Leitura: a vantagem já era mínima no desenvolvimento (+3R em 5 anos, DSR 0, ou seja, sorte na seleção) e sumiu na validação.

## TV46_cybernetic: TASC 2025.06 Cybernetic Oscillator (PineCodersTASC)
- Fonte: https://www.tradingview.com/script/QwMaFZTL-TASC-2025-06-Cybernetic-Oscillator e o código traduzido `tasc-2025-06-cybernetic-oscillator.ts`.
- Regra (modo "Trend"): passa-alta de 2ª ordem (HP) + SuperSmoother (LP), dividido pelo RMS de 100 candles. Compra quando cruza acima de 0, vende quando cruza abaixo. O RMS não muda o sinal, então fica fixo.
- Grade: LP {10,15,20}, HP {30,45,60,90}, k {2,3}, lado × 3 tempos gráficos = 144.
- Veredito: **REPROVADA_VALIDACAO**. Escolha H4, LP=20, HP=90, k=2, só compra.
- Desenvolvimento: 240 trades, +159,1R, PF 2,69, DD 6,3R. Validação: 99 trades, −11,9R, PF 0,79, DD 20,4R (10,2% da conta, acima do limite).
- Leitura: mesmo caso do Trendflex, um seguidor de tendência que dependeu da alta de 2016 a 2020.

## TV47_continuation_index: TASC 2025.09 The Continuation Index (PineCodersTASC)
- Fonte: https://www.tradingview.com/script/5ZrOut79-TASC-2025-09-The-Continuation-Index/, https://traders.com/Documentation/FEEDbk_docs/2025/09/TradersTips.html e o código traduzido `tasc-2025-09-the-continuation-index.ts`.
- Regra: CI = tanh(2·(UltimateSmoother(L/2) − Laguerre(L, gamma, ordem))/SMA|·|). Comprado ao cruzar acima de +0,5 e fora ao voltar abaixo de +0,5; vendido abaixo de −0,5 e fora ao voltar acima.
- Grade: L {20,30,40,60,80}, gamma {0,6; 0,8}, ordem {4,8}, k {2,3}, lado × 3 tempos gráficos = 240.
- Veredito: **REPROVADA_VALIDACAO**. Escolha H4, L=80, gamma 0,8, ordem 8, k=2, só compra.
- Desenvolvimento: 156 trades, +196,4R, PF 3,54, DD 7,9R. Validação: 69 trades, −19,1R, PF 0,59, DD 25,8R (12,9% da conta).
- Leitura: forte no BTC em alta, perdedor em 2021–22. A troca de filtro de Ehlers não mudou o comportamento de seguidor de tendência comprado.
