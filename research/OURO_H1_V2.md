# Ouro H1 — segunda rodada

Sete configurações de cinco famílias, registradas antes de calcular resultados. As sete foram reprovadas no desenvolvimento de 2010–2015. Os períodos de validação (2016–2018) e reserva retrospectiva (2019–2021) não foram avaliados para essas candidatas. Nenhuma aprovação operacional.

| Família / seleção | Desenvolvimento base (USD) | Desenvolvimento stress (USD) | Trades desenvolvimento | Jan/2022–ago/2026 (USD) | Jan/2025–ago/2026 (USD) | Trades / PF recente |
|---|---:|---:|---:|---:|---:|---:|
| G1 Pullback de tendência H1 / control | -9963.92 | -9975.76 | 248 | -250.55 | 1000.95 | 158 / 1.069 |
| G2 Faixa inicial e reteste H1 / control | -9944.96 | -9904.65 | 133 | -9869.50 | -3948.86 | 125 / 0.775 |
| G3 Retorno às Bandas H1 / control | -9867.37 | -9806.36 | 137 | -5034.76 | -949.04 | 29 / 0.652 |
| G4 Varredura e confirmação H1 / confirmation | -4547.69 | -8062.50 | 137 | -2233.87 | -836.43 | 51 / 0.803 |
| G5 Divergência RSI H1 / control | -1271.44 | -2559.73 | 47 | -1000.55 | 27.92 | 9 / 1.043 |

Resultados recentes são descritivos e já conhecidos de outras pesquisas. Um lucro isolado em período recente não recupera uma candidata que falhou no desenvolvimento. A seleção usa o resultado com custos elevados dividido pela estimativa de drawdown; variantes não contam como novas estratégias.

## Dados e execução

- H1: 99.999 velas desde 2009; H4: 34.089 velas desde 2004. Hashes preservados contra o manifesto original. As 24.981 horas completas de sobreposição H1/M15 têm exatamente os mesmos OHLC.
- A tentativa de ampliar o M15 pelo terminal isolado falhou com IPC. Não foi usada na pesquisa. A instância aberta para exportação foi encerrada; o terminal original e as fontes anteriores não foram modificados.
- Sinal somente depois do fechamento, entrada na próxima abertura contígua, horários nativos do servidor. Saída às 20h, observável em H1. Sem interpolar 20h45 ou candles ausentes.
- Conta fictícia US$100 mil, risco planejado US$250, piso total US$90 mil. Referência diária=max(saldo, patrimônio marcado) no último fechamento disponível do dia anterior; teto=min(US$3 mil,3% da referência). Uma violação mantém a conta desqualificada nos dias seguintes.
- Referência do programa recuperada do perfil anterior confirmado pelo usuário: High Stakes 100K Summer 2-Step10/5. [Regras públicas do Summer](https://the5ers.com/summer-plan/). Não é confirmação de tarifas ou condições executáveis do contrato.
- Custos base: spread US$0,60/oz, slippage US$0,10/lado, comissão US$10/lote ida e volta. Stress: US$1,20, US$0,25 e US$20. Valores mantidos; spread mínimo intrabar não é preço de abertura executável.
- Posição inesperadamente mantida à noite fica marcada com custo não reconstruído. Não se inventa swap zero. Stops simultâneos ao alvo têm prioridade; gaps podem exceder o risco planejado.
- Queda nos fechamentos e envelope adverso intrabar são separados. O envelope considera extremos adversos até o stop executável e gaps sem esse limite. Não reconstrói a ordem real de ticks nem usa uma máxima futura favorável para dimensionar entradas.

## Reprodução e testes

Requer os CSVs originais locais e NumPy conforme scripts/requirements-research.txt. Não há conexão com MT5 ou execução de ordens no estudo.

```powershell
python scripts/audit_gold_source.py --source "D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration" --output research/gold-source-audit.json
python scripts/rebuild_gold_h1_cache.py --source "D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration"
python scripts/run_gold_h1_research.py --source "D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration" --phase evaluate
python tests/gold-h1-execution.py
python tests/gold-h1-signals.py --source "D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration"
python tests/gold-h1-report.py
```

A seleção já está congelada em research/gold-h1-v2-selection.json. O comando develop foi executado antes de evaluate e recusa sobrescrever uma seleção existente. O comando rebuild_gold_h1_cache reproduz as cinco seleções contra os hashes e métricas congelados, sem sobrescrever o manifesto, e cria somente os caches ausentes. Foi verificado em outro diretório vazio: as cinco reproduções coincidiram exatamente. Não remover ou alterar a seleção da cópia de trabalho.

14 testes sintéticos de execução, 45 verificações de causalidade/simetria/sinais e reconciliação de 3.502 operações exportadas passaram. As contas de simulação não recebem reposição de capital; a falta de orçamento completo de US$250 impede novas entradas.

Faltam cinco candidatas que passem nos critérios, custos executáveis confirmados, acompanhamento prospectivo, execução idêntica no motor em tempo real e teste do risco conjunto. A meta continua aberta.
