# Meta: cinco estratégias distintas validadas

Registrada por solicitação do usuário em 15/09/2026. A meta permanece aberta; uma variação de parâmetros ou o mesmo método em outro ativo não conta como outra estratégia.

## Requisitos de entrega

- Cinco métodos com regras e parâmetros fechados, sem editor de estratégia no site.
- Histórico real, custos explícitos, critérios registrados antes dos resultados e avaliação cronológica fora do período usado para escolher parâmetros.
- Resultado líquido positivo, fator de lucro, quantidade de operações e drawdown suficientes segundo o protocolo de cada rodada.
- Confirmar programa/servidor, contrato, custos e cálculo dos limites da mesa antes de declarar aprovação para aquela conta.
- Conta informada: 100 mil, perda diária de 3 mil, perda total de 10 mil. O perfil do projeto anterior registra confirmação do High Stakes 100K Summer, 2-Step 10/5. A página oficial do Summer informa perda diária de 3% do maior saldo/patrimônio no fechamento anterior e perda total de 10% do capital inicial; contrato e custos executáveis ainda precisam de confirmação. O protocolo v1 mantém suas hipóteses originais para preservar a reprodução.
- Validar risco conjunto e acompanhar prospectivamente antes de liberar alertas manuais. Sem execução de ordens reais.
- Preservar o visual aprovado, modos Backtest/Simulação em tempo real e Robô com motivos, entrada, stop e alvo.

## Evidências e andamento

1. Rodada inicial cripto: 18 combinações, nenhuma aprovada.
2. Calibração H1 v2: 27 variantes, nenhuma aprovada operacionalmente.
3. Calibração H1 v3: 21 configurações incluindo os controles; histórico desde 2022, filtros H4 e saídas protegidas. Nenhuma substituição de preset passou a regra de adoção; zero aprovação histórica.
4. Ouro CFD v1: cinco famílias, dois presets por família, regras congeladas em `gold-v1-protocol.json`. Exportações locais anteriores verificadas por hash; todas as cinco foram reprovadas. Resultados e operações em `public/research/gold-v1*.json`. Nenhuma estratégia foi liberada para alertas reais.
5. Ouro H1 v2: sete configurações, cinco famílias; desenvolvimento 2010–2015, mesmas hipóteses de custos e referência diária corrigida para o Summer. Todas reprovadas no desenvolvimento. Validação 2016–2018 e reserva 2019–2021 não foram abertas para essas candidatas; 2022–ago/2026 foi apenas diagnóstico. Relatório em `research/OURO_H1_V2.md` e operações em `public/research/gold-h1-v2*.json`. A contagem permanece 0 de 5 aprovadas.

Os períodos finais de recalibração já foram vistos em pesquisas anteriores. Não descrevê-los como amostra intocada, nem declarar rentabilidade futura garantida. Uma meta de pesquisa não autoriza baixar critérios após perdas, excluir períodos desfavoráveis ou repetir buscas até encontrar números positivos.

## Reproduzir

Cripto v3: `python scripts/download-history-v3.py` e `npm run research:calibrate:v3`.

Ouro: `python scripts/run_gold_research.py --source "D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration"`. O script lê os CSVs existentes; não inicializa MT5, consulta conta ou modifica arquivos de origem. Requer NumPy; dependência local em `scripts/requirements-research.txt`.

Arquivos completos locais de pesquisa ficam em `research/cache/`, ignorados pelo Git. Relatórios públicos e operações simuladas ficam em `public/research/`. Nenhum relatório contém posições reais ou credenciais da conta.
