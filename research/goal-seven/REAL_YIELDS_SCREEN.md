# N7 · juro real dos EUA → ouro: triagem de desenvolvimento

28/09/2026. **Reprovada; zero estratégia aprovada.** Esta é uma única família macroeconômica, distinta dos sinais de preço G1–G5. O [protocolo](real-yield-protocol.json) e os [hashes dos insumos/código](real-yield-freeze.json) foram salvos antes do primeiro cálculo de desempenho. Os cinco testes sintéticos de causalidade passaram. Só foi avaliado **2010–2015**; nenhum dado de 2016 em diante foi usado para PnL ou resgate.

Regra fixa: após a H1 rotulada 08:00 no servidor do broker, usar a última observação da curva **par real 10 YR do Tesouro dos EUA** datada entre 7 e 14 dias corridos antes do dia rotulado pelo broker. Queda de pelo menos 0,15 ponto percentual ante cinco observações anteriores gera compra; alta equivalente, venda. Entrada na abertura contígua 09:00; stop a 2 ATR14 do fechamento do sinal, alvo a 2R do preço efetivo de entrada, duração máxima de oito H1 e encerramento 20:00 conforme o motor legado. Uma entrada por dia. O capital inicial é US$100 mil, risco planejado **até** US$250 e exposição nocional máxima de 100%; o lote mínimo/passo pode reduzir o risco realizado. Custos base: spread US$0,60/oz, slippage US$0,10/lado e comissão US$10/lote ida e volta; stress: US$1,20, US$0,25 e US$20.

| Desenvolvimento 2010–2015 | Base | Stress |
| --- | ---: | ---: |
| Operações | 232 | 227 |
| Líquido | −US$3.741,45 | −US$9.831,43 |
| Fator de lucro | 0,853 | 0,624 |
| Drawdown proxy conservador | US$4.938,84 (4,94%) | US$9.907,03 (9,91%) |
| Maior perda diária adversa estimada | US$355,50 | US$346,95 |
| Custo noturno não precificado / violação da conta | 0 / não | 0 / não |

Os [resultados estruturados](real-yield-results.json) registram todos os gates. A amostra mínima, os tetos da métrica de drawdown e de perda diária, e a ausência de custo noturno/violação passaram. **Lucro líquido e fator de lucro ≥1,20 falharam em ambos os cenários**, portanto a candidata termina no desenvolvimento. Não houve mudança de regra, tentativa de outro limiar, seleção de direção/ano ou abertura de validação. Os detalhes de operações, curva e marcação ficam nos dois arquivos comprimidos em `research/cache/goal-seven/real-yields/`, ignorados pelo Git, com SHA-256 no resultado. O motor observou 1.559 descontinuidades H1 no período (inclusive sessões fechadas); saídas usam a próxima abertura observada se houver posição.

Limites independentes do resultado: a [fonte oficial Treasury](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rate-archives) baixada é um snapshot retrospectivo, sem vintage ou hora histórica de publicação verificada; sete dias de atraso não provam conhecimento ponto no tempo. A hora do arquivo XAU é um rótulo nativo do broker sem offset UTC confirmado. Custos e swap executáveis do contrato também não foram certificados. O `conservativeDrawdown` do motor usa vale adverso intrabar contra picos observados em aberturas/fechamentos; **não mede o máximo real intrabar** nem certifica o limite da mesa. Essas lacunas impediriam aprovação mesmo se a triagem tivesse lucro. `validated:false`, `operationallyApproved:false` e incremento da meta = **0**.
