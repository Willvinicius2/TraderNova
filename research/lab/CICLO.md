# Ciclo automático do laboratório

Roteiro de cada rodada automática (o Claude segue isto a cada disparo agendado).

1. `git pull` no ramo do laboratório; se não houver dados em `research/cache/lab`, clonar o Bitstamp e rodar `data.py` (instruções no topo do arquivo).
2. Ler `FILA.md`, `registry.json` e o último `RODADA_N.md`. Escolher os próximos itens não marcados que não repetem nada do registro.
3. Lançar 4 agentes de estratégia (4 estratégias cada) + 1 agente de dados, com as mesmas regras da rodada 2 (`protocol.json` lab-v2, `status.py`, notas em `notes/rN-*.md`).
4. Ao fim: `diagnose.py`, `report.py --round N`, `export_dashboard.py`, atualizar o painel, escrever `RODADA_N.md`, marcar a fila, commit e push.
5. Candidatas novas e antigas: rodar em todo ativo novo que o agente de dados trouxer, com os mesmos parâmetros (sem recalibrar).
6. Mandar ao Will um resumo curto (o que passou, o que falhou, placar acumulado). Se a meta de `FILA.md` for atingida, avisar com destaque.

## Código Pine (fora do repositório)
Se `/home/user/labdata/pine/` não existir (container novo), clonar com `git clone --depth 1` em `/home/user/labdata/pine/<dono>_<repo>`:
- https://github.com/deepentropy/lightweight-charts-indicators (1.545 scripts da comunidade traduzidos para TypeScript, com autor e regra)
- https://github.com/everget/tradingview-pinescript-indicators
- https://github.com/Alorse/pinescript-strategies
- https://github.com/f13end/tradingview-custom-indicators
- https://github.com/ArunKBhaskar/PineScript, https://github.com/ricardosantos79/pinescript, https://github.com/Heavy91/TradingView_Indicators

## Lições que valem para toda rodada
- 2016–2020 foi alta forte do BTC: quase todo seguidor de tendência "só compra" brilha no desenvolvimento e quebra em 2021–2022. Isso não é sinal da regra.
- Para candidatas, rodar o teste placebo (mesma regra de saída, entradas ao acaso ou previsões embaralhadas): se o placebo ganha parecido, a vantagem não é da estratégia (caso TV32 Lorentzian).
- Rodada 5: indicadores de volume, Elder/Williams, reversão curta de Connors e padrões de barras deram 0 de 16. Vantagem grande no desenvolvimento com DSR baixo ou dependente de uma operação quase sempre some em 2021–2022. Próximos blocos (9 em diante) devem priorizar regras que já operam vendido ou têm filtro de regime.
