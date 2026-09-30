# Meta mínima: sete estratégias distintas

Pedido de 29/09/2026. **0/7 validadas.** Cinco hipóteses novas não equivalem a cinco aprovações. O pedido mais recente restaura sete aprovações; o novo `protocol.json` atualiza a identificação e a governança da meta; mantém integralmente custos, drawdown, amostra, independência e observação prospectiva. O protocolo antigo permanece byte a byte para preservar seus hashes e auditorias.

N16–N22 estão em `candidates.json`: liquidações confirmadas, demanda de ETF spot, depósitos em exchanges, diferença executável entre praças, surpresa de inflação, recuperação da liquidez passiva e aperto de crédito DeFi. Sete hipóteses não são sete aprovações. Cada mecanismo conta uma vez. Cruzamentos de indicadores são filtros, não famílias adicionais.

A pesquisa diária permanece agendada até sete aprovações comprovadas; ausência de dados muda a frente da próxima rodada. Não há encerramento por três evidências iguais ou sete rodadas totais. Cota, STOP, concorrência e prazos continuam limitando cada rodada; ver `SUPERVISION.md`.

O módulo `scripts/goal_five_signals.py` verifica features fornecidas e produz somente intenções de pesquisa. Seus testes sintéticos verificam o código, não lucro. Agregadores point-in-time, conectores, execução completa de N16–N20 e dados suficientes ainda precisam ser construídos/auditados antes de qualquer backtest. Nenhum serviço pago foi habilitado.

Para conferir uma condição offline: `npm run research:five:check -- --candidate N17 --input caminho/features.json`; o comando aceita N16–N22. Regras N21/N22 ficam em `scripts/continuous_signals.py`, com banda absoluta fixa, metadados causais, blocos sincronizados e ATR anterior. Testes: `python tests/continuous-signals.py`. Flags de integridade e horários fornecidos dependem de auditoria externa; condições não são fills/PnL.

`node scripts/capture-depth-pilot.mjs` captura apenas um piloto público BTCUSDT L2 (até 25 segundos, menos de 2 MB), verifica sequência e grava JSON bruto/hash no cache. Lock exclusivo e STOP impedem duplicação. Não constrói variáveis, não oferece cobertura contínua nem envia ordens. Captura prolongada, retenção limitada e executor devem ser revisados antes da avaliação prospectiva.

## Fluxo e consumo

1. Arquivar dados brutos com publicação/recebimento, revisões, instrumento e contrato executável; auditar a disponibilidade de cada feature no instante da decisão.
2. Congelar hashes dos dados, regras, cálculo de features, custos e executor. Guardar todas as tentativas.
3. Contar amostra de desenvolvimento. Menos de 100 operações: inconclusivo. Custos ausentes: bloqueado. Resultado financeiro reprovado: parar, sem abrir janelas posteriores para resgate.
4. Só candidatas elegíveis seguem para avaliação independente e prospectiva: mínimo de 60 dias **e** 100 operações encerradas, controle estatístico, paridade com sinais e revisão independente.

Use scripts locais sem IA para cálculo. Uma rodada por protocolo congelado, sem busca combinatória, reinícios automáticos, coletores duplicados ou repetição das nove reprovações. `npm run research:status` atualiza apenas o painel a partir dos relatórios locais; não coleta dados, não chama modelos e não faz backtest.

## Estado encerrado da fila anterior

N13 terminou em 29/09/2026 às 02:50:21 de São Paulo. Cobertura coletada, auditorias de identidade e metadados concluídas; nenhuma certificação de disponibilidade histórica. Base: 570 operações, −8,68%, PF 0,809, DD 12,36%. Stress: 443, −9,89%, PF 0,713, DD 11,39%, violação da conta. Reprovada, sem avaliar janelas posteriores. N2, N5, N6, N7, N11, N12, N14 e N15 também reprovaram. N8/N10: amostra insuficiente. N9: custos históricos ausentes.

O coletor de observações deixou estado `running=true`, mas seu PID não existia na conferência de 29/09. Não foi reiniciado. A fila N13 está encerrada, não aguardando novos dados.

## Aplicativo

Web na raiz, mobile WebView em `mobile/`, três temas originais. Versão web instalável na tela inicial do celular; depende de internet. Exportação Expo gera bundles, não APK/IPA. Assinatura Apple e teste em iPhone físico continuam pendentes. Login, sincronização, push e cobrança não são serviços ativos.
