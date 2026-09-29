# N13 option instrument catalog join pilot

Read-only metadata QA at 2026-09-29T00:29:28.649377+00:00; all 14 leaves and 6 splits were read after verifying archive and catalog hashes. No price/performance fields were inspected.

Verified trade artifacts: 20/20. Trade appearances including overlaps: 45569; unique names by symbol: BTC=361, ETH=431. The count includes repeated windows from leaves and splits; it is not a count of unique trades.

| Currency | Appearances | Matched | Missing | kind=option pass/fail | base currency | price_index | creation â‰¤ trade | trade < expiry | strike > 0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC | 28481 | 28481 | 0 | 28481/0 | 28481/0 | 28481/0 | 28481/0 | 28481/0 | 28481/0 |
| ETH | 17088 | 17088 | 0 | 17088/0 | 17088/0 | 17088/0 | 17088/0 | 17088/0 | 17088/0 |

Pass/fail counts are over matched trade appearances and include repeats. No tenor/moneyness filtering or signal/PnL calculation. Examples are capped (10 per check, 20 missing names) in the JSON snapshot. The present-day `include_old=true` catalog provides metadata consistency only; it does not establish point-in-time membership or remove survivorship concerns. Snapshot: `options-instrument-join-pilot.json`.
