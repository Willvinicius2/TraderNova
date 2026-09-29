# Barras mark H1 diárias para lacunas congeladas

Cinco dias completos ausentes nos arquivos mensais USD-M foram identificados diretamente no `dataAudit.mark` do [freeze N11](open-interest-freeze.json): BTCUSDT em 31/07/2022, 02/10/2022 e 24/02/2023; ETHUSDT em 02/10/2022 e 24/02/2023. Esta aquisição serve apenas à preparação de dados N12. Não altera os arquivos mensais, o freeze N11, sinais ou resultados.

Os cinco ZIPs **diários** oficiais de `data/futures/um/daily/markPriceKlines/{symbol}/1h/` e seus cinco `.CHECKSUM` retornaram HTTP 200. Cada ZIP contém as 24 aberturas H1 ordenadas do respectivo dia UTC, com SHA-256 igual ao checksum oficial; são 120 horas recuperadas. Foram 10 GETs e 5.367 bytes de resposta, dentro dos limites de 20 GETs e 10 MB. A [Binance Public Data](https://github.com/binance/binance-public-data/blob/master/README.md) documenta os arquivos públicos diários e o `.CHECKSUM` adjacente.

O [manifesto](mark-gap-data-manifest.json) lista cada dia em `files` com `symbol`, `day`, `kind=mark_h1`, `status`, `cachePath`, `sha256`, `expectedMissingTimes` e `recoveredTimes` em segundos Unix UTC. Cada GET conserva URL, status, hora de envio/recebimento reportada pelo PC, bytes, SHA-256 e caminho bruto no cache ignorado `research/cache/goal-seven/mark-gaps/`. Esses horários de recebimento não certificam o relógio nem a disponibilidade histórica do arquivo. O script não sobrescreve bytes locais divergentes e, quando o manifesto já existe, verifica o snapshot sem rede.

```powershell
python scripts/download-goal-mark-gaps.py --verify
```

Um runner novo deve consumir **somente** entradas `status=verified` e conferir hash/checksum. Cada barra diária deve ocupar exclusivamente um dos `expectedMissingTimes`; qualquer colisão com a série mensal ou divergência de dia deve interromper a integração, não escolher a versão mais favorável. Esses arquivos não fornecem bid/ask histórico, preenchimento de ordens ou equivalência com outro contrato/corretora. Nenhuma janela de 2025+ foi consultada e nenhum PnL foi calculado.
