# Rodada 3: agente r3-estrutura (scripts populares da comunidade TradingView)

Ativo BTCUSD, protocolo lab-v2. Os números estão em R (custo base de 0,10% por lado). O DD% supõe 0,5% de risco por operação. Nenhuma estratégia foi refinada: todas abriram a validação já na primeira calibração, e depois disso o protocolo proíbe reajuste.

Acesso às fontes: o WebFetch não abriu o TradingView, a LuxAlgo, a Alpaca, a ProRealCode nem a mql5, e a busca de código no GitHub está bloqueada. As regras vieram dos resumos do WebSearch, do porte Python `advanced-ta` (baixado do PyPI, só no caso da Lorentzian) e da definição conhecida de cada script.

## TV32_lorentzian: Machine Learning: Lorentzian Classification (jdehorty)
- **Fontes:** tradingview.com/script/WhBzgfDu e o porte Python advanced-ta 0.1.7 (lido no pacote).
- **Regra:**
  - Atributos padrão do Pine: RSI14, WT(10,11), CCI20, ADX20, RSI9. WT e CCI são normalizados pelo mínimo e máximo históricos acumulados. O porte Python normaliza com a amostra inteira, o que olha o futuro, e isso não foi copiado.
  - Usa distância Lorentziana e kNN exato sobre candles passados espaçados de 4 em 4, dentro de uma janela de L candles.
  - **Rótulo "futuro":** sinal de fech[j+4]−fech[j], usado só quando j+4 ≤ t.
  - **Rótulo "pine":** pareamento literal do script, que é causal e equivale a uma reversão dos últimos 4 candles.
  - Filtros de volatilidade e de regime, gatilho no kernel racional-quadrático (que não repinta) e saída "fixo4" ou "dinamico".
  - Stop de proteção de k×ATR14.
- **Calibrado:** k vizinhos, L, tipo de rótulo, saída, k do stop e lado (288 combinações).
- **Veredito: CANDIDATA.** Escolha: H4, 8 vizinhos, L=2000, rótulo futuro, saída dinâmica, k=2, só compra.

| Fase | Trades | netR | PF | DD | Stress netR |
|---|---|---|---|---|---|
| Desenvolvimento | 93 | +113,1 | 4,05 | 5,0R (2,5%) | – |
| Validação | 30 | +5,3 | 1,48 | 4,2R | +3,6 |
| Reserva | 78 | +48,2 | 2,14 | 11,0R (5,5%) | +41,2 |

- **Avisos:**
  - DSR = 0,0: a escolha provavelmente é sorte entre combinações.
  - Na validação, o resultado sem a maior operação é de só +1,6R.
- **Testes extras:**
  - Truncamento: os sinais calculados com dados cortados batem 100% com os sinais calculados com tudo, então não há olhar o futuro.
  - Previsões do kNN embaralhadas ao acaso, mesma regra, 20 sorteios: mediana de +104 no desenvolvimento, −8,8 na validação e +59 na reserva.
- **Interpretação:** o lucro vem quase todo do gatilho do kernel com compras num mercado de alta, não do classificador. O kNN só se destacou do acaso na validação, e por pouco. É candidata frágil e não deve virar sinal sem acompanhamento prospectivo.

## TV33_smc_bos: Smart Money Concepts (LuxAlgo), BOS/CHoCH
- **Fontes:** tradingview.com/script/CnB3fSph, luxalgo.com/library e uma cópia do Pine no Scribd. O código não foi lido diretamente: veio do resumo da busca.
- **Regra:**
  - As pernas seguem o `leg(size)` da LuxAlgo, com o swing confirmado `size` candles depois, sem repintura.
  - O rompimento é `crossover(close, nível)`, e cada nível vale uma vez.
  - É CHoCH quando rompe contra o viés e BOS quando rompe a favor.
  - Modos testados: entrar só no CHoCH, só no BOS ou em todos.
  - Saída no rompimento oposto e stop de k×ATR14.
