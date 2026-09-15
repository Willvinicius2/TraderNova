# ASTRA GOLD V3 — App mobile, laboratório externo e sinais para decisão humana

Data: 15/09/2026. Responsável pelo projeto: William Vinícius Corrêa.

**Estado desta entrega: especificação e catálogo de hipóteses. Nenhum dado de mercado foi baixado, nenhum backtest foi executado e nenhuma estratégia foi validada nesta revisão.**

## 1. Decisão de produto que substitui a arquitetura anterior

O aplicativo analisa o mercado, testa estratégias e apresenta oportunidades. William faz a segunda análise e decide se executa, altera ou encerra uma operação manualmente no MT5.

Toda a interface, o motor de estratégias, o replay e o testador histórico ficam fora do MT5. A interface principal será mobile, em um app web instalável (PWA), com suporte a uso no computador. O terminal pode continuar como fonte de dados, por um conector de leitura. Uma API direta poderá substituí-lo se fornecer o instrumento e os dados necessários. O desenho de nuvem e os custos estão nas seções 12–14.

Este documento é um complemento que substitui as partes incompatíveis do `ASTRA_GOLD_V2_PLANO_MESTRE.md`, de 08/09/2026. A V2 foi lida para preservar decisões e restrições existentes. A mudança solicitada pelo usuário prevalece sobre o executor automático planejado anteriormente.

| Decisão anterior | Decisão vigente |
|---|---|
| EA em MQL5 executa operações | Motor externo em Python produz sinais; William opera no MT5 |
| Testador do MT5 como ferramenta principal | Testador e replay externos, acessíveis no aplicativo |
| Emergência pode fechar posições automaticamente | Aplicativo bloqueia novos sinais e alerta; fechamento e stop são feitos pelo usuário no MT5 |
| Equivalência Python/MQL5 como caminho principal | Mesmo núcleo de estratégias em Python no histórico, replay e acompanhamento ao vivo |
| Uma estratégia inicial, segunda após verificar a base | Mantido; catálogo de seis candidatas para implementação e pesquisa progressivas |
| Apenas ouro inicialmente | Ouro primeiro; arquitetura preparada para Nasdaq e BTC, com validação separada |

Não haverá botão de enviar ordem, função de negociação remota, negociação por automação de mouse ou permissão de negociação no conector. Marcar “executei no MT5” registra uma decisão; não envia uma ordem.

## 2. Informações conhecidas e pendências

| Item | Situação |
|---|---|
| Conta nominal | 100.000, conforme informação anterior |
| Limites informados | Perda diária 2.999; perda total 10.000 |
| Metas informadas | Fase 1: 10.000; fase 2: 5.000 |
| Moeda, empresa, produto e fórmulas | Ainda não confirmados |
| Instrumentos ativos na primeira versão | XAUUSD, Nasdaq 100, BTCUSD, ETHUSD, SOLUSD, EURUSD e USDJPY; contratos/símbolos exatos pendentes |
| Estratégias e indicadores desejados | POC, SMC, oferta/demanda e outras hipóteses auditáveis |
| Fluxo de decisão | Sinal externo → análise humana → execução manual no MT5 |
| Consumo | Processamento local e orçamento incremental externo inicial zero |

Pesquisar e construir o laboratório pode avançar sem nome da mesa. O simulador deve identificar cenários hipotéticos. Sem regras oficiais e estado atualizado da conta, não mostrar “liberado pela mesa” nem calcular folga contratual como se estivesse confirmada.

## 3. Experiência do usuário

O aplicativo deve ter cinco abas no menu inferior, desenhadas primeiro para celular:

1. **Mercado:** candles, sessão, horário do último dado, spread e indicadores selecionados. Exibir a origem e se o feed é ao vivo, atrasado ou desconectado.
2. **Robô:** ficha clara por sinal, com motivo, entrada, stop, alvo, validade e evidência. Sem oportunidades elegíveis, mostrar “aguardando configuração”. Explicar o estado atual de cada estratégia, seus critérios e o que falta para um sinal.
3. **Estratégias:** repertório, fontes, parâmetros, comparação de versões e resultados de validação; inclusão de ideias para pesquisa, com rastreabilidade.
4. **Testes:** escolher estratégia, ativo, período e custos; solicitar backtest; acompanhar replay e abrir a lista completa das operações simuladas.
5. **Diário:** registrar sinais aceitos, ignorados e executados, preços reais, resultado, alterações manuais e tempo gasto na decisão.

Cada indicador deve poder ser ligado e desligado apenas na visualização. Alterar os indicadores usados pela estratégia constitui uma nova versão de pesquisa; não mudar silenciosamente o cálculo quando alguém esconde uma linha do gráfico.

### Ficha obrigatória de sinal

| Campo | Conteúdo |
|---|---|
| Identificação | Ativo/contrato, servidor/fonte, direção, estratégia e versão |
| Situação | Em observação, disponível para análise, expirado, invalidado, conflito ou dados indisponíveis |
| Entrada | Preço de referência, faixa aceitável e condição de confirmação |
| Stop | Preço de proteção proposto, distância e regra que o define |
| Saída | Alvo principal, eventual segundo alvo apenas em versão testada e condição de saída antecipada |
| Relação retorno/risco | Recalculada para o preço executável atual, com hipótese de custos explícita |
| Tamanho | Lote estimado somente com contrato, moeda e orçamento de risco informados |
| Validade | Instante de geração, prazo restante e condições que cancelam a ideia |
| Justificativa | Duas a quatro condições objetivas satisfeitas e fatos contrários relevantes |
| Evidência | Status de validação, fonte, período, amostra, expectativa líquida e maior queda |
| Condições atuais | Spread, volatilidade, eventos relevantes e estado do monitor da conta |

Até existirem experimentos, métricas aparecem como “ainda não medido”, com valor interno `null`. Não preencher tela com taxas de acerto inventadas ou chamar pontuação de confluência de probabilidade.

### Segunda análise humana

A revisão sugerida deve caber em uma ficha: conferir instrumento, atualidade do sinal, preço disponível, stop, relação retorno/risco, exposição e notícias. A revisão aumenta o controle sobre a decisão; seu efeito sobre o resultado será medido.

Registrar todos os sinais, inclusive recusados. Manter duas curvas: resultado simulado de todos os sinais elegíveis e resultado das operações humanas confirmadas. Registrar separadamente a simulação das escolhas humanas. Comparar as curvas sem apresentar a diferença como prova causal de que o usuário melhorou ou piorou a estratégia.

## 4. Conexão externa com dados

### Caminho inicial: leitura do servidor pretendido

