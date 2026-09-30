# N22 — Ethereum Aave V3 finalized snapshot

- RPC: PublicNode https://ethereum-rpc.publicnode.com; eth_getBlockByNumber finalized succeeded.
- Block: 0x18e1036 (26,087,478), hash 0x678d461edd50ff34a3e318275bc9294b3ce1c1c27619d2f4e3745e674c35d8f2, timestamp 2026-09-30T03:02:47Z UTC.
- Pool: 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2; AaveProtocolDataProvider: 0x7B4EB56E7CD4b454BA8ff71E4518426369a138A3. Addresses cross-checked against Aave governance; ABI fields against Aave contract docs.
- Request window: 2026-09-30T03:20:28.3979359Z–2026-09-30T03:22:13.8602866Z. Raw reserve, pool and liquidity responses are adjacent JSON files; hashes are in report.json.

| Reserve | Borrow | Available liquidity | Utilization* | Variable borrow rate |
|---|---:|---:|---:|---:|
| USDC | 2,244,946,708.2743 USDC | 151,925,592.040766 USDC | 93.6615% | 4.3842% nominal annual |
| WETH | 1,754,664.966389 WETH | 285,513.135569 WETH | 86.0083% | 2.0567% nominal annual |

* Utilization = total stable and variable debt / (debt + underlying token balance of reserve aToken). Stable debt was zero in both responses. Liquidity was read using underlying.balanceOf(aToken) at the same finalized block.

Cloudflare RPC returned HTTP 200 with JSON-RPC error -32046 Cannot fulfill request; PublicNode succeeded. This is a single finalized snapshot, not a PIT series, signal test, or performance claim. Aave variableBorrowRate is shown as nominal annual rate, not compounding APY. Fee, execution venue, slippage/funding and short contract remain unverified.

The existing GraphQL poller was read only and not run. Three operational risks: unbounded JSONL disk growth; no graceful stop beyond process interruption; concurrent instances can duplicate/interleave appends.


The full raw block header response was not retained; the reported block fields were extracted during acquisition. This sample is not approved as a financial dataset. APY normalization, repeated collection, source cross-check and executable costs remain prerequisites.
