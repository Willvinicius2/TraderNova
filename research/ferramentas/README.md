# Ferramentas da pesquisa de estratégias

Ferramental compartilhado por todas as frentes de pesquisa (laboratório, validação das candidatas, hipóteses novas).
Este arquivo é o registro de **qual ferramenta faz qual função**. Quem adotar, trocar ou descartar uma ferramenta
atualiza a tabela no mesmo commit, com o motivo. A skill `ferramentas-pesquisa` (em `.claude/skills/`) faz o Claude
consultar este mapa sozinho antes de qualquer trabalho de pesquisa.

## Mapa: função → ferramenta

| Função | Ferramenta adotada | Onde | Por que esta |
|---|---|---|---|
| Candles e funding do perpétuo (BTC, ETH, SOL e outros USDT-M) | Arquivo público da Binance (`binance-public-data`), espelho S3 quando o domínio é bloqueado | `dados_binance.py` | Grátis, com SHA-256 por arquivo, funding real para os vendidos. O domínio `data.binance.vision` dá 403 neste ambiente; o espelho S3 do mesmo bucket funciona |
| Open interest e razão long/short (5 min, desde 2020-09) | Mesmo arquivo, `daily/metrics` | `dados_binance.py --metrics` | Única fonte grátis com histórico |
| Backtest de posição com taxa, slippage e funding | Próprio, vetorizado | `backtest.py` | Gera a série de retornos por variante que a estatística precisa; 1 linha por regra, sem dependência de licença |
| Backtest por trade com stop/alvo intrabarra | Motor do laboratório | `research/lab/engine.py` (ramo do laboratório) | Já validado em 150+ estratégias; não duplicar |
| Lookahead | Próprio, ideia do `lookahead-analysis` do freqtrade | `estatistica.checar_lookahead` | Recalcula o sinal com dados truncados; atraso de 1 barra no estresse |
| Walk-forward rolante | Próprio | `estatistica.walk_forward` | Janelas por data, sem sobreposição |
| CPCV (validação cruzada combinatória purgada) | Próprio (López de Prado, cap. 12) | `estatistica.cpcv`, `cpcv_sharpes` | 40 linhas; o skfolio traria scikit-learn só para isso |
| PBO por CSCV | Próprio (Bailey et al., 2015) | `estatistica.pbo` | O `pypbo` é AGPL e não está no PyPI |
| PSR, Deflated Sharpe, MinTRL | Próprio (Bailey e López de Prado) | `estatistica.psr`, `dsr`, `min_trl` | Fórmulas fechadas; testadas contra valores do artigo |
| Hansen SPA (data snooping) | `arch` 8.0.0 (NCSA) | `estatistica.spa` | Implementação de referência, bootstrap estacionário |
| MCPT (permutação de barras) | Reescrito do `neurotrader888/mcpt` (MIT) | `estatistica.permutar_barras`, `mcpt` | Testa o processo inteiro, inclusive a otimização |
| Bootstrap dos trades | Próprio | `estatistica.bootstrap_trades` | Queda no percentil 95 e PF no percentil 5 |
| Portões e veredito | `portoes.json` + `validar.py` | aqui | Veredito por regra fixa, nunca por opinião |
| Registro de tentativas (N do DSR) | `tentativas.jsonl` | aqui | Pré-registro com hash antes de qualquer número |
| Protocolo para o Claude | Skill `validar-estrategia` | `.claude/skills/validar-estrategia/` | Mesmo passo a passo em toda frente |
| Escolha de ferramentas | Skill `ferramentas-pesquisa` + agente `curador-ferramentas` | `.claude/` | Decide e adota sem precisar de pedido, com as regras abaixo |
| Revisão cética de resultado | Agente `revisor-cetico` | `.claude/agents/` | Padrão bull vs. bear do TradingAgents, aplicado a um JSON de resultado |
| Relatórios para o Will | Claude Docs (conector) | — | Documento vivo, comentável |

## Avaliadas e não adotadas agora