A integração oficial Python consulta preços, barras e ticks através de um terminal MT5 ativo. Ela não elimina essa dependência de infraestrutura. A interface do laboratório será independente e não exigirá visualizar os testes no MT5. [F01]

Usar um terminal/conector separado com acesso de investidor, quando disponível, enquanto William opera em sua instalação habitual. O acesso de investidor permite análise e consulta sem negociar. Conferir o suporte do servidor às sessões simultâneas e às permissões necessárias. [F02]

O conector expõe apenas leitura; credenciais ficam no ambiente local. O motor e a interface não recebem senha de negociação. Se não houver credencial de leitura, usar feed de dados ou conta demo apropriada para pesquisa e identificar as diferenças; não solicitar a senha principal como solução automática.

### Instrumentos e equivalência

| Instrumento executado | Dado principal | Contexto opcional |
|---|---|---|
| Ouro no MT5 | Bid/ask e candles do símbolo exato do servidor | Dados de futuros de ouro, se licenciados e disponíveis |
| Nasdaq no MT5 | Contrato exato disponibilizado na conta | Futuros/índice relacionado, com identificação da diferença |
| BTC no MT5 | Feed do contrato de BTC da conta | Negócios de exchange específica |
| BTC em exchange, em pesquisa separada | Mercado spot ou derivativo explicitamente selecionado | Outros mercados apenas como comparação |

Futuros, CFDs e spot podem apresentar preços, sessões, custos e volumes diferentes. Um nível de preço de outro contrato não deve virar entrada ou stop no MT5 sem modelar e validar essa relação. Transferência de estratégia exige novo teste no instrumento de execução.

Dados históricos são limitados pelo provedor, período disponível e configuração do terminal. Auditar cobertura antes de prometer anos de ticks. [F03] APIs públicas de exchange são uma opção para BTC, com arquivos históricos e atualizações ao vivo; disponibilidade, regras de acesso e limites devem ser verificados na implementação. [F04, F05]

### Contrato de dados

Persistir fonte, servidor, símbolo, tipo de contrato, timezone de origem, timestamps UTC, instante de recebimento, bid/ask, preço negociado e quantidade quando disponíveis, candles, natureza do volume, especificações e versões dos custos.

Conferir duplicatas, lacunas, ordem temporal, mudança de especificações, feriados, horário de verão, dados desatualizados e aquecimento dos indicadores. Marcar cada barra como aberta ou encerrada. Um candle H1 só pode ser usado depois de seu encerramento, mesmo que o sinal seja M5/M15.

## 5. Indicadores: cada um precisa de uma função

POC indica o nível de maior atividade dentro do perfil escolhido. Em algumas plataformas, o perfil de forex, índices e CFDs utiliza contagem de atualizações de preço. Isso difere de quantidade negociada. O laboratório distinguirá `volume negociado`, `perfil de ticks` e `volume indisponível`. [F06]

VWAP será calculada com a ponderação documentada da fonte; se usar contagem de ticks, o nome e o relatório indicarão essa aproximação. ATR mede amplitude/volatilidade, e não direção. [F07, F08]

| Grupo | Elementos candidatos | Uso proposto |
|---|---|---|
| Contexto | Estrutura H1, médias e inclinação | Separar tendência, lateralização e cenário indefinido |
| Localização | Perfil de volume, POC, VWAP, zonas de oferta/demanda | Identificar níveis antes de buscar gatilhos |
| Confirmação | Fechamento além de nível, rejeição, reteste, rompimento de estrutura | Determinar quando a hipótese fica elegível |
| Dimensionamento | ATR, tick size, spread e custo | Avaliar stop, preço aceitável e viabilidade |
| Qualidade da informação | Fonte, atraso, cobertura e calendário | Bloquear conclusões sem dados adequados |

As funções acima são escolhas de projeto, não um ranking comprovado de indicadores. Cada filtro precisa melhorar uma versão de referência em dados separados. Evitar contar médias, MACD e outras transformações do mesmo preço como votos independentes.

### POC reproduzível

Usar inicialmente perfil da sessão anterior já concluída. Se o perfil atual for pesquisado, reconstruí-lo incrementalmente; o POC final da sessão não pode aparecer no início do dia histórico. O perfil não depende do zoom ou da área visível do gráfico.

Congelar sessão e regra de bins antes dos testes. Semente própria: largura do bin = maior entre um tick e 0,05 ATR M15, arredondada para múltiplo do tick; usar o ATR conhecido no início da sessão e uma origem de bins fixa em zero. Em empate do maior volume, escolher o bin de menor preço; POC é o centro do bin. Testar sensibilidade posteriormente como novas versões.

Com negócios e quantidades, agregar quantidade por preço. Sem esses dados, pode-se contar atualizações de midpoint por bin, com nome explícito `perfil de ticks`. OHLCV sozinho não revela exatamente quanto foi negociado em cada preço; distribuir volume de candle em bins é outra aproximação, cuja regra precisa ser registrada e validada separadamente.

Para a hipótese de área de valor deste projeto, partir do POC e incorporar o bin adjacente de maior volume até acumular pelo menos 70% do total; empate escolhe o inferior. VAH e VAL são as bordas externas dos bins incluídos. Essa é uma convenção própria e pode diferir da plataforma de referência. Dados ausentes ou sessão incompleta impedem o cálculo elegível.

### SMC, estrutura e oferta/demanda

Converter interpretações em regras mensuráveis: qual pivô, quando foi confirmado, qual fechamento rompeu, como a zona foi formada e quando ficou inválida. Um desenho de candles não comprova presença de ordens institucionais.

Convenção inicial própria: pivô exige duas barras completas de cada lado; ele fica conhecido apenas após fechar a segunda barra posterior. Empates não formam pivô. Rompimento exige fechamento além do último pivô conhecido por 0,10 ATR. Nunca retroagir o sinal à data visual do pivô.

FVG de alta candidato: no fechamento de `t`, mínima de `t` acima da máxima de `t-2`; a faixa nasce em `t`. Manter separado de zonas de oferta/demanda. Não presumir preenchimento futuro obrigatório.

## 6. Catálogo inicial de seis estratégias candidatas

Todas começam em **ESPECIFICADA / NÃO VALIDADA**. Os números abaixo são sementes de pesquisa escolhidas antes dos resultados. Não são calibração ótima nem recomendação de entrada atual.

