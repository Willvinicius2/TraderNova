# Continuidade da meta

Estado central: [STATUS.md](STATUS.md), **0/7**, meta ativa. Os critérios de [protocol.json](protocol.json) continuam congelados. N2, N5, N6, N7, N11 e N12 reprovaram a triagem financeira; N8 e N10 não atingiram a amostra; N9 aguarda dados de custos executáveis. Não reabrir janelas posteriores para resgate nem contar uma variante como outra família.

A frente atual é **N13**, [skew de opções para sinais em futuros](OPTIONS_SKEW_IDEA.md). A [aquisição planejada](N13_ACQUISITION_PLAN.md) tem custo de dados considerável; o piloto usa limites explícitos. O campo IV permanece na unidade nativa da fonte: a regra é invariante a uma escala constante positiva, sem inferir percentual ou anualização. Nenhum skew, sinal ou PnL N13 foi calculado.

Antes de testar N13:

1. Conferir o manifesto e o relatório do piloto de `download-goal-options-trades.py`; retomar por lotes limitados, sem processos concorrentes, após verificar os recibos e espaço disponível. Falhas HTTP, páginas truncadas e respostas incompletas não podem virar cobertura completa. Não insistir em acesso 403.
2. Concluir a auditoria global de IDs entre páginas e entre pais truncados e suas folhas, preservando conflitos/revisões. A cobertura de intervalos não substitui essa auditoria. Confirmar metadados oficiais de strike, tipo e expiração dos instrumentos antes de agregá-los. Não assumir vencimento somente pelo nome.
3. Implementar agregação diária e gerador N13 com testes sintéticos de informação disponível, filtros de contratos, 90 dias anteriores e prioridade. O executor atual v3 é **long-only**: short exige implementação separada e verificação de custos, sinal do funding, stop/gap e drawdown, preservando versões congeladas.
4. Congelar regra, dados, custos, código e testes antes de contar condições. Executar só desenvolvimento; amostra insuficiente encerra sem PnL, reprovação financeira encerra sem consultar 2025–2026. Passar na triagem não aumenta a contagem de aprovadas.

O coletor de observações públicas [descrito aqui](OBSERVATIONS.md) roda localmente com duração máxima de 24 horas. Conferir `status.json` com o processo antes de declarar que está ativo. Ele não gera sinais nem inicia automaticamente um teste prospectivo. Não alterar seu código durante uma rodada. A assinatura Apple continua adiada pelo usuário.
