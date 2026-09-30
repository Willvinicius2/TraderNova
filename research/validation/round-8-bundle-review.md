# Round 8 — revisão do auditor Aave

Revisão estática de `scripts/audit_aave_bundle.py`; sem executar testes nem rede.

- Os offsets do Provider estão corretos para a amostra round 4: `reserve-eth_call-response.json` contém 12 palavras; índices 3/4/6 coincidem exatamente com stable debt, variable debt e variableBorrowRate nos dois ativos do `report.json`.
- Confirmações úteis: hashes de request/headers/response, sequência fixa e parâmetros comparados ao raw, bloco/revalidação conferidos; aprovações exigem `is False` e o relatório de saída mantém todas falsas.
- A codificação ABI do endereço no `balanceOf` usa padding esquerdo a 32 bytes. A falha sintética reportada (`hx900`, comprimento inválido) é defeito do mock, não evidência de bug no padding atual.
- `pool_tuple_decoding=unknown_abi_not_decoded` é apropriado: Pool raw fica opaco e não sustenta os campos derivados. O Provider é decodificado por offsets, mas isso ainda depende da ABI congelada; o relatório deve continuar não aprovado.
- Pendência no código inspecionado: `_raw` e `manifest.json` usam leitura sem limite antes de validar tamanho; a soma inicial de tamanhos não evita crescimento concorrente. Aplicar leitura limitada também ao manifesto.
- JSON raiz e estruturas internas não têm validação completa de tipo. Arrays/escalares como request/response ou `params` malformados podem escapar como `AttributeError`/`IndexError`; `bool` também passa por `isinstance(id, int)` e `chain_id == 1`. Rejeitar com `AuditError` claro.
- Caminhos resolvidos de raw são contidos no bundle; ainda convém deduplicar por caminho resolvido e recusar symlinks internos se unicidade de artefatos for requisito.

Root informou quatro fixtures sintéticas e uma falha causada somente pelo `balance` mock curto; não executei nem confirmei essa contagem. O bundle round 7 disponível é falha HTTP 403 e não serve como captura válida para este auditor.

Integração root posterior: leituras raw/manifest bounded, contagem de arquivos e symlinks, dedupe por caminho resolvido, tipos JSON/IDs e params estritos, JSON keys duplicadas rejeitadas e Decimal local precision100. Cinco testes passaram; bundle real HTTP403 rejeitado. Aprovações financeiras permanecem false.