| ID | Hipótese | Ambiente a pesquisar | Prioridade |
|---|---|---|---|
| S1 | Tendência com retração | Continuação de tendência | Primeira implementação; herdada da V2 |
| S2 | Rompimento e reteste | Saída de consolidação | Segunda, após verificar a base |
| S3 | Rejeição da área de valor em direção ao POC | Lateralização | Depende da qualidade do perfil |
| S4 | Varredura e recuperação de nível | Falso rompimento | Depois da auditoria temporal de SMC |
| S5 | Reteste de oferta/demanda após deslocamento | Retração em tendência | Depois de zonas causais |
| S6 | Rompimento e reteste da faixa de abertura | Sessão com expansão | Nasdaq como primeiro estudo específico |

Gold, Nasdaq e BTC terão resultados e configurações próprios. O fato de uma hipótese funcionar em um deles não a valida nos demais.

### Regras comuns às sementes

Começar com gatilhos M15 e contexto H1 para avaliar a compatibilidade com decisão manual. M5 é um experimento posterior. Calcular sinais apenas com barras encerradas; condições de invalidação podem ser verificadas a cada cotação.

Usar ATR14 com suavização de Wilder/RMA. EMA inicializada com a média dos primeiros N fechamentos e aquecimento suficiente; registrar o método. Não processar um sinal enquanto os indicadores necessários não estiverem prontos.

Stop candidato entre 0,8 e 3 ATR de distância da referência de entrada; buffer estrutural de 0,20 ATR. A regra de entrada válida será reavaliada após atraso humano. Expiração inicial de 60 segundos e afastamento máximo de 0,15 ATR da referência: ambos são hipóteses a testar.

Sem parcial, breakeven ou trailing na primeira versão. Janela operacional e saída por tempo precisam constar do perfil de sessão antes do backtest; faltando esse perfil, a simulação não começa. Semente de encerramento por tempo: primeira cotação negociável após o fechamento da oitava barra M15 posterior à entrada, ou término autorizado da sessão, o que vier primeiro.

### S1 — Tendência com retração

Compra: último H1 encerrado fecha acima da EMA200 e EMA50 H1 está acima de seu valor três H1 antes. Pelo menos uma das três barras M15 anteriores à barra de sinal tocou a EMA20. A barra de sinal fecha acima da EMA20 e da máxima M15 anterior. Venda simétrica.

Stop: mínima das quatro barras M15 encerradas mais recentes menos 0,20 ATR; venda simétrica. Alvo de pesquisa: 2R em relação à referência de entrada no instante do sinal. Congelar o alvo; nova cotação altera a relação retorno/risco mostrada, sem deslocar silenciosamente a saída para preservar 2R.

Variantes VWAP, POC ou estrutura adicional entram uma por vez, comparadas à semente sem o filtro. A alteração da regra de alvo em relação à V2 recebe versão própria.

### S2 — Rompimento e reteste

Caixa nas 12 barras M15 anteriores ao rompimento, excluindo a barra de rompimento. Largura entre 1 e 4 ATR; fechamento para fora por pelo menos 0,10 ATR. Congelar caixa e ATR.

Nas quatro barras M15 seguintes, procurar reteste na faixa de ±0,20 ATR ao redor da borda rompida, com fechamento de volta para o lado do rompimento. Cancelar se houver fechamento além da borda oposta. Um sinal por caixa/rompimento.

Stop além da extremidade adversa da barra de reteste por 0,20 ATR; alvo de 2R sobre a referência no sinal. Para esta versão, não antecipar o reteste com ordem limite imaginária.

### S3 — Rejeição da área de valor rumo ao POC

Contexto lateral candidato: eficiência direcional das últimas 20 barras M15 abaixo de 0,30. Definir eficiência como valor absoluto da variação entre primeiro e último fechamento dividido pela soma das variações absolutas consecutivas. Denominador zero resulta em estado indisponível.

Usar VAL, VAH e POC da sessão anterior, congelados. Compra: mínima da barra cruza abaixo de VAL e fecha novamente acima de VAL e abaixo do POC. Venda: máxima cruza VAH e fecha abaixo de VAH e acima do POC.

Stop além do extremo da barra de rejeição por 0,20 ATR. Alvo principal no POC. Exigir retorno/risco líquido projetado de pelo menos 1,5 no preço aceitável; caso contrário, nenhuma candidata. Não trocar o POC por 2R retrospectivamente.

Um sinal por borda por sessão na semente. Testar perfil negociado e perfil de ticks como versões distintas, sem misturar estatísticas. Essa regra é uma hipótese própria baseada em níveis de perfil; a documentação do indicador não valida sua rentabilidade.

### S4 — Varredura com recuperação e confirmação

Congelar máxima e mínima da sessão anterior. Compra: uma barra M15 negocia abaixo da mínima por pelo menos 0,10 ATR e fecha novamente acima dela. Nas duas barras M15 seguintes, exigir fechamento acima da máxima da barra de varredura. Venda simétrica.

Cancelar se preço ultrapassar novamente o extremo adverso da barra de varredura antes da confirmação. Stop além desse extremo por 0,20 ATR; alvo 2R sobre referência no sinal. Uma candidata por nível por sessão.

A semente evita depender de pivôs ainda não confirmados. Uma variante com pivô, BOS, CHoCH ou FVG terá convenções causais, versão e comparação próprias. O termo “varredura” descreve o padrão de preço, não identifica o agente que negociou.

### S5 — Reteste de oferta/demanda após deslocamento

Contexto de tendência igual ao de S1. Semente de demanda: três barras consecutivas com faixa total de no máximo 1 ATR conhecido antes do deslocamento; a barra seguinte tem corpo positivo de pelo menos 1 ATR e fecha acima da máxima da base por 0,10 ATR. Oferta é simétrica.

A zona corresponde à faixa total da base. Ela só existe após fechar o deslocamento. Pesquisar apenas o primeiro reteste nas oito barras seguintes: o preço toca a zona e a barra encerra além da borda proximal, na direção da continuação. Fechamento além da borda distal invalida a zona; o stop proposto também é limite de invalidação intrabar.

Stop além da borda distal por 0,20 ATR; alvo 2R. Havendo zonas sobrepostas elegíveis, usar a mais recente e registrar as outras. Não redesenhar a base após conhecer a reação.

### S6 — Faixa de abertura com reteste

Exige calendário e âncora de sessão explicitamente definidos para o contrato. Semente: faixa das duas primeiras barras M15 da sessão escolhida. Só usar a faixa depois do fechamento das duas barras.

Nas quatro barras seguintes, procurar fechamento além da faixa por 0,10 ATR. Nas duas barras seguintes ao rompimento, exigir reteste da borda com tolerância de 0,20 ATR e fechamento para fora na direção do rompimento. Cancelar ao fechar além da borda oposta.

