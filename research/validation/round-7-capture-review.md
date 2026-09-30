# Revisão da captura Aave round 7

Revisão estática do coletor final e da captura preservada; não repeti a chamada, não usei rede e não executei testes.

## Resultado da aquisição

`research/cache/validation/aave-captures/round-7/manifest.json` registra `failed_raw_only`: `eth_chainId` recebeu HTTP 403 e corpo não JSON. Os arquivos de request, headers e response foram preservados (59, 490 e 17 bytes). Não há bloco nem retorno de reserva utilizável; não contornar a falha nem reclassificar como captura bem-sucedida. Headers são registrados como normalizados por `urllib`, não bytes HTTP originais.

## Revisão do coletor

A versão lida valida estritamente cabeçalho de bloco, `jsonrpc` e ID de resposta, shape hexadecimal dos retornos ABI, hash no número congelado e altura `finalized` posterior; permite avanço normal. O limite cumulativo considera arquivos anteriores no diretório de cache e a resposta é limitada antes de persistir. Root informou quatro testes aprovados; não foram executados nesta revisão.

A validação dos retornos do `eth_call` cobre somente formato hex e múltiplos de 32 bytes para reservas. Não decodifica campos nem comprova a semântica/ABI do Pool: **pool ABI semanticamente desconhecida**. Capture UTC e aprovações continuam falsas.

`REQUEST_TIMEOUT=4` é timeout de socket do `urllib`, não limite garantido de duração total da chamada (DNS/conexão e overhead podem excedê-lo). Exigir timeout externo do processo de 180 s. STOP é verificado antes/depois de chamadas; não alegar garantia de parada em cinco segundos durante chamada bloqueante.

`audit_aave_bundle.py` não estava presente no caminho `scripts/` durante esta revisão.
