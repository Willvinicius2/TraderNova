# N22 — plano de ingestão Aave (sem coleta nesta etapa)

## Objetivo e limites

Especificar um coletor local, determinístico e sem IA para obter observações futuras de N22. Este plano não contém série temporal, dados de mercado novos, custos verificados nem evidência financeira. O snapshot da rodada 4 é uma amostra única, não série PIT nem confirmação de executabilidade. N22 continua `awaiting_data`.

Antes de executar, congelar deployment Ethereum Core Aave V3, `chainId=1`, Pool e DataProvider e endereços USDC/WETH já definidos em `candidates.json`. Hashes e ABI devem ser registrados como configuração imutável da captura; mudança de endereço/ABI requer revisão e nova versão, nunca remapeamento silencioso.

## Unidade de captura

- Uma unidade é um único bloco retornado por `eth_getBlockByNumber("finalized", false)`, com número, hash, timestamp e parent hash preservados em hexadecimal e forma normalizada.
- Após obter o header `finalized`, fixar número/hash; todas as chamadas `eth_call` usam o mesmo `blockNumber` explícito. Registrar o hash esperado no manifesto. Uma leitura inicial adicional por hash é redundante para esta captura mínima.
- Coletar `Pool.getReserveData` para USDC e WETH, `DataProvider.getReserveData` para ambos e `ERC20.balanceOf(aToken)` para liquidez disponível. Guardar retorno JSON-RPC completo, sem decodificar por cima do original.
- Depois das chamadas, consultar novamente o hash do bloco congelado por número e o estado atual de `finalized`. Invalide/isole a unidade somente se o hash no número congelado divergir ou se a altura `finalized` recuar abaixo do bloco congelado; avanço normal de `finalized` é válido. Não reparar nem substituir os bytes brutos.
- Persistir em cada resposta: método, parâmetros exatos, endpoint identificado, HTTP status, JSON-RPC id/erro, hora de início e recebimento, headers HTTP brutos e corpo bruto. SHA-256 dos headers e do corpo/recibo por chamada; o manifesto liga hashes, resultado decodificado, bloco e configuração.

## Tempo e causalidade

- Guardar timestamp do bloco como tempo de evento, e relógio local monotônico/UTC de início e recebimento como tempo de conhecimento observado.
- `available_at` é o instante de recebimento (`received_at`) em UTC, explicitamente marcado `utc_clock_approved=false`; enquanto a aprovação UTC não existir, a causalidade fica `unverified` e a observação não pode alimentar estudo retrospectivo.
- Nunca atribuir disponibilidade ao timestamp do bloco nem ao `lastUpdateTimestamp` da reserva. Manter este último como campo de evento separado.
- Se relógio aprovado estiver indisponível, atrasado ou incoerente, salvar evidência bruta com causalidade não verificada e bloquear sua elegibilidade, sem corrigir horários por inferência.

## Decodificação, congelamento e falhas

- Preservar inteiros on-chain em strings decimais; validar comprimento/tipos ABI, endereços, chain ID e correspondência do bloco antes de decodificar. Falha de qualquer reserva invalida a unidade inteira.
- Nomear `variableBorrowRateRay` como taxa nominal anual APR em RAY. Derivar `APR = ray / 10^27`; não rotular como APY nem compor. Qualquer conversão APR/APY deve ser definida e revisada antes de congelar regra/dados, e não pode ser introduzida após observar resultados.
- Utilização reproduzível: dívida total / (dívida total + liquidez disponível), usando quantidades normalizadas pelos decimals congelados. Salvar também valores raw e fórmula/versão.
- Restringir cada chamada e resposta a limites configurados; um processo, concorrência 1, timeout por chamada e teto de bytes/blocos por execução. Sem repetição adaptativa para resgatar falha; retry limitado de transporte pode repetir apenas a mesma chamada/bloco e todos os intentos ficam registrados.
- Escrita append-only por captura com manifesto atômico. Duplicata de (chainId, block number, block hash, reservas) é recusada; hash igual não cria nova evidência.

## Segurança operacional e saída

- Consultar `research/cache/validation/STOP` antes de iniciar e entre blocos; STOP encerra coleta em até cinco segundos e não inicia novas chamadas.
- Usar lock exclusivo com PID, início e identificador da captura; não remover lock vivo. Em falha, registrar estado e liberar somente lock próprio.
- Cache separado de evidência publicada, com quota limitada e sem apagar raw; falta de espaço bloqueia antes de iniciar a próxima unidade.
- Saída é apenas observacional: não chama modelos, não executa cálculo de sinal/backtest e não concede aprovação financeira, feed, custo, relógio ou estratégia.
- Antes de qualquer desenvolvimento, ainda congelar feed/mercado ETH executável e contrato short, comissão, slippage e funding; o coletor Aave não fornece esses itens nem satisfaz o requisito de dados prospectivos/históricos por si só.



## Revisão estática do coletor (30/09/2026)

`capture_aave_finalized.py` foi revisado sem execução. A versão mais recente lê o hash novamente no número congelado, consulta `finalized` ao final e permite avanço, rejeitando hash divergente ou altura finalizada abaixo do bloco. A leitura inicial adicional por hash não é necessária nesta captura mínima. Limites de gravação agora são checados antes de salvar cada blob; há soma de cache Aave anterior e timeout RPC de 4 s, compatível com o alvo STOP de 5 s em chamadas bloqueantes. Isso é análise estática; execução e revisão final do root continuam pendentes.