Stop além do extremo adverso do reteste por 0,20 ATR; alvo 2R; uma candidata por sessão. VWAP entra como variante, comparada ao modelo sem VWAP. A abertura relevante deve ser configurada pela sessão do mercado de referência, com timezone e horário de verão; não fixar um horário brasileiro para todos os meses. Em BTC, uma janela escolhida é uma convenção de pesquisa, não abertura de um mercado que encerra diariamente.

## 7. Aproveitamento de estratégias e código disponíveis no mercado

Pesquisar documentação de indicadores, artigos dos autores, código público com licença compatível e regras verificáveis. Registrar URL, data, versão/commit quando houver importação, licença, mercado original, horizonte e limites da evidência. Não copiar código fechado nem tratar propaganda, estrelas de repositório ou taxa de acerto anunciada como validação.

O projeto aberto `joshyattridge/smart-money-concepts` oferece referências para FVG, pivôs e estrutura. Sua documentação usa barras anteriores e posteriores para identificar pivôs; incorporar resultados em tempo real exige respeitar o instante de confirmação. A licença consultada é MIT. Nesta entrega, o código não foi instalado nem auditado linha a linha. Usá-lo como referência, e só incorporar após fixar versão e verificar causalidade. [F09, F10]

O estudo de Moskowitz, Ooi e Pedersen documenta momentum em futuros e forwards em horizontes muito mais longos que M15. É contexto para pesquisar tendência; não valida a nossa S1 intradiária. [F11]

Uma ideia de mercado entra como CANDIDATA. A aba Estratégias mostra sua procedência e os experimentos próprios necessários. Nenhum material encontrado libera sinais automaticamente.

## 8. Testador externo com execução manual realista

Implementar um único núcleo Python para gerar features, estados e sinais. Alimentá-lo com eventos históricos em replay ou com eventos recebidos ao vivo. Trocar apenas o relógio e a origem dos eventos; preservar as mesmas regras.

O simulador de preenchimentos fica separado do núcleo de sinais. O laboratório apenas simula ordens. No modo de uso humano, não existe envio de ordens pelo sistema.

### Atraso, faixa e expiração

Registrar instantes do dado, geração, publicação, visualização, decisão e execução quando conhecida. Testar atrasos hipotéticos de 5, 15, 30, 60 e 120 segundos, depois substituí-los/complementá-los com a distribuição observada no uso real. Eles são cenários, não medições.

Para cada cenário, obter a primeira cotação executável depois do atraso e conferir validade. A expiração inicial de 60 segundos significa que o cenário de 120 segundos perde a oportunidade; não estender a validade para contar uma entrada. Uma variante com prazo maior exige outro teste.

Compra usa Ask na entrada e Bid para saída; venda faz o inverso. Reavaliar faixa aceitável, stop, alvo, relação retorno/risco, spread e estado da sessão. Se o alvo ou stop já tiver sido alcançado antes da decisão, expirar a ideia. Gaps e slippage podem produzir perdas superiores à distância nominal do stop.

Ordens limite simuladas exigem regras de execução específicas. Tocar o preço não garante preenchimento, principalmente em dados agregados. Não transformar toda oportunidade perdida em fill favorável.

### Qualidade do histórico

OHLCV serve para triagem. Se stop e alvo puderem ter ocorrido dentro da mesma barra e faltarem ticks para ordenar os eventos, marcar ambiguidade, usar o resultado adverso na triagem e reportar sensibilidade. Não assumir sequência intrabar favorável. Para validar entrada manual e custos com precisão, priorizar bid/ask e resolução suficiente.

Testar por prefixos do histórico: adicionar barras futuras não pode alterar decisões que já estavam disponíveis, nem antecipar o instante de confirmação de pivôs ou zonas. Indicadores em formação podem variar; sinais confirmados devem ser versionados e preservados.

## 9. Critérios para dizer que uma estratégia foi validada

A validação pertence ao conjunto estratégia + versão + ativo/contrato + fonte + timeframe + sessão + custos + política de decisão manual. Ela não é transferível por nome.

| Etapa | Evidência exigida |
|---|---|
| Especificada | Regras completas, fontes, custos e critérios de avanço definidos |
| Verificada no software | Fórmulas, relógio, causalidade, estados e ausência de envio de ordem testados |
| Backtestada | Histórico rastreável, fills identificados como simulados e relatório reproduzível |
| Avaliada fora da amostra | Configuração congelada antes de avaliar dados separados |
| Observada ao vivo | Sinais registrados prospectivamente, com atrasos, recusas e mudanças de preço |
| Elegível para análise humana | Evidência e limites publicados; contrato/perfil revisados quando aplicável |
| Suspensa | Dados, custos, regra ou desempenho exigem revisão |

As políticas de triagem da V2 continuam candidatas: expectativa líquida positiva; profit factor líquido ≥1,25; pelo menos 200 operações fora da amostra distribuídas por 12 meses como piso de cobertura; intervalo da expectativa estimado por reamostragem em blocos; cenário de custos +50% preservando expectativa positiva; +100% reportado como estresse. Esses números não certificam lucro e não autorizam diminuir exigências depois de ver os resultados. Evidência escassa recebe status INSUFICIENTE.

Separar desenvolvimento, validação e avaliação final em ordem temporal. Purga/intervalo de separação quando exemplos se sobrepõem. Controlar o número total de hipóteses, ativos, parâmetros e seletores tentados; registrar inclusive falhas. A escolha do melhor entre muitos backtests pode produzir falso positivo. Um teste final consultado repetidamente deixa de ser independente. [F12]

Uma janela prospectiva inicial de 20 sessões e 30 decisões/execuções manuais em treino pode verificar operação, sem forçar sinais para completar a contagem. Isso não substitui evidência econômica. Regras da conta de treino precisam ser distintas de desafio pago, mesmo quando ambos aparecem como demo no terminal.

### Medidas que entram no comparador

Acerto, ganho médio, perda média, expectativa líquida em R, profit factor, número de sinais, número de execuções simuladas/humanas, custos, maior queda de equity, pior dia, tempo exposto, sequência de perdas, concentração do lucro e resultados por sessão/regime. Incluir intervalos de incerteza e sensibilidade ao atraso.

R é a unidade de risco nominal inicial do experimento; especificar se custos foram incluídos nesse denominador e manter a convenção em todos os relatórios. Retornos em R de operações executadas manualmente usam a referência registrada no momento da execução.

Exemplo matemático, sem relação com resultados do projeto: 80% de acerto, ganho médio de 0,2R e perda média de 1R produz `0,8 × 0,2 − 0,2 × 1 = −0,04R` antes de custos. Buscar acerto sem avaliar tamanho de perdas pode selecionar uma estratégia deficitária.

