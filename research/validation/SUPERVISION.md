# Pesquisa supervisionada e limitada

Meta vigente: sete famílias distintas aprovadas; **0/7**. N16–N20 são cinco novas hipóteses, não cinco aprovações. Nenhuma mudança de indicador, nome, ativo ou timeframe autoriza duplicar uma família. Ineditismo econômico precisa de revisão humana/agente: hash sozinho não prova originalidade.

O chat principal é o orquestrador. Subagente pesquisador e subagente revisor usam `gpt-6-luna` com esforço baixo/médio quando disponível. No máximo dois agentes por rodada, sem subdelegação; até duas hipóteses/tentativas diárias e um cálculo por vez. Cada tarefa tem escopo, prazo de três minutos e resposta curta. Trabalho repetitivo roda em Python sem chamadas a modelos. Não existe API paga de IA ou serviço instalado executando loops.

## Paradas

- Consultar cota real antes de iniciar. Com 35% semanal consumido ou leitura indisponível/desatualizada, não iniciar pesquisa. Ao observar aumento de dois pontos percentuais em uma rodada, interromper novas tarefas naquele dia. A cota é compartilhada; não é medição de custo exclusivo deste projeto nem uma trava exata de tokens.
- Uma tentativa de desenvolvimento por entradas congeladas. Dados/custos ausentes, falha financeira ou integridade inválida encerram a tentativa; não buscar janela posterior ou novos parâmetros para resgatá-la.
- Sem dados novos, não criar agentes nem rodar backtests. Após três verificações sem mudança, pausar a recorrência. A recorrência também precisa de revisão depois de sete verificações, mesmo sem atingir a meta.
- `research/cache/validation/STOP` impede novas rodadas locais. Locks e tentativas ativas exigem inspeção antes de recuperar; não remover lock vivo ou matar processo com PID reaproveitado.
- Prazos de subprocessos precisam de `subprocess.run(..., timeout=180)` em comandos Python previamente revisados, sem shell e com apenas um processo de cálculo. Interromper os subagentes que excederem o prazo. O controlador registra prazo vencido, mas não mata processos nem impõe sozinho limites de CPU/RAM.

## Controle auditável

`python scripts/research_controller.py status` consulta o registro. `preflight`, `round`, `begin` e `finish` persistem somente metadados no cache, com gravação atômica e lock exclusivo. Uma tentativa só começa se a candidata estiver explicitamente revisada como `ready_for_development` e existirem arquivos de regra, dados, custos e engine dentro do projeto; quatro hashes preservam o congelamento. A CLI não altera essa prontidão.

`finish` aceita somente bloqueada, reprovada ou candidata. Nunca aprova automaticamente. Sete aprovações só poderão ser contadas com relatórios financeiros, evidência estatística independente, paridade de execução e ao menos 60 dias/100 operações prospectivas revisadas. A ausência desses arquivos não é um erro a contornar.

## Primeira rodada

Pesquisador: nenhuma hipótese adicional distinta e executável com os dados locais foi identificada, conforme `round-1.md`. Revisor: controle de concorrência e cota implementado; a integração substituiu a sondagem de PID por sinais por bloqueio conservador seguro no Windows. Nenhum estudo financeiro foi repetido. Estado: **aguardando dados auditáveis**, não pesquisando continuamente.
