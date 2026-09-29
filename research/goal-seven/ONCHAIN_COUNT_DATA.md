# N12 `TxTfrCnt` acquisition and data-quality memo

Coin Metrics Community API, metric-only request (`TxTfrCnt`, 1d), BTC and ETH, 2021-09-01 through 2024-12-31 inclusive. No prices, returns, signals, triggers, PnL or execution results were requested or calculated.

Requests: 1/20; raw response bytes: 185862/10485760; complete: True.

| Asset | Rows normalized | Missing daily labels | Invalid time/count | Duplicate copies excluded | First/last UTC epoch | SHA-256 normalized |
|---|---:|---:|---:|---:|---|---|
| BTC | 1218 | 0 | 0/0 | 0 | 1630454400/1735603200 | `1ef2b96e42ebc88e64f100fcbe8671c464c40cb200e51c71ddedb9217b0c1400` |
| ETH | 1218 | 0 | 0/0 | 0 | 1630454400/1735603200 | `1dbc2704c6881e021702806547a8afb688a10bc7d1634a37c5cfce80526b5aac` |

Every missing daily label is enumerated in the manifest. No gaps are filled. Duplicated timestamps are excluded in all copies; counts must be finite, positive integers and are stored as decimal strings. Source timestamps are preserved as UTC epoch seconds only when exactly on the daily midnight grid; no flooring/rounding is applied.

Raw response bodies are retained byte-for-byte with URL, HTTP status, UTC receipt time, byte length and SHA-256 in the manifest. Only metric `TxTfrCnt` was requested. Raw and normalized files are in the ignored `research/cache/goal-seven/onchain-count/` cache.

The protocol labels source day D conservatively and treats the activity interval as ending D+24h; its later decision and entry timing are fixed before looking at values. This archive does not contain original publication receipts or immutable historical vintages, so historical availability at the delayed decision remains unproven. `--verify` checks local hashes and coverage only; it makes no network requests.
