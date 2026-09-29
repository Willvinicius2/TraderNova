# Observações prospectivas de OI (Binance USD-M)

Este coletor registra observações públicas de BTCUSDT, ETHUSDT e SOLUSDT para auditoria futura. Não calcula sinal, PnL ou aprovação de estratégia; dados da Binance não representam execução ou condições da The5ers. Não usa chave, conta nem endpoint de ordens.

**Rodada local iniciada:** 28/09/2026 às 23:42:44 UTC do PC, PID 17500, janela máxima de 24 horas, intervalo 300 s. A conferência posterior confirmou processo ativo, `running=true` e primeiro ciclo com 13/13 respostas. O offset do relógio permaneceu sinalizado. O estado atual deve ser lido em `research/cache/goal-seven/observations/status.json` e confrontado com o processo; esta nota é registro de lançamento, não promessa de disponibilidade contínua. A coleta depende do PC e da conexão. O arquivo `launch-20260928T234244.json` preserva caminhos dos logs e SHA do código executado.

Por ciclo, faz 13 GETs sequenciais: `/fapi/v1/time` e, para cada símbolo, `/futures/data/openInterestHist?period=5m&limit=12`, `/fapi/v1/klines?interval=1h&limit=3`, `/fapi/v1/ticker/bookTicker` e `/fapi/v1/premiumIndex`. Parâmetros e significados seguem o [catálogo oficial USD-M da Binance](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data). A história de OI disponibilizada pela API é limitada pelo provedor; a coleta não reconstrói observações perdidas.

Uso, a partir da raiz do repositório:

```powershell
python tests/goal-observations.py
python scripts/collect-goal-observations.py --cycles 1
```

Sem `--cycles`, a execução é em primeiro plano: início de ciclo a cada 300 s, por no máximo 24 h. Para encerrá-la, crie `research/cache/goal-seven/observations/STOP` ou aguarde o limite de duração. Remova o marcador manualmente antes de nova execução. Ciclos atrasados são pulados, sem rajada de recuperação. Há lock exclusivo contra dois processos, timeout de 8 s e até uma repetição por solicitação, ambos configuráveis dentro dos limites do código. HTTP 403/429 persistente interrompe a rodada. O teto de armazenamento é 1 GiB; o coletor falha explicitamente antes de ultrapassá-lo. O programa não instala serviço de sistema.

Os dados ficam em `research/cache/goal-seven/observations/observations.jsonl` (cache ignorado pelo Git). Cada resposta, inclusive erro, conserva URL, método, status, corpo bruto integral como texto UTF-8 ou hexadecimal, comprimento e SHA-256, horários UTC e nanossegundos do relógio monotônico do PC no envio/recebimento. O JSONL é append-only; cada linha inclui sequência, hash anterior e hash do registro. Ao reabrir, o programa verifica cadeia, integridade do corpo e última linha completa, recusando alterações. `status.json` é apenas resumo substituível, separado da evidência: inclui `running`, PID, ID e início/fim da rodada, motivo do término, duração máxima e última cadeia verificada. O término é gravado mesmo após erro recuperável; se faltar espaço para o próprio status, a tentativa de gravação falha explicitamente. O arquivo de lock fica preservado.

`serverTime` produz limites de deslocamento `serverTime - localReceive` e `serverTime - localSend` em milissegundos. São limites condicionais aos relógios observados e ao trânsito da requisição, **não certificação de tempo point-in-time**. Há flags para perda da calibração, salto de relógio PC, deslocamento absoluto superior a 5 s, alteração de offset, lacuna entre ciclos e lacunas detectáveis nas janelas OI/klines. Falhas e atrasos permanecem no journal; não há preenchimento retrospectivo.

Verificação de 2026-09-28: oito testes mock passaram e um único ciclo de rede retornou 13/13 respostas, com 15 linhas na cadeia. A calibração desse ciclo mostrou offset entre aproximadamente −33,69 s e −33,32 s (PC adiantado frente ao servidor sob a aproximação acima). Esse desvio impede tratar os horários do PC como carimbo certificado. Alertas de offset >5 s, regressão do relógio e estado terminal foram adicionados após o smoke. O JSONL bruto permaneceu intacto; o `status.json` foi reconstruído a partir dele para registrar `running=false`, com `statusReconstructedAfterSmoke=true` e PID desconhecido. O smoke não iniciou processo contínuo; a rodada posterior está registrada no início desta nota.
