# Testador local de estratégias

Ferramenta adicional implementada: [bootstrap semanal para futuras avaliações](BOOTSTRAP_METHOD.md). Tem controle de resolução e de incerteza de Monte Carlo, cinco testes sintéticos e saída sempre não operacional. Não foi aplicada ao histórico nem modifica a fila N13; ainda exige plano prospectivo congelado e evidência de proveniência.

O testador está implementado em `scripts/goal-lab.py`. A primeira família ligada à fila é **N13**, assimetria da volatilidade implícita de opções para operações direcionais em futuros BTC/ETH. Não é uma busca irrestrita de parâmetros e não conta variantes como estratégias diferentes.

Execução no diretório do projeto:

```powershell
python scripts/goal-lab.py run --max-hours 16
python scripts/goal-lab.py status
```

A fila espera o coletor existente terminar e então executa, em ordem: auditoria global das identidades; conciliação dos contratos; congelamento dos hashes de regras, fontes, custos e código; agregação diária; contagem de gatilhos; backtests base e stress no desenvolvimento. Menos de 100 gatilhos impede o cálculo de PnL. Dados incompletos, alterações de fontes, erros ou resultado parcial interrompem para revisão. Resultado negativo não abre janelas posteriores para procurar um resgate.

Cada fase deixa logs em `research/cache/goal-seven/lab`. O resumo fica em `status.json` e o resultado de cada execução tem arquivo próprio. O processo usa lock exclusivo, duração máxima e marcador `research/cache/goal-seven/lab/STOP`. Não alterar seu código enquanto roda. O status é um registro local: conferir também o PID antes de afirmar que está ativo. Não existe serviço instalado para reiniciar após desligar o computador.

Relatórios esperados: `options-skew-freeze.json`, `options-skew-daily-manifest.json`, `options-skew-sample.json` e, somente se permitido, `options-skew-results.json`. Operações detalhadas preservadas no cache têm hash no relatório. Resultados não são sobrescritos. A fila termina em amostra insuficiente, reprovação, candidata para revisão ou necessidade de corrigir dados/execução; **não aprova automaticamente estratégias**.

Validação técnica nesta implementação: 12 testes do coletor corrigido, três do preparador, seis do runner e três da fila passaram; testes existentes do gerador e executor também passaram na etapa anterior. Conciliação real de 247.439 metadados brutos/normalizados e 26.304 barras H1 por ativo e por série perp/mark, sem avaliar sinal ou PnL N13. Revisão independente do contrato entre os componentes não encontrou bloqueadores.

A execução Python não chama modelos, não usa chave de IA e não faz novas combinações de parâmetros. O agente só precisa intervir em hipóteses novas, falhas e revisão dos resultados. Isso reduz o trabalho de IA, mas não reserva nem controla a cota usada por outras conversas: a [documentação oficial de consumo](https://learn.chatgpt.com/docs/pricing) informa que limites são compartilhados e dependem do modelo, contexto e complexidade. A leitura da conta no início desta etapa indicou 2% da janela semanal consumidos; é uma fotografia daquele momento.

O registro de tentativas e o congelamento antes dos resultados seguem a preocupação descrita no estudo primário [The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf): selecionar a melhor regra entre muitos testes pode produzir uma descoberta falsa. Automatizar cálculos não remove esse problema nem prova lucro futuro.

Meta: **sete famílias realmente aprovadas, atualmente 0/7**. Mesmo um histórico positivo exige as etapas independentes/prospectivas, custos e contrato executáveis, controle estatístico e revisão do protocolo global. A próxima família só entra após hipótese registrada e verificação de que não repete as anteriores. Nenhuma ordem é executada; assinatura Apple e publicação nativa continuam fora desta etapa.

Fila iniciada em 2026-09-29 02:54:43 UTC, PID 18444, commit `75f8830c24aea168c904ff246282c0e20a282eab`, limite de 16 horas. Primeira conferência: `waiting_for_data`, processo presente, zero chamadas a modelos. O coletor PID 17436 também estava presente, com 336 folhas, 2.075 intervalos pendentes e zero erros naquele instante. A consulta de cota no final desta implementação indicou 6% consumidos na janela semanal; não é custo atribuído exclusivamente a este chat. `npm test` passou. Não manter uma sessão de IA consultando repetidamente a espera: a própria fila acompanha a coleta e preserva o resultado para revisão.