Comparar cada filtro e conjunto de estratégias com a versão mais simples, no mesmo período e orçamento de risco. Um conjunto só melhora a base se trouxer benefício medido; sinais correlacionados não são diversificação automática.

## 10. Monitor de risco e diário: limites da segunda checagem

O orçamento sugerido por sinal depende de moeda, contrato e risco configurados pelo usuário. Preservar os valores da V2 como cenários de simulação, sem tratá-los como limites executados automaticamente ou transformar o limite diário de 2.999 em orçamento para perder.

Sem acesso atualizado ao estado de toda a conta, exibir “risco da conta não sincronizado”; uma informação manual é declarada pelo usuário, não confirmada pelo servidor. Se a conta estiver sincronizada em leitura, identificar posições existentes e risco agregado, sem alterá-las.

Bloqueios afetam a geração de novas oportunidades, não a capacidade de William operar manualmente no MT5. O aplicativo não fecha posições nem instala stop. Quando a pessoa executar, o stop deverá ser inserido/conferido no MT5. Alertas de saída precisam dizer qual condição ocorreu, quando e a que preço, sem afirmar que uma posição foi encerrada.

Não elevar risco por número de indicadores favoráveis, perdas recentes, pressão de prazo ou meta de assinatura. Na primeira versão, conflitos direcionais entre estratégias elegíveis resultam em “conflito/aguardar”. Candidatas na mesma direção são agrupadas; preserva-se uma prioridade fixa antes dos resultados, com risco agregado único.

## 11. Implementação progressiva e controle de consumo

1. Modelo de dados, catálogo de contratos e tela mobile com estados honestos de conexão.
2. Conector de leitura, auditoria de candles e núcleo causal da S1.
3. Testador externo, custos, replay e comparação com acompanhamento ao vivo em observação.
4. S2 e variantes pontuais; importar novas ideias para pesquisa de forma versionada.
5. Perfil de volume e S3; S4/S5 após causalidade; S6 depois do calendário de sessão.
6. Validação individual, seletor e conjunto, seguida de avaliação do processo de decisão manual.

Backtests pesados têm fila, limite de tempo e cancelamento. A rotina de coleta e de sinais tem prioridade sobre pesquisa. Manter um backtest pesado por vez na configuração inicial, limitar CPU e pausar pesquisas quando aumentarem o atraso dos dados.

IA atua na pesquisa solicitada e explicação de relatórios. Indicadores e sinais usam cálculos determinísticos locais. Não consultar modelo por ativo, tick ou atualização de tela. Guardar cache de documentos e resultados. Orçamento externo padrão zero; nenhum serviço pago é ativado nesta entrega.

## 12. Mobile e Supabase: arquitetura viável

### Formato e interface

Recomendação inicial: PWA privada, instalável pelo navegador e acessível por ícone no celular. A forma de instalação depende do sistema/navegador. Isso permite um primeiro app sem publicação em lojas. A aplicação continuará utilizável por URL quando a instalação não for suportada. [F13]

Direção visual proposta: fundo grafite, texto claro, detalhes discretos em dourado para o produto, verde/vermelho acompanhados de palavras e ícones para direção. Abas inferiores Mercado, Robô, Estratégias, Testes e Diário. Preços grandes, campos de stop/alvo legíveis, botões com área de toque de pelo menos 44 px e detalhes expandidos sob demanda.

XAUUSD e Nasdaq 100 ficam fixos no início de Mercado. A versão inicial acompanha mais cinco: BTCUSD, ETHUSD, SOLUSD, EURUSD e USDJPY. A lista anterior de vinte fica como catálogo de expansão, sem coleta ou processamento automático. Mostrar último preço e sua natureza (bid, ask, last ou midpoint), variação com referência temporal explícita, hora do dado e estado do mercado. Para CFDs, permitir ver bid/ask e spread. Não gerar preço com animação fictícia.

No ativo aberto, exibir gráfico, até três sobreposições escolhidas, painel compacto dos indicadores e ficha de oportunidade. Os dez indicadores ficam disponíveis, mas não precisam ser desenhados todos simultaneamente.

### Responsabilidades técnicas

| Componente | Responsabilidade | Local proposto para o piloto econômico |
|---|---|---|
| PWA | Interface, gráficos, filtros e diário | Hospedagem estática gratuita elegível, como Cloudflare Pages |
| Supabase Auth | Login do usuário | Supabase Free |
| Supabase Postgres | Catálogo, estratégias, sinais, decisões e resumos | Supabase Free |
| Supabase Realtime | Atualizações compactadas da tela e novos eventos | Supabase Free dentro da franquia |
| Processo Python | Coleta, indicadores, sinais e fila de backtests | PC existente do usuário |
| Histórico extenso/ticks | Pesquisa, reprodutibilidade e reexecução | Arquivos locais com backup disponível |
| Fonte de cotações | Feed autorizado do instrumento | Conector MT5 de leitura ou API elegível |

Supabase atende autenticação, persistência e distribuição de eventos. Suas Edge Functions têm limites de duração, CPU e memória; não são o local proposto para um terminal Windows ou um processo Python contínuo de backtests. A documentação consultada informa 150 segundos de duração no Free, 2 segundos de CPU por requisição e 256 MB de memória. [F14]

O motor no PC pode atender o celular pela nuvem com conexões de saída autenticadas, sem abrir uma porta pública no roteador. PWA aberta não significa motor ativo: mostrar heartbeat e parar de apresentar novas oportunidades quando o processo de dados parar.

Uma operação integralmente em nuvem precisará de um processo de execução compatível com o feed. Se mantiver o conector MT5, precisará de ambiente capaz de manter o terminal ativo. Se adotar API direta, poderá usar outro ambiente, mas precisará verificar cobertura, permissão, histórico e custo. Portanto, **não há promessa de funcionamento integral em nuvem 24 horas por dia a custo zero**.

### Atualização e bateria

- Feed e motor: coletar conforme a fonte suportar; validar sessão e atraso.
- Tela visível: publicar lote de cotações e indicadores provisórios do ativo aberto a cada 5 segundos na semente econômica. Trata-se de atualização periódica sobre feed ao vivo, com latência adicional de até 5 segundos mais rede, não de exibição de cada tick.
- Resumo dos dez indicadores dos sete ativos: atualizar no máximo a cada 60 segundos, com timestamp. Recalcular/confirmar sinais nos fechamentos definidos pela estratégia.
- Indicadores da barra atual devem dizer “em formação”; os usados no sinal confirmado devem apontar a barra fechada. Cor do indicador não equivale a autorização de entrada.
- Quando o app ficar oculto, suspender o envio contínuo ao celular e usar um prazo curto de sessão ativa no servidor. O motor pode continuar observando se a máquina estiver ligada.
- Notificações push são uma extensão a verificar no aparelho e sistema. Não são mecanismo de stop e podem atrasar. Ao abrir um aviso, buscar o estado atual do sinal antes de mostrá-lo como vigente.
- Offline: somente consulta ao último conteúdo, com marcação evidente; nenhuma cotação ou indicação armazenada permanece com rótulo “ao vivo”.