| Ferramenta | Motivo | Quando reavaliar |
|---|---|---|
| vectorbt | Commons Clause; o `backtest.py` cobre o que usamos | Varreduras com milhares de variantes por segundo |
| backtesting.py, pypbo, cryptofeed | AGPL (ruim para o app que será vendido); pypbo nem está no PyPI | — |
| skfolio | Puxa scikit-learn para um CPCV de 40 linhas | Otimização de carteira entre estratégias |
| freqtrade, nautilus_trader | Plataformas inteiras; só copiamos a ideia do lookahead | Paper trading realista (nautilus) |
| Binance MCP | Rede da nuvem bloqueia a Binance; o arquivo público já cobre o histórico | Quando houver dado ao vivo a consultar de dentro do Claude |
| hmmlearn, ruptures, LightGBM | Sem hipótese que precise deles ainda | Hipótese 7 (HMM) e meta-labeling do relatório |
| Skills de terceiros (tradermonty, Kryhr, agiprolabs) | Rodam código com as permissões do Claude; escrevemos as nossas a partir do esboço do relatório | Se uma delas trouxer algo que as nossas não fazem |

## Regras para adotar uma ferramenta nova

1. Só dados de mercado: nada que envie ordens ou peça chave de corretora.
2. Licença permissiva (MIT, BSD, Apache, NCSA) para o que pode ir ao app. AGPL/GPL só em script offline, e anotado aqui.
3. Versão fixada em `requirements.txt`; mantida nos últimos 18 meses; instalável pela rede do ambiente (PyPI e GitHub funcionam; Binance, Yahoo, Kaggle e Hugging Face não).
4. Menos de ~50 linhas para reescrever? Reescreva com testes em vez de puxar a dependência.
5. Toda adoção entra na tabela acima no mesmo commit.

## Uso

```
pip install -r research/ferramentas/requirements.txt
python research/ferramentas/dados_binance.py BTCUSDT ETHUSDT SOLUSDT --spot   # ~2 min, 36 MB em research/cache/binance
python research/ferramentas/testes/test_estatistica.py
python research/ferramentas/validar.py H01_donchian_ensemble                  # ~5 min; --rapido para testar código
```

Usar só a estatística sobre resultados próprios (por exemplo, a matriz de retornos de outra frente):

```python
import sys; sys.path.insert(0, "research")
from ferramentas import estatistica as est
est.pbo(matriz_T_x_N)              # todas as variantes testadas, inclusive descartadas
est.dsr(retornos_oos, n_tentativas=153 + len(grade))
est.spa(matriz_T_x_N)              # contra ficar fora do mercado
est.bootstrap_trades(trades_em_fracao_da_conta)
```

Resultados de cada hipótese ficam em `resultados/<ID>.json`; o histórico de tentativas em `tentativas.jsonl`.
A reserva (de `reservaInicio` em diante) só abre com `--abrir-reserva`, uma vez por versão da hipótese.

## Hipóteses rodadas

| ID | Veredito | Fora da amostra (2022–set/2025, BTC+ETH+SOL) | Leitura |
|---|---|---|---|
| H01 Donchian ensemble com alvo de vol | REPROVADA (trades) | +25,4%, Sharpe 0,79, queda 7,4%, 76 trades, PF 5,4 | O walk-forward escolheu "só comprado" em 15 de 16 janelas; o lado vendido piorou o Sharpe em todas as variantes (0,76–0,88 contra 1,27–1,39). Funding custou ~0,16 de Sharpe. Passou PBO (0,05), SPA (p 0,011), CPCV e estresse; reprovou trades < 100, janelas positivas 50%, DSR 0,60 com N = 171 e MCPT p 0,23 (o ganho é quase todo a deriva de alta, que a permutação preserva) |
| H02 Momentum 7/14/28 dias com alvo de vol | REPROVADA (janelas positivas, DSR) | +35,2%, Sharpe 1,04, queda 7,0%, 246 trades, PF 1,95 | Passou PBO (0,04), SPA (p 0,001), MCPT (p 0,025), CPCV, bootstrap e estresse (custo 3×: Sharpe 0,85). Reprovou 7 de 16 janelas positivas e DSR 0,61 com N = 161. O walk-forward escolheu "só comprado" em todas as janelas; o vendido perdeu (16 trades, −3,7%). Funding custou ~0,13 de Sharpe |
| H06 Filtro de funding sobre o H02 | REPROVADA (janelas positivas, DSR, MCPT) | +33,4%, Sharpe 1,07, queda 6,1%, 239 trades | Zerar compras com funding de 7 dias acima do percentil 90 melhorou pouco a queda; vender nesses momentos piorou. Não acrescenta o suficiente ao H02 |

Observação para a próxima versão dos portões (a decidir antes da próxima hipótese, não para reavaliar estas): em
sistemas só comprados, janelas de 90 dias sem posição contam como "não positivas". Em H02, 4 das 9 janelas reprovadas
ficaram zeradas. Vale considerar "≥ 60% das janelas com posição" em `ferramentas-v2`.
