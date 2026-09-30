# Revisão de independência — rodada 9

Leitura dos registros locais; `round-9-primary-feasibility.md` estava ausente na única verificação. Nenhum mecanismo novo foi fornecido para julgar. Contagem segue 0/7.

## Classes já inventariadas

- **Preço/tendência e padrões técnicos:** S1–S6, T1–T3, G1–G5 e telas FX já cobrem pullback/tendência, rompimento/reteste, reversão à média, POC, varredura de liquidez, oferta-demanda, abertura, Bollinger, RSI/Donchian. Trocar ativo, período ou indicador não cria família.
- **Valor relativo/rotação:** N1 spread ETH/BTC por OLS e N4 rotação transversal foram rejeitados; N19 spread executável entre venues está em estudo. Mesmo ativo/mesmo par e convergência cross-venue devem ser comparados a esses registros.
- **Funding, carry e basis:** N2 funding com hedge rejeitado; N9 carry FX sem custos históricos; N10 basis de futuro datado com amostra insuficiente. Alterar instrumento sem mudar fonte econômica não cria família.
- **Fluxo e microestrutura:** N5 agressão e N6 transmissão BTC→ETH rejeitados; N11 contração de OI com preço rejeitada. N16 liquidação/recuperação, N21 resiliência de profundidade L2 e N19 arbitragem estão em estudo, cada qual no máximo uma família.
- **Posicionamento, dados externos e macro:** N7 choque de juros reais/XAUUSD rejeitado; N8 COT com amostra insuficiente; N12 transferências on-chain, N14 pressão de mineração e N15 emissão de stablecoin rejeitadas. N17 fluxo ETF, N18 depósitos em exchanges e N20 surpresa CPI estão em estudo.
- **Opções e crédito:** N13 assimetria IV para direção de futuros rejeitada; prêmio de volatilidade com perda definida em IDEIAS permanece a mesma classe de opções. N22 aperto de crédito Aave/ETH está em estudo; variações de reserva, limiar ou ativo não contam separadamente.

## Critérios para revisar a proposta quando existir

1. Exigir mecanismo/cashflow distinto, com comparação explícita a S/T/G, N1–N22 e às classes de IDEIAS; combinações de indicadores, novos parâmetros ou novos ativos continuam a família existente.
2. Exigir publicação e `received_at`, revisões/vintages, cobertura PIT e causalidade no instante da decisão; snapshots atuais ou série reconstruída sem proveniência não bastam.
3. Exigir CFD The5ers executável correspondente, bid/ask, contrato, comissão, spread, slippage e financiamento observáveis. Binance spot/L2 e leituras Aave não substituem preços/custos do CFD.
4. Dados/custos/UTC/contrato ausentes significam bloqueio, não aprovação nem convite a ajustar parâmetros ou escolher outra janela. Sem ordens, APIs pagas ou exceções aos gates; zero aprovadas.

A classificação econômica da proposta da rodada 9 fica pendente até o arquivo de viabilidade ser criado.

Integração root após publicação do arquivo: proposta CFTC BTC recusada como duplicata de N8/H3, mesmo crowding/unwind por classes reportáveis. Trocar ativo/categoria não é mecanismo novo. Nenhuma família adicionada nem estudo financeiro iniciado.
