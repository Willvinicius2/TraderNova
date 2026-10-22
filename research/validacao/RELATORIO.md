# Validação das 11 candidatas do laboratório

Data: 22/10/2026. Pasta separada do laboratório (`research/lab` não foi alterado). Tabelas completas em [RESUMO.md](RESUMO.md), números brutos em `results/`.

## Resposta curta

- **Dá para aproveitar uma coisa:** seguir tendência no BTC, **recalibrando os parâmetros uma vez por ano** com os 3 anos anteriores. As candidatas não sobrevivem com parâmetros fixos para sempre, mas sobrevivem quando são recalibradas desse jeito.
- **Três regras se saíram melhor que uma média móvel simples:** AI Trend Navigator (TV85), Heikin Ashi suavizada (TV39) e RVI (TV74). Juntas, com o risco dividido entre elas, deram **+68,7% em 2019–2026** fora da amostra (0,5% de risco por operação, sem juros compostos), com **queda máxima de 2,8%**. Ficaram no zero em 2022 e 2025, sem perda relevante.
- **A vantagem é de risco, não de retorno.** Uma média móvel simples, com a mesma recalibração anual, deu +79,6%, mas com queda de 7,7% e dois anos negativos. Grande parte do ganho das candidatas é a tendência do BTC, não a regra em si.
- **Fora do BTC nada se sustenta.** Em ouro e cinco pares de forex (2013–2022), nenhuma candidata foi positiva de forma estável. O ouro é a exceção parcial: CUSUM, Keltner, Derivative Oscillator e Lorentzian foram positivos com 2, 3 e 4 anos de calibração, mas com pouca margem (PF 1,1–1,9) e só 6 anos de teste.
- **Descartar:** Estocástico (L07), Momentum 60d (L04, queda de 17%), Aroon (TV21) e Lorentzian (TV32).

## O que foi testado

Para cada uma das 11 candidatas (motor, regras e dados do laboratório):

1. **Parâmetros do laboratório, ano a ano (2015–2026)**, em 4 versões: original, comprado e vendido, só vendido e com filtro de regime (compra só acima da média de 200 dias e vende só abaixo).
2. **Sensibilidade da grade:** quantas combinações de parâmetros ficam positivas na validação (2021–22) e na reserva (2023–26).
3. **Walk-forward:** calibra nos 3 anos anteriores com os critérios do laboratório (PF ≥ 1,15, vizinhos robustos, queda ≤ 10%), opera o ano seguinte sem olhar e rola. Repetido com 2 e 4 anos de calibração para ver se o resultado depende dessa escolha.
4. **Outros ativos:** ouro, EURUSD, GBPUSD, USDJPY, AUDUSD e USDCAD, recalibrando no próprio ativo pelo mesmo walk-forward, e também com os parâmetros fixos do BTC.
5. **Referências ingênuas:** média móvel simples e rompimento de Donchian passaram pelo mesmo walk-forward. Uma regra só vale a pena se render mais por unidade de queda que elas.

## Resultado por estratégia (BTC, walk-forward 2019–2026)

| Estratégia | Fora da amostra | Queda máx. | Anos positivos | Veredito |
|---|---|---|---|---|
| TV85 AI Trend Navigator | +171R, PF 3,5 | 4,7% | 7 de 8 | **Aproveitável** |
| TV39 Heikin Ashi suavizada | +128R, PF 2,4 | 4,3% | 6 de 8 | **Aproveitável** |
| TV74 RVI | +114R, PF 1,7 | 4,7% | 7 de 8 | **Aproveitável** |
| TV72 CUSUM | +307R, PF 2,5 | 10,1% | 6 de 8 | Igual à referência (queda alta); com filtro de regime: +105R, queda 8,2% |
| L12 Keltner (com regime) | +115R, PF 2,1 | 7,4% | 6 de 8 | Igual à referência |
| TV79 Derivative Osc. | +56R, PF 1,4 | 4,5% | 6 de 8 | Igual à referência |
| TV81 TDI | +53R, PF 1,4 | 6,7% | 7 de 8 | Igual à referência |
| TV21 Aroon | +60R, PF 1,4 | 13,9% | 6 de 8 | Descartar |
| TV32 Lorentzian | +45R, PF 1,4 | 8,4% | 4 de 8 | Descartar |
| L04 Momentum 60d | +295R, PF 2,8 | 17,5% | 7 de 8 | Descartar (queda acima de 10%) |
| L07 Estocástico | −5R | 8,4% | 3 de 7 | Descartar |
| *Referência: média móvel* | +159R, PF 2,7 | 7,7% | 6 de 8 | — |
| *Referência: Donchian* | +119R, PF 1,9 | 6,1% | 7 de 8 | — |

R = múltiplos do risco da operação. Com 0,5% de risco por operação, 100R ≈ 50% da conta em soma simples.

## Comprado e vendido

- Só vendido rende pouco: de +4R a +39R em 11 anos, quase tudo em 2018 e 2022. Estocástico, Derivative Oscillator e TDI perdem dinheiro só vendidos.
- O **filtro de regime (média de 200 dias)** resolve o problema de 2022 que derrubava as candidatas: com ele, Keltner, CUSUM, RVI e Heikin Ashi ficaram positivas em 2022. O custo é ganhar menos nos anos de alta. Para quem quer operar os dois lados, o filtro é o caminho; para o maior retorno, a versão original recalibrada ainda ganha.

## Limites

- A escolha das três "aproveitáveis" usou o resultado do walk-forward de 2019–2026. Isso é uma última camada de seleção, então o número real deve ser menor. O próximo passo honesto é acompanhar em papel a partir de agora.
- Os dados de forex e ouro são candles de corretora MT5 (fuso do servidor, nov/2012 a mar/2022), não os ticks Dukascopy do laboratório. O download dos ticks levaria horas e foi trocado por essa fonte só para este teste de robustez.
- Os custos do BTC são os do laboratório (0,10% por lado, stress 0,20%). Em CFD de corretora podem ser maiores; o stress segue positivo (+60,9% na carteira).

## Como usar

1. Em janeiro de cada ano, rodar a calibração das três regras nos 3 anos anteriores (`validar.py` faz isso) e fixar os parâmetros do ano.
2. Operar as três em paralelo no BTC, dividindo 0,5% de risco entre elas.
3. Antes de dinheiro real: 30 dias ou mais em papel, comparando os sinais com a carteira de referência.

## Reproduzir

```
python research/lab/data.py --bitstamp <clone>                 # BTC, como no laboratório
python research/validacao/dados_fx.py <clone ejtraderLabs>     # ouro e forex (instruções no topo do arquivo)
python research/validacao/validar.py --benchmarks              # ~10 min com 4 núcleos
python research/validacao/resumo.py                            # gera RESUMO.md
python research/validacao/carteira.py                          # carteira das aproveitáveis
```
