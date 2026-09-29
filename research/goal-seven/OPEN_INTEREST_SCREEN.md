# N11 — contração de posições abertas e queda de preço

**Reprovada no desenvolvimento. Contagem da meta: 0/7.** A regra e os arquivos foram congelados antes de contar sinais ou calcular resultados; os hashes estão em [open-interest-freeze.json](open-interest-freeze.json). Esta família não será renomeada por trocar ativo, direção ou parâmetro.

A hipótese compra BTC, ETH ou SOL perpétuo quando a quantidade de posições abertas cai pelo menos 0,5% e o preço cai pelo menos 0,5% na mesma hora concluída. A decisão ocorre 55 minutos depois do término das variáveis; a entrada é na abertura da hora seguinte, sem usar seu retorno para decidir. Precedência fixa BTC/ETH/SOL, uma posição, stop de 1,5%, duração máxima de quatro horas, risco inicial de 0,25% do saldo e exposição máxima de 100%. Regras completas em [open-interest-protocol.json](open-interest-protocol.json).

## Resultado líquido

Janela registrada: 01/01/2022 a 01/01/2025, término exclusivo. Houve 3.069 horas com condição de entrada, antes de sobreposição, execução e interrupção por violação do limite da conta; não são 3.069 operações. O motor bloqueia novas entradas após a violação e preserva os dias inativos.

| Métrica | Base | Stress |
|---|---:|---:|
| Operações encerradas | 180 | 157 |
| Retorno líquido | −9,9465% | −10,1638% |
| Resultado sobre US$100.000 | −US$9.946,47 | −US$10.163,81 |
| Fator de lucro | 0,5780 | 0,4994 |
| Drawdown conservador máximo | 10,1809% | 10,3140% |
| Maior perda diária conservadora | 1,6583% | 1,6613% |
| Violação do limite da conta simulada | Sim | Sim |

As últimas saídas ocorreram em 07/03/2022 às 02h UTC no cenário base e 23/02/2022 às 22h UTC no stress; o restante da janela ficou sem novas entradas após o bloqueio. O retorno apresentado inclui essa interrupção, não uma estratégia operando continuamente até dezembro de 2024.

Inclui comissão e slippage por execução (base: 5 + 2 pontos-base; stress: 10 + 5), funding efetivo e tratamento conservador da elegibilidade ao funding nas horas de entrada/saída. Essa política foi corrigida antes do teste N11 e está registrada em [EXECUTION_V2.md](EXECUTION_V2.md); fontes e resultados anteriores permanecem preservados.

Os dois cenários perderam dinheiro, excederam o limite de drawdown e violaram o limite da conta. A hipótese não avançou às janelas de 2025 e 2026. Resultados legíveis por máquina em [open-interest-results.json](open-interest-results.json), com caminhos e hashes dos registros completos de operações.

## Dados e limites

Foram conferidos 3.291 ZIPs oficiais com checksums, incluindo o dia de aquecimento. A normalização excluiu observações inválidas, duplicatas e dois timestamps de SOL fora da grade, sem arredondamento ou interpolação. Mesmo assim, faltam 51, 27 e 29 observações horárias necessárias em BTC, ETH e SOL, respectivamente. Essa incompletude já impede aprovação, independentemente do PnL. O contador de falhas de barras em posições abertas é uma verificação diferente: ser zero não elimina essas lacunas de entrada.

A [auditoria do relógio](OPEN_INTEREST_CLOCK.md) encontrou 33 correspondências exatas entre arquivo e API após interpretar o timestamp do arquivo como início de intervalo e somar cinco minutos. A permanência histórica desse alinhamento e a disponibilidade das observações no momento da decisão são hipóteses, sem vintages ou recibos históricos. O teste é exploratório; nenhuma observação retrospectiva conta como validação independente. Dados Binance tampouco comprovam as condições executáveis do contrato da The5ers.

O gerador em modo prospectivo exige recibos dentro do prazo. O [coletor público](OBSERVATIONS.md) está separado da estratégia: registrar observações não inicia automaticamente um teste prospectivo nem aprova esta hipótese rejeitada.

## Revisão independente

A auditoria conferiu os 16 hashes do congelamento, a cadeia de hashes de amostra/resultados/detalhes e a reconciliação do PnL das 180/157 operações. Encontrou uma ressalva no executor v2: ele pode pular uma entrada caso não exista a barra mark H1 da própria hora de entrada. A ausência do arquivo consolidado não comprova o que era observável naquela abertura; essa condição pode selecionar entradas retrospectivamente. O registro permanece reprovado e imutável, sem promover seus números a desempenho validado. Uma versão nova do executor tratará a lacuna explicitamente, antes de outros estudos; não se usará a correção para resgatar esta família com novas escolhas de parâmetros.
