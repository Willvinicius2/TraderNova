# N13 — piloto de aquisição encerrado

O piloto fez 10 GETs oficiais e preservou 1.960.488 bytes brutos, comprimidos com recibos em 242.514 bytes de cache. Limitou-se a parte de 01/10/2021 de BTC: quatro intervalos completos e seis páginas-pai truncadas que precisaram de subdivisão. Não cobriu o período completo nem ETH; não calculou skew, sinais ou PnL.

O [manifesto](options-trades-data-manifest.json) registra `state=round_limit`, `coverageComplete=false`, `crossPageIdentityAuditComplete=false`, `fullDataAuditComplete=false` e `complete=false`. Não houve erro de resposta ou conflito de ID dentro de página no piloto; isso não demonstra ausência de conflitos entre páginas, que ainda exige auditoria global. Os hashes de todos os corpos/recibos foram conferidos pela revisão principal.

O [script](../../scripts/download-goal-options-trades.py) retoma os intervalos pendentes usando no máximo 1 GET/s, timeout de 10 segundos, limite por rodada de requisições/bytes/tempo e teto total de cache de 2 GB. Respostas HTTP de erro e corpos parciais recebem recibos; 403 impede retomada automática. JSON inválido permanece salvo e torna a lacuna fatal. A cobertura só usa folhas não truncadas; um milissegundo ainda truncado é uma falha explícita. Nenhum preenchimento de lacuna ou inferência de negócio é permitido.

Seis testes sintéticos passaram, cobrindo divisão de intervalos, limites, retomada, imutabilidade, erros HTTP/esquema e separação entre cobertura e auditoria completa. Apenas uma instância deve operar o manifesto; este piloto não instalou serviço nem iniciou aquisição em massa. A [sequência restante](NEXT_STEPS.md) inclui metadados dos contratos, identidade global, gerador e executor short antes de qualquer congelamento para teste financeiro.
