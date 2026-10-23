# Agente r4-ehlers-classicos: notas (BTCUSD, protocolo lab-v2, rodada 4)

O TradingView não abre pelo WebFetch. As páginas dos scripts vieram do WebSearch, e o código Pine do repositório público do autor (github.com/everget/tradingview-pinescript-indicators, cópia em /home/user/labdata/pine/everget_...). Nenhum dos quatro repinta. Os quatro são indicadores sem regra de trade nem stop. A entrada foi o cruzamento descrito na FILA ou pelo autor, a saída o sinal oposto, e o stop de proteção k*ATR14. Entrada e saída na abertura seguinte (motor).
Os quatro saíram REPROVADA_VALIDACAO. O protocolo proíbe refinar depois de abrir a validação, então não houve refinamento.

## TV48_decycler: Ehlers Decycler Oscillator (everget)
- Fonte: tradingview.com/script/5xelSGhd-Ehlers-Decycler-Oscillator; Pine `oscillators/ehlers_decycler_oscillator.pine`; Ehlers, S&C set/2015.
- Regra: Osc = 100*K*HP(close − HP(close,P), 0,5P)/close, com linhas P1 (K=1) e P2=0,8*P1 (K=1,2). Modo "cross": linha 2 cruza a linha 1 (descrição do autor). Modo "zero": linha 1 cruza 0 (FILA).
- Grade: P1 75/100/125/150, modo, k 2/3, lado; H1/H4/D1 (96).
- Veredito: **REPROVADA_VALIDACAO**. Escolha: H4, P1=125, modo zero, k=2, só compra.
  Dev 171 trades, +167,1R, PF 3,17, DD 7,3R (3,7%). Val 63 trades, −8,4R, PF 0,77, DD 13,2R (6,6%), stress −11,6R. DSR 0,998.
- Interpretação: na prática é um filtro de tendência comprado. Ganhou muito na alta de 2016–2020 e perdeu em 2021–22.

## TV49_cyber_cycle: Ehlers Cyber Cycle (everget)
- Fonte: tradingview.com/script/Rol6rD2Y-Ehlers-Cyber-Cycle; Pine `oscillators/ehlers_cyber_cycle.pine`; Ehlers, *Cybernetic Analysis*, cap. 4.
- Regra: Smooth=(C+2C1+2C2+C3)/6. Cycle = passa-alta de 2 polos com alpha. Compra quando Cycle cruza acima de Cycle[1], vende no inverso. O Pine do everget usa alpha=0,7 por padrão (o "length" não é usado) e Ehlers usa 0,07, então a grade cobre de 0,05 a 0,7.
- Grade: alpha 0,05/0,07/0,1/0,15/0,3/0,7, k 2/3, lado; H1/H4/D1 (72).
- Veredito: **REPROVADA_VALIDACAO**. Escolha: D1, alpha=0,1, k=2, só compra.
  Dev 209 trades, +43,1R, PF 1,98, DD 4,2R (2,1%). Val 89 trades, −5,3R, PF 0,77, DD 9,3R (4,7%), stress −6,9R. DSR 0,788.
- Interpretação: comprar a virada do ciclo no diário só deu certo no mercado de alta.

## TV50_center_gravity: Ehlers Center of Gravity (everget)
- Fonte: tradingview.com/script/cbPsaSCd-CG-Oscillator-Center-of-Gravity; Pine `oscillators/center_of_gravity_oscillator.pine`; Ehlers, *Cybernetic Analysis*.
- Regra: fonte hl2. CG = −Σ(i+1)*src[i]/Σsrc[i] em L candles. Compra quando CG cruza acima de CG[1], vende no inverso.
- Grade: L 6/8/10/14/20, k 2/3, lado; H1/H4/D1 (60).
- Veredito: **REPROVADA_VALIDACAO**. Escolha: D1, L=8, k=2, só compra.
  Dev 193 trades, +62,1R, PF 3,13, DD 2,5R (1,3%). Val 84 trades, −5,2R, PF 0,77, DD 9,2R (4,6%), stress −6,7R. DSR 0,999.
- Interpretação: o PF de 3,1 no desenvolvimento era o vento da alta. Na validação o resultado é o mesmo do Cyber Cycle (as duas regras compram viradas de curto prazo).

## TV51_roofing: Ehlers Roofing Filter (everget)
- Fonte: tradingview.com/script/rVixuZKT-Ehlers-Roofing-Filter; Pine `oscillators/ehlers_roofing_filter.pine`; Ehlers, S&C V.32:1 (2014).
- Regra: passa-alta de 2 polos (hp) e depois SuperSmoother de 2 polos (ssf) de (HP+HP1)/2. Modo "zero": cruza 0. Modo "lag2": cruza Roof[2].
- Grade: hp 32/48/64/80, ssf 10/14, modo, k 2/3, lado; H1/H4/D1 (192).
- Veredito: **REPROVADA_VALIDACAO**. Escolha: H4, hp=80, ssf=14, modo zero, k=2, só compra.
  Dev 278 trades, +151,1R, PF 2,42, DD 8,4R (4,2%). Val 119 trades, −8,1R, PF 0,86, DD 17,6R (8,8%), stress −14,1R. DSR 0,995.
- Interpretação: mesmo padrão. A escolha ficou no ciclo mais longo e só comprado, ou seja, seguiu a tendência de alta do desenvolvimento, e isso não se manteve em 2021–22.

Padrão geral: em todos, o desenvolvimento escolheu "só compra" e o DSR alto não protegeu, porque o viés vem do regime de alta de 2016–2020 e não da sorte na seleção.
