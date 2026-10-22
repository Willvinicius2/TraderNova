# Laboratório de estratégias

Lugar único para pesquisar, calibrar e validar estratégias de sinais. Nada aqui envia ordens ou consulta conta.

## Como funciona uma rodada

1. Cada agente pega estratégias publicadas (site, livro ou artigo, sempre citado) que **não** estão em `registry.json`.
2. A estratégia vira um arquivo em `strategies/<ID>.py` com regra fechada e uma grade de parâmetros declarada antes de rodar.
3. `calibrate.py` testa a grade **só no desenvolvimento**, exige robustez (vizinhos de parâmetro também precisam funcionar) e escolhe uma combinação.
4. Só a combinação escolhida é aberta na validação e depois na reserva, com custo base e custo dobrado. Não há reajuste depois disso.
5. Se reprovar no desenvolvimento, o agente pode tentar até 2 refinamentos com motivo (`<ID>_r1`, `<ID>_r2`). Isso atende o "não desistir de primeira" sem transformar a validação em otimização.
6. `report.py` gera `RELATORIO.md` e acrescenta tudo ao `registry.json`, para nenhuma estratégia ser repetida em rodadas futuras.

## Reproduzir

```
python research/lab/data.py --bitstamp <pasta do clone>   # instruções no topo de data.py
python research/lab/calibrate.py L01_supertrend
python research/lab/report.py --round 1
python research/lab/data.py --fxdata EURUSD --work <pasta>   # ticks Dukascopy do FX-Data, ~2 h de rede
python research/lab/crossasset.py --asset EURUSD          # CANDIDATAS do BTC no EURUSD, sem recalibrar (também USDJPY)
```

Requer Python 3 com pandas e numpy. Dados ficam em `research/cache/lab/` (não versionado).

## Limites conhecidos

- Rodada 1 só tem BTCUSD (Bitstamp). A rede do ambiente bloqueia Binance, Yahoo e Dukascopy; EURUSD entrou via espelho GitHub dos ticks Dukascopy (2009 a 08/07/2022) só para teste cruzado (`results/_cross_EURUSD.json`). Ouro, NAS100, ETH e SOL seguem sem fonte acessível com cobertura suficiente.
- O desenvolvimento (2016–2020) foi um mercado de alta forte no BTC; estratégias compradas tendem a parecer boas ali. Por isso a validação 2021–2022 inclui o ano de baixa de 2022.
- Custos são cenários fixos, não custos executáveis certificados da mesa.
