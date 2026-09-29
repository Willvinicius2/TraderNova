# Continuidade da meta

Estado central: [STATUS.md](STATUS.md), **0/7**, meta ativa. Os critérios de [protocol.json](protocol.json) continuam congelados. N2, N5, N6, N7, N11 e N12 reprovaram a triagem financeira; N8 e N10 não atingiram a amostra; N9 aguarda dados de custos executáveis. Não reabrir janelas posteriores para resgate nem contar uma variante como outra família.

N14 foi pesquisada e testada enquanto a fila N13 aguardava dados: também reprovou, com resultados preservados em [MINER_PRESSURE_SCREEN.md](MINER_PRESSURE_SCREEN.md). Não inverter sua direção nem ajustar suas médias para resgatar o resultado.

N15 (emissão de stablecoins) também encerrou reprovada: base +1,92%, PF 1,062 abaixo do mínimo; stress −0,86%. [STABLECOIN_LIQUIDITY_SCREEN.md](STABLECOIN_LIQUIDITY_SCREEN.md). O lucro base isolado não habilita avaliação posterior ou aprovação. Não alterar a cesta, duração ou filtro de paridade para resgate.

A frente atual é **N13**, [skew de opções para sinais em futuros](OPTIONS_SKEW_IDEA.md). A [rodada ampliada](N13_BULK_RUN.md) foi iniciada após os pilotos e suas auditorias; conferir o processo antes de qualquer retomada. O campo IV permanece na unidade nativa da fonte: a regra é invariante a uma escala constante positiva, sem inferir percentual ou anualização. Nenhum skew, sinal ou PnL real N13 foi calculado.

Antes de testar N13:

1. Usar somente `download-goal-options-trades-v2.py` para continuar a aquisição. Preserva v1 por referência, usa `count=10000`, folhas temporais sem truncamento e lock exclusivo. Conferir manifesto/PID antes de retomar: nunca iniciar um segundo coletor. Limites da rodada ampliada planejada: 15.000 GETs, 20 GB brutos, 12 horas, uma consulta por segundo no máximo e 5 GB de cache. Erros/403/parciais interrompem explicitamente; não viram cobertura completa. Não alterar código de uma rodada ativa.
2. Após cobertura integral e encerramento do coletor, executar `audit-goal-options-trades.py`: exigir auditoria global completa dos IDs, respostas e reconciliação exata entre pais e folhas. O piloto passou apenas no snapshot parcial `2a9e16fa3654b2a7`. Catálogos oficiais BTC/ETH completos foram adquiridos; o join piloto passou, mas o join integral ainda precisa ser executado e preservado antes de qualquer filtro econômico. Catálogo atual não comprova disponibilidade histórica.
3. O pipeline offline está implementado e testado: `prepare-goal-options-skew.py` audita metadados e agrega somente após freeze; `run-goal-options-skew.py` congela fontes, conta amostra e executa DEV; `goal-lab.py` encadeia essas fases sem chamadas a modelos. Consultar [LAB.md](LAB.md) e o estado local antes de iniciar outra instância. Gerador e executor short v4 preservam v1–v3 e os estudos anteriores. Nenhum agregado real foi usado para ajustar a regra.
4. Congelar regra, dados, custos, código, testes e auditorias antes de calcular os skews reais e contar condições. Executar só desenvolvimento; amostra inferior a 100 gatilhos encerra sem PnL, reprovação financeira encerra sem consultar 2025–2026. Passar na triagem não aumenta a contagem de aprovadas. Manter evidências históricas como exploratórias; custos/contrato The5ers e a etapa prospectiva permanecem pendentes.

O coletor de observações públicas [descrito aqui](OBSERVATIONS.md) roda localmente com duração máxima de 24 horas. Conferir `status.json` com o processo antes de declarar que está ativo. Ele não gera sinais nem inicia automaticamente um teste prospectivo. Não alterar seu código durante uma rodada. A assinatura Apple continua adiada pelo usuário.
