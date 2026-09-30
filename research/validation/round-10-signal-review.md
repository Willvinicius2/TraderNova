# Revisão de sinal N21 — rodada 10

Somente leitura de `candidates.json` e `scripts/n21_book_audit.py`; nenhum teste ou rede. `scripts/n21_signal_features.py` estava ausente na única verificação.

## Requisitos para integração

- Reutilizar apenas livro L2 com snapshot que cubra a banda inteira e diffs consecutivos do mesmo `runId`/`connectionId`; qualquer lacuna, livro cruzado ou dado inválido/stale bloqueia o evento.
- Ancorar uma banda absoluta `[mid_pre * 0.999, mid_pre]` no mid antes do choque; D0 e D5 usam esses mesmos preços, mesmo com mid posterior mudando.
- Exigir queda de mid de pelo menos 5 bp em 1 segundo e recuo do best bid. A janela de recuperação deve conter cinco segundos completos de dados causais íntegros: não substituir duração por três pontos nem aceitar intervalos com lacuna.
- Só qualificar se não houver nova mínima de mid durante a janela, D0>0 e D5≥1,25×D0. A regra atual segue `awaiting_data`; o auditor de livro retorna `validated=false` e não produz intenção de negociação.
- Preservar `event time`, `received_at` e idade em segundos; UTC não está aprovado. Clock futuro, ausente ou incoerente deve bloquear elegibilidade, não ser corrigido por inferência.
- Binance BTCUSDT é fonte auxiliar de pesquisa. Não é cotação, contrato nem custo The5ers BTCUSD; paridade e execução CFD precisam de evidência própria.
- Entrada no primeiro ask após decisão, stop e saída são regras futuras, não fills realizados. Comissão taker, spread, slippage/tamanho executável e cooldown de 30 minutos ainda não foram aplicados em execução prospectiva.

O módulo de features não foi encontrado; não atribuo implementação, sinal ou resultado. N21 permanece não aprovada e não conta como nova família nesta revisão.

## Leitura do módulo de features

O módulo agora existe; esta é revisão do código visto, sem testes. O gate tem correções pendentes para o mínimo entre confirmação e choque (um mínimo no ponto inicial/current não pode, sozinho, reprovar recuperação), para usar mid real `(bid+ask)/2` e para limitar expoentes Decimal.

Outros riscos de integração: `source` aceita qualquer texto, mas saída rotula sempre `Binance_aux`; `externally_attested=true` é emitido sem atestação. `utc_verified`, `event_age_s` e `continuity_verified` são declarações do chamador, sem recomputar idade de `event_time`/`received_at` nem prova do intervalo completo. Só há três estados e sequência estritamente crescente (não contígua); assim a função não prova por si só cinco segundos sem lacunas nem mínimo contínuo. O `known_bid_lower_bound` também é aceito sem vínculo/hash do snapshot; banda pode parecer coberta por metadado afirmado. Vincular esses campos ao audit bundle, rejeitar origem não-Binance e retirar/qualificar `externally_attested` antes de tratar `hypothesis_signal` como causal.

A confirmação deve usar a banda absoluta ancorada no mid pré-choque; cooldown, fills e custos continuam não executados. Nenhum desses estados autoriza uma ordem ou uma aprovação.

Integração root: source restrito a binance_spot_l2, saída externally_attested=false e requires_verified_adapter=true, mínimo inclusivo ao ponto inicial corrigido, mid=(bid+ask)/2 exigido, representações exponenciais rejeitadas. Cinco checks sintéticos e suítes raiz passaram. Ainda protótipo matemático: sem adapter comprovando relógio/recebimento/continuidade/cobertura, sem cooldown e sem CFD fills/custos; não inicia prospectivo financeiro.
