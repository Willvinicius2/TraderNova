# Ferramenta estatística para futuras avaliações

Implementação: `scripts/goal_bootstrap.py`. **Ferramenta numérica auxiliar; não aprova estratégias.** Não foi aplicada aos resultados históricos N1–N15. O protocolo global congelado permanece intacto e a contagem continua em 0/7.

## Método proposto, a congelar antes da avaliação prospectiva

Retornos simples diários líquidos da equity marcada ao fim de cada dia UTC, após custos observados. Todos os dias consecutivos são obrigatórios, incluindo zeros de dias inativos; datas ausentes não são preenchidas com zero. Reamostragem circular em blocos de sete dias, com reposição e truncamento da última semana para conservar o tamanho original. Cada réplica estima a média diária.

Para o índice global de avaliação independente `k`, a alocação é `alpha = 0,05 / (k*(k+1))`. Reserva-se 90% para a cauda bootstrap e 10% para incerteza de Monte Carlo. O limite unilateral basic é `2*média_observada - quantil_(1-cauda)(médias_bootstrap)`, usando quantil superior sem interpolação. Exige-se limite positivo além da tolerância numérica.

Se `m` réplicas atingirem pelo menos duas vezes a média observada, a guarda de Monte Carlo exige `P(Binomial(B, cauda) <= m) < 0,1*alpha`, com pequena margem numérica. A soma binomial é calculada em logaritmos; valores próximos ao limiar não passam. O relatório guarda essa log-CDF, a alocação do erro, `m`, `B`, a semente, PCG64 e versão NumPy. A estimativa suavizada `(m+1)/(B+1)` nunca é zero e **não é apresentada como p-valor calibrado**.

São necessárias pelo menos `max(10000, ceil(100/cauda))` réplicas. A exigência de 100 observações esperadas na cauda é uma regra de resolução conservadora, não um teorema. O teto local é 500 mil réplicas; portanto `k >= 15` fica inconclusivo nesta implementação. O teto economiza recursos e jamais altera alpha. Não repetir sementes ou aumentar B após ver resultados para procurar aprovação.

A ferramenta propõe **26 semanas completas (182 dias)** como piso numérico conservador. É uma escolha metodológica heurística, **não uma alteração do mínimo global de 60 dias nem uma garantia de suficiência**. Antes de usar evidência prospectiva real, esse piso e o método precisam integrar o plano previamente congelado e a revisão independente. Distribuições constantes dos retornos ou das réplicas ficam inconclusivas.

## Contrato e limites

Entrada JSON: `trialNumber` inteiro positivo, `seed` inteiro de 64 bits não negativo, `replicates` inteiro e `days`, uma lista de objetos `date` (YYYY-MM-DD) e `netReturn` (fração, por exemplo 0,001 significa 0,1%). Execução: `python scripts/goal_bootstrap.py CAMINHO_INPUT.json`; o resultado vai para stdout, com hashes do input e do script. O script não faz chamadas de rede ou IA.

O índice `k` fornecido **não é autenticado**. Ainda são necessários registro global de avaliações, comprovação de recebimento/independência dos dados, congelamento anterior à janela, mínimo de operações, custos e contrato executáveis, risco e revisão independente. `numericalSupport: true` é suporte aritmético condicional; `validated` e `operationalApproval` permanecem sempre falsos. Não há integração para liberar sinais no aplicativo.

Blocos semanais supõem que a dependência relevante e a distribuição observada sejam representativas. A guarda de Monte Carlo controla a simulação condicional, não garante a cobertura estatística do bootstrap nem lucro futuro. Seleção retrospectiva, dependência mais longa e mudanças de regime continuam limitações.

## Verificação

Cinco testes sintéticos em `tests/goal-bootstrap.py`: soma binomial contra distribuição exata pequena; repetibilidade e retenção de dias zero; dados negativos/constantes, réplicas degeneradas, amostra curta e resolução insuficiente; rejeição de datas ausentes/duplicadas, valores não finitos e índice inválido; semana parcial conferida por concatenação explícita. Revisão separada por subagente conferiu blocos, limite basic, CDF e divisão de alpha. O caso de réplicas degeneradas apontado na revisão foi corrigido e coberto por teste. Nenhum retorno financeiro real foi avaliado nesta etapa.

Fontes primárias: [Künsch (1989), bootstrap de observações dependentes](https://doi.org/10.1214/aos/1176347265), [SciPy, intervalos basic e unilateral](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html), [SciPy, distribuição binomial](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binom.html). A implementação usa NumPy e biblioteca padrão; SciPy não foi instalado.