- **Calibrado:** size (5 a 50), modo, k e lado (270 combinações).
- **Veredito: REPROVADA_VALIDACAO.** Escolha: H4, size 10, CHoCH, k=3, compra e venda.

| Fase | Trades | netR | PF | DD | Stress netR |
|---|---|---|---|---|---|
| Desenvolvimento | 161 | +162,9 | 3,22 | 5,2R | – |
| Validação | 69 | −7,2 | 0,83 | 8,1R | −9,8 |

- **DSR:** 0,08.
- **Interpretação:** seguir a estrutura de mercado funcionou na alta de 2016 a 2020 e não se sustentou em 2021-2022.

## TV34_andean: Andean Oscillator (alexgrover)
- **Fontes:** tradingview.com/script/x9qYvBYN, o artigo da Alpaca (Alex Pierrefeu) e a ProRealCode. A fórmula veio dos resumos.
- **Regra:**
  - Envelopes exponenciais "online" do preço e do preço ao quadrado.
  - Bull = sqrt(dn2−dn1²) e Bear = sqrt(up2−up1²), com sinal = EMA9 do maior dos dois.
  - Compra quando Bull cruza Bear (modo "cruz") ou quando Bull > Bear e Bull > sinal (modo "sinal").
  - Sai no cruzamento oposto e usa stop de k×ATR14.
- **Calibrado:** n de 25 a 200, modo, k e lado (144 combinações).
- **Veredito: REPROVADA_VALIDACAO.** Escolha: H1, n=200, modo cruz, k=4, só compra.

| Fase | Trades | netR | PF | DD | Stress netR |
|---|---|---|---|---|---|
| Desenvolvimento | 146 | +255,5 | 4,67 | 6,4R | – |
| Validação | 75 | −10,1 | 0,79 | 25,5R (12,7%, acima do limite) | −14,6 |

- **Correção de implementação:** a inicialização do 1º candle foi corrigida (o `nz` do Pine), com efeito nulo no resultado.
- **Interpretação:** é um seguidor de tendência que capturou a alta do período de desenvolvimento e sangrou na lateral de queda da validação.

## TV35_trend_magic: Trend Magic (CCI + ATR)
- **Fontes:** tradingview.com/script/kRIjThLZ (KivancOzbilgic), a LuxAlgo library e o script uRqGTZOw.
- **Regra:**
  - ATR = SMA(TR,5) e a linha anda a partir de mín−coef×ATR (com CCI ≥ 0) ou de máx+coef×ATR (com CCI < 0), sem recuar.
  - **Modo "alerta":** entra quando a mínima cruza acima da linha (compra) ou a máxima cruza abaixo (venda).
  - **Modo "cor":** entra quando o CCI cruza 0.
  - Sai no sinal oposto e usa stop de k×ATR14.
- **Calibrado:** período do CCI, coeficiente, modo, k e lado (288 combinações).
- **Veredito: REPROVADA_VALIDACAO.** Escolha: H4, CCI 20, coeficiente 1,5, alerta, k=3, só compra.

| Fase | Trades | netR | PF | DD | Stress netR |
|---|---|---|---|---|---|
| Desenvolvimento | 182 | +135,7 | 3,27 | 5,4R | – |
| Validação | 84 | −1,2 | 0,97 | 11,3R | −4,1 |

- **Interpretação:** o período do CCI quase não muda o resultado, porque quem decide é a linha de ATR. Na prática é mais um trailing de volatilidade que não sobreviveu fora da alta.

## Observações sobre o motor
Não achei bug. Duas observações:
- O R por operação pode ficar enorme no D1: um stop de 3×ATR em 2016 com alvo na alta de 2017 dá cerca de 300R. Isso infla o netR de estratégias de tendência compradas no desenvolvimento.
- O DSR é 0 ou próximo de 0 mesmo em escolhas com PF alto quando muitas combinações são parecidas, o que é esperado.