### Dados e acesso

Aplicação privada para William inicialmente. Habilitar políticas por usuário nas tabelas e canais privados. Chaves privilegiadas e credenciais de corretora jamais entram no frontend; o processo de coleta recebe permissão restrita. Supabase documenta políticas de segurança por linha para restringir acesso aos registros. [F15]

Estrutura mínima: `instruments`, `strategy_versions`, `experiments`, `signals`, `signal_events`, `manual_decisions`, `quotes_latest`, `indicator_snapshots`, `candles_recent`, `backtest_jobs` e `worker_status`. Separar `user_id`, instrumentos e escopo de dados. Guardar status, versões e timestamps, não apenas a última frase do robô.

Enviar um lote dos sete ativos por atualização em canal privado. Persistir o último snapshot periodicamente, sem guardar um registro histórico a cada atualização de tela. Eventos importantes e decisões têm registro durável; na reconexão, recuperar o estado pelo banco e deduplicar por ID/versão.

Pedidos de backtest feitos pelo celular selecionam estratégias e parâmetros permitidos. O processo Python busca a fila, executa e devolve relatório. Se o PC estiver desligado, o trabalho fica “aguardando processamento”; não simular progresso.

## 13. Cálculo de custo e capacidade

Consulta das condições públicas: 15/09/2026. Valores de provedores em USD. Sem conversão cambial inventada. Os números de uso abaixo são estimativas de engenharia; precisam ser confrontados com a medição do piloto.

### Franquias relevantes

Supabase Free: banco de 500 MB, armazenamento de arquivos de 1 GB, 5 GB de saída não cacheada, 2 milhões de mensagens Realtime/mês e 500 mil invocações de Edge Functions. Projetos gratuitos podem ser pausados por inatividade. Pro começa em US$25/mês; não é ativado neste plano. [F16]

Cloudflare Pages possui opção gratuita para a interface estática; funções e outras capacidades têm seus próprios limites. Usar o subdomínio fornecido inicialmente e não contratar domínio ou serviços adicionais. [F17]

### Premissas do piloto pessoal

- Um usuário e um celular recebendo o canal; 4 horas de tela ativa por dia, 22 dias/mês.
- Sete ativos em um único pacote a cada 5 segundos; pacote de cotações e ativo aberto estimado em até 2 KiB.
- Resumo adicional de indicadores a cada 60 segundos, estimado em até 4 KiB.
- Dez eventos de sinal por dia apenas para dimensionamento de tráfego, não meta de entradas.
- Um carregamento diário de 400 candles por ativo, com 96 bytes/candle estimados no transporte compacto.
- Cada Broadcast é contado como um envio mais um recebimento por cliente; para um celular, duas mensagens por publicação. [F18]

| Consumo | Fórmula | Estimativa mensal |
|---|---|---:|
| Lotes de cotações | 4 × 3.600 × 22 ÷ 5 | 63.360 |
| Lotes de indicadores | 4 × 60 × 22 | 5.280 |
| Eventos de sinais | 10 × 22 | 220 |
| Mensagens Realtime | (63.360 + 5.280 + 220) × 2 | 137.720 |
| Mensagens com reserva de 20% | 137.720 × 1,20 | 165.264 |
| Payload de cotações | 63.360 × 2.048 bytes | 0,130 GB |
| Payload de indicadores | 5.280 × 4.096 bytes | 0,022 GB |
| Carregamento de candles | 7 ativos × 400 × 96 bytes × 22 dias | 0,006 GB |
| Transporte com margem de 2,5 vezes | Soma dos três payloads × 2,5 | Cerca de 0,40 GB |

Margem de transporte é provisão para serialização, reconexões, consultas e outros dados leves. Não é tamanho medido e não inclui downloads frequentes de históricos extensos. O provedor contabiliza saída de vários serviços, além do Realtime; monitorar o total da organização. [F19]

Para banco recente: 7 ativos × 96 candles M15/dia × 14 dias = 9.408 registros. Supondo 400 bytes por registro com índice, cerca de 3,8 MB. É um limite superior simples de candles 24h/dia; alguns mercados encerram. Manter orçamento inicial de até 100 MB para o banco inteiro e medir o tamanho real, inclusive índices e crescimento de logs. Histórico de vários anos e ticks ficam fora do Postgres gratuito.

Reduzir de 22 para sete ativos diminui a contagem de candles em aproximadamente 68%. Como o envio já era agrupado, a quantidade de mensagens por atualização permanece a mesma; o que diminui é o tamanho do pacote, o histórico e o trabalho de cálculo. Os valores de uso não incluem assinar feed de volume de bolsa.

### Mensalidade estimada por componente

| Item | Piloto proposto | Condição |
|---|---:|---|
| Interface estática | US$0 | Plano gratuito elegível, dentro dos limites |
| Supabase | US$0 | Uso pessoal modelado e controle de franquias |
| IA para atualizar indicadores/sinais | US$0 | Nenhuma chamada de IA na rotina |
| Servidor de processamento | US$0 de aluguel | Usar PC já existente e ligado durante a observação |
| Dados da corretora | Custo adicional a confirmar | Pode ser zero se o feed atual permitir esse uso; não presumir cobertura/licença |
| Eletricidade, internet e backup | Dependem do ambiente | Não equivalem a custo total zero |
| Total de novas assinaturas | **US$0 no cenário condicional** | Depende de feed elegível sem cobrança e recursos existentes |

Exemplo de energia, inteiramente hipotético: equipamento consumindo 80 W por 88 horas/mês usa 7,04 kWh. Com tarifa suposta de R$1/kWh, R$7,04. Ligado 720 horas/mês, 57,6 kWh ou R$57,60 nessa mesma tarifa. Potência, tarifa e consumo incremental reais precisam ser medidos; não são uma cotação da conta de energia de William.

Não concluir que o Pro do Supabase por si só resolve processamento e feed. Um cenário integralmente em nuvem tem total `hospedagem + banco + processo contínuo + dados + armazenamento/transferência + IA opcional`; processamento e dados ainda não podem ser cotados de forma definitiva sem escolher provedor/conta elegível. Não houve contratação ou criação de infraestrutura nesta entrega.

