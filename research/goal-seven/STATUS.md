# Meta: sete estratégias distintas validadas

Meta registrada em 28/09/2026. **Ativa: 0/7 aprovadas.**

Critérios congelados em [protocol.json](protocol.json): lucro líquido depois dos custos, fator de lucro base mínimo de 1,20, drawdown conservador máximo de 8% no cenário base e 10% no stress, perdas diárias limitadas e amostra mínima. O risco direcional é definido antes do teste. Reduzir exposição depois de ver o resultado não aprova uma regra.

Cada família econômica conta uma vez. Trocar ativo, período, direção, parâmetro ou nome não cria outra estratégia. Os testes anteriores e as reprovações continuam no histórico. O período cripto local até agosto de 2026 já foi examinado; nenhuma nova triagem nesse período será chamada de holdout intocado.

Passar em backtest apenas habilita a etapa seguinte. A contagem exige também observação prospectiva após congelar a regra (mínimo de 60 dias e 100 operações), custos e contrato executáveis, comparação com o motor de sinais e avaliação independente. O estudo mantém controle de múltiplas tentativas para evitar selecionar resultados positivos por acaso. Essas condições demandam tempo e dados reais; não podem ser substituídas por uma simulação retrospectiva renomeada.

## Resultados e trabalho em curso

- Inventário concluído em [DADOS.md](DADOS.md), incluindo limitações de fonte, cobertura e custos por instrumento.
- N5 (fluxo agressor) e N6 (transmissão entre ativos) **reprovadas no desenvolvimento**, sem consultar janelas posteriores para resgatá-las. Resultados e métricas em [DIRECTIONAL.md](DIRECTIONAL.md).
- 504 arquivos oficiais de futuros, mark e funding conferidos por SHA-256; eventos REST reconciliados com os arquivos mensais. Lacunas originais e preços de settlement ausentes foram preservados no manifesto.
- N2 (funding) **reprovada**: a revisão numérica v1.1 manteve +2,21% no cenário base e −4,26% no stress; corrigiu o DD para 8,79% e 9,65%. Amostra insuficiente, violação diária e lacunas também impedem aprovação. [FUNDING.md](FUNDING.md) preserva a versão original e a correção auditada.
- Série oficial de juros reais adquirida: 4.437 observações desde 2009. [REAL_YIELDS_DATA.md](REAL_YIELDS_DATA.md) registra ausência de vintages/timestamps históricos. N7 para ouro **reprovou** no desenvolvimento 2010–2015: −US$3.741,45 base e −US$9.831,43 stress, PF 0,853/0,624. [REAL_YIELDS_SCREEN.md](REAL_YIELDS_SCREEN.md) documenta o estudo; 2016 em diante não foi aberto para resgate.
- N8 (posicionamento CFTC Gold): 1.059 relatórios oficiais preservados, mas apenas **12 sinais** no desenvolvimento 2011–2015, abaixo de 100. Sem PnL; vintages e horários de publicação também não foram comprovados. [COT_DATA.md](COT_DATA.md) registra a consulta adicional de contagens nas janelas seguintes como desvio da sequência DEV-only; elas não são holdout intocado e não foram usadas para mudar parâmetros.
- N9 (carry de FX): **dados insuficientes**, sem backtest. Faltam swaps históricos e preços Bid/Ask do contrato. Taxas de bancos centrais e swap atual não substituem o custo realmente cobrado no passado. [FX_CARRY_DATA.md](FX_CARRY_DATA.md).
- N10 (base de futuro BTC com vencimento): 108 ZIPs oficiais conferidos; **2 episódios limpos observáveis**, abaixo de 100. Revisão v1.1 corrigiu a leitura antecipada de OHLC na abertura e preservou código/resultados anteriores; as contagens ficaram iguais. Sem PnL ou consulta de sinais em 2025–2026. [DATED_SAMPLE.md](DATED_SAMPLE.md).
- N11 (contração de posições abertas + queda de preço): 3.291 ZIPs oficiais conferidos; **reprovada no desenvolvimento**. Base: 180 operações, −9,95%, DD 10,18%; stress: 157 operações, −10,16%, DD 10,31%. Ambos violaram o limite da conta. Lacunas de OI também impedem aprovação. Relatório em [OPEN_INTEREST_SCREEN.md](OPEN_INTEREST_SCREEN.md); nenhuma consulta de resultados de 2025–2026 para resgate.
- N12 (atividade de transferências on-chain): a proposta inicial de valor ajustado ficou indisponível. A substituição por contagem de transferências foi registrada antes de consultar a série, sem contar outra família. **Reprovada**: 593 operações base, −9,72%, DD 9,96%; 277 stress, −10,13%, DD 10,36%, com violação da conta. Séries diárias e preços completos; sem consultar desempenho de 2025–2026. [ONCHAIN_COUNT_SCREEN.md](ONCHAIN_COUNT_SCREEN.md).
- N13 (assimetria de IV nas opções para sinais direcionais de futuros): hipótese registrada, **sem sinais ou PnL**. O piloto encerrou em 10 GETs/1,96 MB brutos, com hashes verificados; cobertura e auditoria global ainda incompletas. Seis testes do coletor passaram. [OPTIONS_SKEW_IDEA.md](OPTIONS_SKEW_IDEA.md), [piloto](OPTIONS_TRADES_PILOT.md), [próximos passos](NEXT_STEPS.md).
- Coletor público local iniciado por até 24 horas, a cada cinco minutos; primeiro ciclo conferido com 13/13 respostas. Preserva bytes e horários de recebimento. O relógio do PC está cerca de 33 segundos adiantado, explicitamente sinalizado; não certifica disponibilidade histórica nem valida uma estratégia. [OBSERVATIONS.md](OBSERVATIONS.md).
- Todas as tentativas e reprovações permanecem registradas; nenhuma redução dos critérios após os resultados.

## Contagem e continuidade

Nesta etapa foram testadas cinco famílias novas (N5, N6, N7, N11, N12) e foi finalmente testada a N2, que aguardava dados. As seis reprovaram. Não são seis aprovadas nem variantes contadas repetidamente. A auditoria do histórico encontrou [pelo menos 73 configurações/parametrizações anteriores](LEGACY_TRIALS.md), além das novas famílias; esse limite inferior não serve como contador exato de testes estatísticos independentes.

A meta permanece ativa. A frente atual é N13, com informações de opções como variável para sinais de futuros, sem negociação de opções. A coleta pública de observações BTC/ETH/SOL com timestamps de recebimento está em execução local limitada a 24 horas. Essa coleta não aprova estratégias nem inicia seu teste prospectivo automaticamente. Estratégias com o mesmo mecanismo não serão somadas novamente por trocar instrumento ou parâmetros.

Nenhuma candidata desta rodada foi promovida à etapa prospectiva ou ao registro de sinais operacionais. Se pesquisas futuras passarem nas triagens, ainda precisarão satisfazer os critérios independentes, de execução e de observação prospectiva registrados; a quantidade desejada não comprova que sete resultados aprováveis existam.

A assinatura Apple permanece adiada pelo usuário. Nenhuma ordem ou contratação de serviço pago faz parte desta meta.
