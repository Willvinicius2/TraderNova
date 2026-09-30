# Pesquisa supervisionada e limitada

Meta vigente: sete famílias distintas aprovadas; **0/7**. N16–N22 são sete hipóteses em estudo, não sete aprovações. Nenhuma mudança de indicador, nome, ativo ou timeframe autoriza duplicar uma família. Ineditismo econômico precisa de revisão humana/agente: hash sozinho não prova originalidade. A pesquisa permanece ativa até completar a meta ou haver bloqueio de segurança; histórico longo ou evidência repetida, por si só, não a encerra.

## Continuidade automática

Enquanto o PC estiver ligado e o Codex aberto, o supervisor encadeia a próxima rodada assim que a anterior termina, no mesmo turno. O heartbeat a cada cinco minutos recupera a continuidade entre turnos, sem esperar outro dia. Cada lote consulta a cota e obedece aos limites abaixo. Rodadas repetidas são permitidas no mesmo dia; o hash da evidência impede registrar duas vezes a mesma captura. Capturas novas não tornam uma estratégia ou mecanismo diferente. Quando os estudos forem insuficientes, a próxima tarefa muda de frente auditável e registra o que falta. PC ligado sozinho não mantém modelos ativos: Codex também precisa permanecer aberto.

O chat principal é o orquestrador. Subagente pesquisador e subagente revisor usam `gpt-6-luna` com esforço baixo/médio quando disponível. No máximo dois agentes por rodada, sem subdelegação; o limite de duas tentativas é por lote supervisionado, não uma trava diária global. Um cálculo por vez. Cada tarefa tem prazo de três minutos e resposta curta. Trabalho repetitivo usa scripts locais sem chamadas a modelos. Nenhuma API paga de IA foi ativada.

O coletor `scripts/continuous-depth-worker.mjs` mantém a conexão pública L2 e grava blocos gzip consecutivos sem chamadas a modelos. Lock exclusivo e estado em `research/cache/validation/depth-worker-status.json`; checkpoints separam conexões e preservam horário original de recebimento dos diffs. Buffers têm limites, cache de raw gzip limitado a 256 MiB sem apagar dados; após três falhas seguidas ou capacidade esgotada, para e registra o impedimento. STOP encerra em até cinco segundos; perda abrupta do processo pode perder o bloco ainda em memória. Não fornece cobertura financeira aprovada, features, paper fills ou rentabilidade. Sua continuidade não depende da cota de modelos; o supervisor só inicia nova coleta após inspecionar processo/lock. Enquanto há lock de coleta, `begin` recusa cálculo de desenvolvimento concorrente.

## Paradas

- Consultar cota real antes de iniciar. Com 35% semanal consumido ou leitura indisponível/desatualizada, não iniciar tarefas que usem modelo; aguardar a recarga e manter o agendamento ativo para nova consulta. Ao observar aumento de dois pontos percentuais em uma rodada, interromper novas tarefas naquele dia. A cota é compartilhada; não é medição de custo exclusivo deste projeto nem uma trava exata de tokens.
- Uma tentativa de desenvolvimento por entradas congeladas. Dados/custos ausentes, falha financeira ou integridade inválida encerram a tentativa; não buscar janela posterior ou novos parâmetros para resgatá-la.
- Sem dados auditáveis, não iniciar agentes de desenvolvimento nem rodar backtests; dado/custo ausente encerra aquela tentativa e direciona a pesquisa para outra frente. Não há pausa automática após três evidências iguais nem limite total de verificações; evidência idêntica é recusada, e duplicatas, cota, STOP e revisão humana continuam valendo.
- `research/cache/validation/STOP` impede novas rodadas locais. Locks e tentativas ativas exigem inspeção antes de recuperar; não remover lock vivo ou matar processo com PID reaproveitado.
- Prazos de subprocessos precisam de `subprocess.run(..., timeout=180)` em comandos Python previamente revisados, sem shell e com apenas um processo de cálculo. Interromper os subagentes que excederem o prazo. O controlador registra prazo vencido, mas não mata processos nem impõe sozinho limites de CPU/RAM.

## Controle auditável

`python scripts/research_controller.py status` consulta o registro. `preflight`, `round`, `begin` e `finish` persistem somente metadados no cache, com gravação atômica e lock exclusivo. Uma tentativa só começa se a candidata estiver explicitamente revisada como `ready_for_development` e existirem arquivos de regra, dados, custos e engine dentro do projeto; quatro hashes preservam o congelamento. A CLI não altera essa prontidão. `maxAttemptsPerRound` limita o lote supervisionado e não limita rodadas nem tentativas por dia.

`finish` aceita somente bloqueada, reprovada ou candidata. Nunca aprova automaticamente. Sete aprovações só poderão ser contadas com relatórios financeiros, evidência estatística independente, paridade de execução e ao menos 60 dias/100 operações prospectivas revisadas. A ausência desses arquivos não é um erro a contornar.

## Registro da primeira rodada e continuidade

Pesquisador: nenhuma hipótese adicional distinta e executável com os dados locais foi identificada, conforme `round-1.md`. Revisor: controle de concorrência e cota implementado; a integração substituiu a sondagem de PID por sinais por bloqueio conservador seguro no Windows. Nenhum estudo financeiro foi repetido. Estado atual: **pesquisa ativa**. Rodadas futuras podem buscar fontes e hipóteses novas mesmo sem alterações nos arquivos locais, sem repetir avaliação financeira.