### Onde o gratuito deixa de caber

Um lote por segundo, 24h por dia, durante 30 dias, para um único celular: 30 × 86.400 × 2 = **5.184.000 mensagens**, acima da franquia Free. Se cada ativo for uma mensagem separada, o consumo cresce ainda mais. Multiplos celulares ou abas conectadas também aumentam recebimentos.

A Twelve Data anuncia Basic com 8 créditos API/minuto, 800/dia e WebSocket de teste. Sua página distingue usos e direitos de exibição; não foi confirmada elegibilidade desse plano para exibir todos os nossos instrumentos no aplicativo. Como cenário de endpoint custando um crédito por símbolo, sete ativos uma vez por minuto por quatro horas exigem 1.680 créditos/dia; a cada cinco segundos, 20.160. Portanto, essa cota REST gratuita não sustenta esse desenho de atualização mesmo com sete ativos. [F20]

OANDA v20 é uma alternativa técnica a pesquisar para feed direto: anuncia histórico e preços via API, mas a disponibilidade depende da divisão e conta, e algumas divisões não oferecem v20. Não foi verificada a elegibilidade de William nem a cobertura dos sete ativos. Não usar como promessa de solução gratuita pronta. [F21]

### Controles de gasto obrigatórios

Alertas internos aos 50%, 70% e 85% da franquia; aos 85%, reduzir frequência de tela, suspender downloads grandes e pesquisas, mantendo estado correto de atualidade. Não reduzir silenciosamente a frequência dos sinais sem validar outra versão. Dados atrasados passam a ser indisponíveis para sinal.

Sem clientes ativos, interromper broadcasts contínuos de preços. Guardar só dados necessários na nuvem, limpar retenção após preservar evidência, controlar reconexão com recuo progressivo e limitar jobs. Uma única coleta abastece todos os indicadores, sem dez chamadas de API por ativo. Não habilitar upgrades ou complementos automaticamente.

## 14. Dez indicadores/ferramentas prioritários para o aplicativo

Esta é uma seleção de engenharia para pesquisar XAUUSD e Nasdaq 100; não é um ranking de rentabilidade comprovada. SMC e oferta/demanda são conjuntos de regras de estrutura, incluídos como ferramentas do painel. Parâmetros abaixo são sementes, não calibrações validadas.

| Nº | Indicador/ferramenta | Semente | Informação no celular |
|---|---|---|---|
| 1 | Volume Profile: POC, VAH e VAL | Sessão anterior; área 70% | Níveis, distância atual e natureza do volume |
| 2 | VWAP | Sessão definida | Preço médio ponderado e distância do preço |
| 3 | ATR | 14, Wilder/RMA | Amplitude, distância do stop em ATR e mudança de volatilidade |
| 4 | Médias exponenciais | EMA20 no M15; EMA50/200 no H1 | Alinhamento, inclinação e contexto |
| 5 | ADX/DMI | 14, variante de Wilder identificada | Intensidade direcional e +DI/−DI |
| 6 | RSI | 14 | Momentum e posição relativa; extremos não viram ordens isoladas |
| 7 | Bandas de Bollinger | 20 períodos, 2 desvios | Largura e localização do preço dentro/fora das bandas |
| 8 | Canal de Donchian | 20 barras encerradas anteriores | Máximas/mínimas e tentativa de rompimento |
| 9 | Volume relativo | Comparação com mesmo horário em 20 sessões anteriores | Participação acima/abaixo do padrão, com fonte e amostra |
| 10 | Estrutura causal: SMC e oferta/demanda | Convenções das seções 5–6 | Pivôs confirmados, rompimentos, FVG e zonas com validade |

Documentação técnica para VWAP/ATR/perfil: [F06–F08]. Referências para médias, ADX, RSI, Bollinger e Donchian: [F22–F26]. Volume relativo terá implementação própria: volume da barra dividido pela média do mesmo intervalo de sessão nas 20 sessões anteriores, excluindo a sessão atual. Em barra em formação, comparar fração de tempo equivalente apenas se houver histórico intrabar; caso contrário, esperar o fechamento. Não comparar uma barra de um minuto com o volume completo de quinze minutos.

No XAUUSD de CFD, ferramentas baseadas em quantidade negociada podem ficar indisponíveis ou explicitamente usar proxy de ticks. No Nasdaq 100, separar o índice de referência do contrato negociado. Nunca mostrar volume agregado de bolsa se a fonte não fornecer esse dado.

Prioridade inicial para sinais: médias/estrutura, ATR, spread e sessão. Perfil/VWAP entram conforme a fonte; demais filtros entram por comparação. Ter dez indicadores disponíveis não implica exigir dez confirmações em toda entrada.

## 15. Sete ativos na primeira versão e catálogo opcional de expansão

Após a solicitação de reduzir o escopo e a inclusão expressa de Solana, a versão inicial fica com **XAUUSD, Nasdaq 100, BTCUSD, ETHUSD, SOLUSD, EURUSD e USDJPY**. As dez ferramentas permanecem no catálogo. Primeiro validar ouro, depois Nasdaq, e liberar os demais individualmente. Cotações disponíveis não significam estratégia validada.

Solana terá seu próprio histórico, custos, especificação e resultados. Se o dado disponível for SOLUSDT em exchange e a operação pretendida for SOLUSD no MT5, registrar os dois mercados e validar a transferência, sem substituir silenciosamente o contrato ou equiparar dólar e USDT.

A lista anterior de vinte foi preservada abaixo apenas como referência de expansão. Ela não cria assinaturas de dados, jobs ou registros contínuos para vinte ativos. Não foram buscadas cotações atuais nesta entrega.

Principais: **XAUUSD (ouro/dólar)** e **Nasdaq 100**, com código do contrato confirmado no servidor (por exemplo, NAS100 ou US100, sem presumir equivalência automática).

