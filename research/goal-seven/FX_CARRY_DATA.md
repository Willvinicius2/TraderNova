# FX carry — disponibilidade de dados para uma triagem

Auditoria somente de metadados e código existentes em 28/09/2026. Nenhum MT5 foi inicializado; nenhuma conta, login, ordem ou desempenho foi consultado.

## O que existe

- O cache HistData local é EURUSD M1 Bid OHLC, com derivados M15/H1/H4 para blocos 2010–15, 2019, 2020–21 e 2024. Seu manifesto declara que não há Ask nem spread: `spread=0` no CSV derivado significa dado ausente, não custo zero; também não há volume real. Não encontrei histórico USDJPY local.
- A exportação conhecida `D:/openclaude/Nova pasta/SNIPER_XAUUSD/calibration/market_metadata.json` é exclusivamente do CFD XAUUSD. Guarda OHLC/tick volume/spread/real_volume por barra e um snapshot pontual de spread/swap/metadados em 10/09/2026; nada disso fornece tarifas históricas para EURUSD ou USDJPY. Não reproduzo aqui valores de conta nem identificadores.
- `scripts/export_mt5_history_readonly.py` exporta somente `XAUUSD` M15/H1. Lê metadados atuais `spread`, `swap_mode`, `swap_long`, `swap_short` e `swap_rollover3days`; não guarda uma série de swaps, não aceita símbolo FX e não exporta bid/ask ticks. A lista de chamadas não inclui API de conta. O script também depende de terminal isolado explicitamente configurado; não foi executado nesta auditoria.
- A documentação oficial MQL5 consultada descreve `SymbolInfoDouble` e `SYMBOL_SWAP_LONG/SHORT` como propriedades de símbolo e `SYMBOL_SWAP_ROLLOVER3DAYS` como regra de rollover. Não encontrei nessa referência uma série histórica de tarifas de swap: [SymbolInfoDouble](https://www.mql5.com/en/docs/marketinformation/symbolinfodouble), [Symbol Properties](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants). É evidência de consulta corrente da propriedade, não prova formal de que nenhum servidor ofereça exportação separada.

## Consequência para carry de FX

Os dados atuais não sustentam um teste líquido de carry overnight em EURUSD ou USDJPY. Taxas de bancos centrais, diferenciais de juros ou pontos teóricos de swap não substituem o débito/crédito que o broker aplica ao contrato, na unidade e calendário dele. Um número corrente de `SYMBOL_SWAP_LONG/SHORT` não deve ser retroprojetado para anos anteriores.

Uma avaliação executável precisaria, por instrumento exato e período, de: barras/ticks com Bid e Ask ou spread histórico confiável; histórico datado de swap long/short com unidade/modo, moeda de cobrança e mudança de tarifa; horário/fuso de rollover, feriados e dia de triplo swap; contrato, comissão e regras de margem/liquidação do mesmo broker. Arquivos históricos de juros podem ser contexto explicativo, não o custo de financiamento observado.

## Viabilidade de 100 trades

O teto aproximado de **52 por ano** pressupõe no máximo uma entrada independente por semana; o hold de cinco noites, isoladamente, não impõe esse teto se houver sobreposição ou entradas mais frequentes. Sob essa cadência, 100 operações requerem pelo menos 1,92 anos completos de validação sem semanas perdidas. Uma validação de 2020–21 teria no máximo cerca de 104 oportunidades semanais e pouca folga; um período de três anos ou mais é mais plausível para cumprir 100 trades e conservar margem para sinais ausentes, gaps e filtros. Períodos usados para calibrar ou vistos antes não se tornam independentes por serem longos. Sem custos históricos do broker e preços de ambos os lados, aumentar a janela não resolve a lacuna de validade econômica.

**Conclusão:** viabilidade de preparar uma hipótese, sim; dados locais suficientes para medir carry líquido histórico de EURUSD/USDJPY, não. Não há resultado de estratégia nesta nota.