| Nº adicional | Ativo/referência | Categoria | Identificação para o app |
|---|---|---|---|
| 1 | EUR/USD | Câmbio | EURUSD |
| 2 | GBP/USD | Câmbio | GBPUSD |
| 3 | USD/JPY | Câmbio | USDJPY |
| 4 | AUD/USD | Câmbio | AUDUSD |
| 5 | USD/CAD | Câmbio | USDCAD |
| 6 | USD/CHF | Câmbio | USDCHF |
| 7 | NZD/USD | Câmbio | NZDUSD |
| 8 | EUR/JPY | Câmbio | EURJPY |
| 9 | S&P 500 | Índice/contrato relacionado | Referência US500, sujeito ao servidor |
| 10 | Dow Jones Industrial Average | Índice/contrato relacionado | Referência US30, sujeito ao servidor |
| 11 | DAX | Índice/contrato relacionado | Referência GER40, sujeito ao servidor |
| 12 | FTSE 100 | Índice/contrato relacionado | Referência UK100, sujeito ao servidor |
| 13 | Prata/dólar | Metal | XAGUSD |
| 14 | Petróleo WTI | Energia | Símbolo e vencimento a mapear |
| 15 | Petróleo Brent | Energia | Símbolo e vencimento a mapear |
| 16 | Bitcoin/dólar | Cripto | BTCUSD; distinguir spot/CFD/derivativo |
| 17 | Ether/dólar | Cripto | ETHUSD; distinguir spot/CFD/derivativo |
| 18 | Solana/dólar | Cripto | SOLUSD; disponibilidade a confirmar |
| 19 | XRP/dólar | Cripto | XRPUSD; disponibilidade a confirmar |
| 20 | Litecoin/dólar | Cripto | LTCUSD; disponibilidade a confirmar |

Essa é uma lista candidata para monitoramento, não uma recomendação de abrir posições. Ela não pressupõe que uma única corretora ou API ofereça todos. A descoberta deve consultar o catálogo real da conta e registrar código, contrato, lote, moeda, sessão, custos e fonte. Um ativo indisponível aparece com esse estado, sem trocar silenciosamente por outro.

Somente os sete ativos escolhidos são carregados no início. A aba Robô só libera uma versão para análise quando houver evidência específica naquele ativo. Separar pesquisa de FX, índices, metais/energia e cripto; medir correlação e quedas simultâneas antes de sugerir mais de uma exposição.

## 16. Fontes e limites da pesquisa

Fontes consultadas em 15/09/2026, salvo o plano próprio V2 de 08/09/2026. Elas sustentam mecanismos, definições e limites publicados; não demonstram rentabilidade das seis estratégias candidatas nem confirmam elegibilidade em uma corretora.

- **F01 — [MetaQuotes: integração Python](https://www.mql5.com/en/docs/python_metatrader5).** Comunicação com terminal, preços, barras e ticks.
- **F02 — [MetaQuotes: acesso à conta](https://www.metatrader5.com/en/terminal/help/startworking/authorization).** Diferença entre acesso principal e investidor.
- **F03 — [MetaQuotes: histórico de barras](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py).** Cobertura disponível e timestamps.
- **F04 — [Binance: fluxos de mercado spot](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams).** Canal de dados, sem recomendação de corretora.
- **F05 — [Binance: arquivos históricos públicos](https://github.com/binance/binance-public-data).** Fonte possível para pesquisa de cripto.
- **F06 — [TradingView: conceitos de Volume Profile](https://www.tradingview.com/support/solutions/43000502040-volume-profile-indicators-basic-concepts/).** Definições e natureza do volume. Os bins e regras das nossas estratégias são propostas próprias.
- **F07 — [TradingView: VWAP](https://www.tradingview.com/support/solutions/43000502018-volume-weighted-average-price-vwap/).** Definição do indicador.
- **F08 — [TradingView: ATR](https://www.tradingview.com/support/solutions/43000501823-average-true-range-atr/).** Amplitude e volatilidade.
- **F09 — [Smart Money Concepts: repositório](https://github.com/joshyattridge/smart-money-concepts).** Referência de implementação; confirmação temporal requer auditoria.
- **F10 — [Smart Money Concepts: licença](https://github.com/joshyattridge/smart-money-concepts/blob/master/LICENSE).** Verificada nesta pesquisa; fixar versão e preservar atribuições antes de incorporar código.
- **F11 — [Moskowitz, Ooi e Pedersen: Time Series Momentum](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum).** Evidência em outro horizonte; não valida sinais M15.
- **F12 — [Bailey e coautores: The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).** Risco da seleção entre muitos experimentos.
- **F13 — [MDN: instalação de PWAs](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable).** Requisitos e variação entre plataformas.
- **F14 — [Supabase: limites das Edge Functions](https://supabase.com/docs/guides/functions/limits).** Duração, memória e CPU.
- **F15 — [Supabase: segurança por linha](https://supabase.com/docs/guides/database/postgres/row-level-security).** Restrição de acesso aos dados.
- **F16 — [Supabase: preços e franquias](https://supabase.com/pricing).** Valores sujeitos a revisão antes de provisionar.
- **F17 — [Cloudflare Pages](https://www.cloudflare.com/products/pages/) e [limites](https://developers.cloudflare.com/pages/platform/limits/).** Alternativa para interface estática.
- **F18 — [Supabase: contabilização de Realtime](https://supabase.com/docs/guides/platform/manage-your-usage/realtime-messages).** Envio e recebimento de Broadcast.
- **F19 — [Supabase: tráfego de saída](https://supabase.com/docs/guides/platform/manage-your-usage/egress).** Medição entre serviços.
- **F20 — [Twelve Data: preços e créditos](https://twelvedata.com/pricing).** Cota REST e necessidade de verificar direitos de uso/exibição.
- **F21 — [OANDA: introdução à v20](https://developer.oanda.com/rest-live-v20/introduction/).** Alternativa dependente da divisão/conta.
- **F22 — [MetaQuotes: médias móveis](https://www.metatrader5.com/en/terminal/help/indicators/trend_indicators/ma).** Referência de indicador.
- **F23 — [MetaQuotes: ADX/DMI](https://www.metatrader5.com/en/terminal/help/indicators/trend_indicators/admi).** Identificar a variante exata na implementação.
- **F24 — [TradingView: RSI](https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/).** Referência de momentum.
- **F25 — [MetaQuotes: Bollinger](https://www.metatrader5.com/en/terminal/help/indicators/trend_indicators/bb).** Referência de bandas.
- **F26 — [TradingView: Donchian](https://www.tradingview.com/support/solutions/43000502253-donchian-channels-dc/).** Referência de canal.

## 17. Entrega e pendências concretas

Entregue nesta revisão: arquitetura mobile com execução humana, sete ativos ativos, catálogo de dez ferramentas, seis estratégias especificadas, protocolo de validação, orçamento condicional e fontes.

Ainda não realizado: implementação do aplicativo, conexão de contas, provisionamento do Supabase, importação de histórico e testes de mercado. Métricas de rentabilidade continuam não medidas.

Próxima tarefa de implementação: identificar ambiente e feed permitido para XAUUSD/Nasdaq, montar uma fatia mobile de Mercado e Robô com leitura real ou estado explícito de desconexão, e verificar o núcleo de uma estratégia antes de ampliar o repertório. O projeto não inclui autorização para ordens automáticas.
