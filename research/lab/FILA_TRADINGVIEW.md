# Fila TradingView (comunidade): próximas rodadas automáticas

Catálogo montado em 21/10/2026 pelo agente de catálogo do Laboratório.
Entra na fila depois de TV24–TV35, que estão em teste agora (Vix Fix, Waddah Attar, Impulse MACD, VFI, Coral Trend, HalfTrend, Gaussian Channel, McGinley, Lorentzian Classification, SMC BOS/CHoCH, Andean Oscillator e Trend Magic). Nenhum deles aparece aqui como item novo.

## Quantos scripts existem e por que não dá para testar todos

- **Tamanho da biblioteca.** A documentação oficial do Pine Script v6 ([First steps](https://www.tradingview.com/pine-script-docs/primer/first-steps)) fala em **mais de 150 mil scripts da comunidade, cerca de metade open-source**. A documentação da v5 dizia "mais de 100 mil". Um fórum de terceiros (NexusFi) fala em mais de 200 mil, mas esse número não é oficial e não consegui confirmá-lo. Neste catálogo uso **150 mil+**.
- **A maioria é indicador, não estratégia.** Este catálogo usou como principal amostra a coleção [deepentropy/lightweight-charts-indicators](https://github.com/deepentropy/lightweight-charts-indicators), que traz 1.545 ports fiéis de scripts da comunidade, 408 deles do conjunto dos "mais curtidos". Só **17 dos 1.545 títulos** são estratégias (`strategy()`). O resto desenha linhas, zonas, tabelas e painéis, e a regra de entrada e de saída fica a critério de quem olha o gráfico. Para testar um indicador, primeiro alguém precisa escrever a regra.
- **Muitas são a mesma regra com outro nome.** Na mesma amostra, 241 ports usam RSI, 213 usam pivôs, 102 usam MACD, 61 são de FVG/order block e 44 são variações do Supertrend. O `registry.json` já reprovou as regras centrais de cruzamento de médias, Supertrend, Keltner, Bollinger, RSI, estocástico, MACD, WaveTrend, QQE e Range Filter. Por isso a maioria das "novidades" populares (UT Bot, Twin Range Filter, QQE MOD, VuManChu, Squeeze Momentum etc.) é **DUPLICADA**. A lista delas, com o item do registry que já cobre cada uma, está no fim do arquivo.
- **Muitos scripts repintam.** Na amostra, 60 ports trazem `repaint`, `backpaint` ou `lookahead_on` explícitos. A conta não inclui ZigZag, Nadaraya-Watson Envelope, linhas desenhadas `length` candles para trás e `request.security` em tempo gráfico maior sem defasagem. Um sinal que muda depois do fechamento não pode ser testado como foi publicado.
- **Alguns precisam de dados que não temos**, como hash rate, open interest, liquidações, delta por tick (CVD) ou índices de amplitude.
- Conclusão: com 150 mil scripts, testar tudo seria inviável e, na maior parte, repetiria testes. O que cabe testar é cada **regra central distinta**, uma vez só. Esta fila faz isso.

## Fontes usadas

- Pesquisa na web: documentação oficial do Pine v6/v5; o [blog do TradingView sobre Editors' Picks](https://www.tradingview.com/blog/en/indicators-editors-picks-20161) (o programa começou em 2020 e escolhe só scripts open-source; em 2022 foram 84 escolhas); a [lista "Best Editors' Picks of 2022"](https://www.tradingview.com/chart/SPY/eTOyVYgR-Best-Editors-Picks-of-2022/); e listas de terceiros de "mais curtidos", em que Squeeze Momentum [LazyBear], Smart Money Concepts [LuxAlgo], CM MACD MTF e WaveTrend aparecem no topo.
- Repositórios clonados com `git clone --depth 1` em `/home/user/labdata/pine/`, **fora do repositório e sem versionar**:

| Sigla | Pasta em /home/user/labdata/pine/ | Conteúdo |
|---|---|---|
| DE | `deepentropy_lightweight-charts-indicators/src/community/<arquivo>.ts` | 1.545 ports TS de scripts da comunidade. Cada cabeçalho traz a regra, o título exato e o autor do Pine original (licença MPL-2.0, a mesma do original). O índice do conjunto "mais curtidos" está em `docs/INDICATOR_INVENTORY_COMMUNITY.md`. |
| EV | `everget_tradingview-pinescript-indicators/<pasta>/<arquivo>.pine` | 210 arquivos `.pine` originais do everget (osciladores, médias, trailing stops, volume) |
| AL | `Alorse_pinescript-strategies/strategies/...` | 74 arquivos `.pine`, cerca de 50 estratégias da comunidade com `strategy()` |
| F13 | `f13end_tradingview-custom-indicators/...` | 116 arquivos `.pine` (osciladores, canais, algumas estratégias) |
| — | `ArunKBhaskar_PineScript`, `ricardosantos79_pinescript`, `Heavy91_TradingView_Indicators`, `just-nilux_awesome-tradingview`, `pAulseperformance_awesome-pinescript` | coleções menores e listas de links (ICT, RicardoSantos, Market Profile) |
| TV | só no TradingView | script open-source que não foi encontrado nos clones. O agente precisa reescrever a partir da fórmula publicada. |
| EMB | indicador embutido do TradingView | fórmula conhecida (funções `ta.*` ou manual de referência) |

Também clonei e apaguei o `pineforge-corpus`, porque ele só traz scripts de teste de motor e nenhuma estratégia da comunidade.

**Links.** O tradingview.com não abre neste ambiente. Por isso a coluna "Link" usa a busca de scripts do TradingView pelo título exato, no formato `https://www.tradingview.com/scripts/search/<título>/`, que ainda não foi confirmado. O título e o autor exatos ficam na coluna "Nome / autor" e permitem achar o script.

**Legenda.** Prioridade **alto** = open-source, regra fechada e não repinta. **Repinta**: "não" = sinal fixo no fechamento do candle; "atraso" = confirmação de pivô com atraso de N candles, que não repinta se o sinal for lido no candle da confirmação (como fizemos no TV07/TV08); "sim" = muda depois do fechamento. **Parente** = regra próxima de algo já testado, mas com mecanismo diferente o bastante para entrar. **DUPLICADA** = a regra central já está no registry e o item foi descartado (lista no fim).

---

## Prioridade ALTA (TV36–TV75)

### Bloco 1: trailing adaptativo da comunidade turca e afins (TV36–TV39) · testado na rodada 4
| ID | Nome / autor | Tipo | Regra central (uma linha) | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV36 | Optimized Trend Tracker (OTT) / KivancOzbilgic (criação de Anıl Özekşi) | indicador | VAR (média tipo VIDYA com CMO de 9 candles) com stop percentual (padrão 1,4%) que só aperta. Compra quando a VAR cruza acima da OTT e vende no cruzamento abaixo. | não | DE `optimized-trend-tracker.ts` | parente do L01 (stop móvel), mas aplicado a uma média adaptativa com distância percentual. PMax, MOST, HOTT-LOTT e Stochastic OTT são variações deste item e não entram. |
| TV37 | AlphaTrend / KivancOzbilgic | indicador | Linha = mínima − ATR×k quando MFI(14) ≥ 50 (ou RSI sem volume), senão máxima + ATR×k, e a linha só anda a favor. Compra quando a AlphaTrend cruza acima do próprio valor de 2 candles atrás. | não | DE `alpha-trend.ts` | parente do L01; a direção vem do MFI, não do preço |
| TV38 | Follow Line Indicator / Dreadblitz | indicador | Fechamento acima da Bollinger(21,1) leva a linha para mínima − ATR(5), sem nunca descer; fechamento abaixo da banda inferior faz o espelho. A tendência vira quando a linha muda de sentido. | não | DE `follow-line.ts` | parente do L01; o gatilho é o rompimento da Bollinger |
| TV39 | Trend Indicator A-V2 (Smoothed Heikin Ashi Cloud) / DZIV | indicador | Médias (EMA) de abertura e fechamento Heikin Ashi. Compra quando o fechamento HA suavizado cruza acima da abertura HA suavizada. | não | DE `trend-indicator-a-v2.ts` | parente do L13. O L13 exige N velas HA sem sombra; aqui a regra é a cor da HA suavizada. |

### Bloco 2: momento duplamente suavizado e pressão (TV40–TV43) · testado na rodada 4
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV40 | True Strength Index (William Blau) / everget e EMB | indicador | TSI = EMA(EMA(Δfech,25),13) / EMA(EMA(\|Δfech\|,25),13). Compra quando cruza acima da linha de sinal EMA(13), de preferência abaixo de 0. | não | EV `oscillators/tsi_true_strength_index.pine` | parente do TV09; é momento, não diferença de médias. Ergodic e Price Momentum Oscillator são variações. |
| TV41 | Trend Trigger Factor / LazyBear (M. H. Pee) | indicador | BP = maior máxima(n) − menor mínima(n)[n], SP espelhado, TTF = 100·(BP−SP)/(0,5·(BP+SP)). Compra quando o TTF cruza acima de +100 e vende abaixo de −100. | não | DE `trend-trigger-factor.ts`, EV `oscillators/trend_trigger_factor.pine` | — |
| TV42 | Trend Continuation Factor (M. H. Pee) / everget | indicador | Soma das variações positivas e negativas com "momentum acumulado". Compra quando +TCF > 0 e −TCF < 0. | não | EV `oscillators/trend_continuation_factor.pine` | — |
| TV43 | Ultimate RSI / LuxAlgo | indicador | Usa o range inteiro quando há nova máxima ou mínima de n candles, senão Δfech. aRSI = média(diff)/média(\|diff\|)·50+50. Compra quando cruza acima da linha de sinal ou de 50. | não | DE `ultimate-rsi.ts` | parente do FX-RSI; o insumo muda (range em expansão) e a regra é cruzamento, não sobrevenda |

### Bloco 3: Ehlers recentes publicados na TASC (TV44–TV47) · testado na rodada 4
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV44 | Reflex & Trendflex (Ehlers, TASC 2020) / e2e4 | indicador | Trendflex = média de (SuperSmoother − SuperSmoother[i]) normalizada por RMS. Compra quando o Trendflex cruza acima de 0 e vende abaixo. | não | DE `reflex-trendflex.ts` | — |
| TV45 | TASC 2026.01 The Reversion Index / PineCodersTASC (Ehlers) | indicador | Razão Σd/Σ\|d\| suavizada (Smooth 8) contra Trigger (4). Compra quando o Smooth cruza acima do Trigger em zona negativa. | não | DE `tasc-2026-01-the-reversion-index.ts` | — |
| TV46 | TASC 2025.06 Cybernetic Oscillator / PineCodersTASC (Ehlers) | indicador | Passa-alta mais SuperSmoother, dividido pelo RMS. Comprado acima de 0 e vendido abaixo (modo "Trend" do artigo). | não | DE `tasc-2025-06-cybernetic-oscillator.ts` | — |
| TV47 | TASC 2025.09 The Continuation Index / PineCodersTASC (Ehlers) | indicador | Transformada de Fisher inversa de 2·(UltimateSmoother − Laguerre)/média. Comprado acima de +0,5, vendido abaixo de −0,5, fora no meio. | não | DE `tasc-2025-09-the-continuation-index.ts` | — |

### Bloco 4: Ehlers clássicos (TV48–TV51) · testado na rodada 4
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV48 | Ehlers Decycler Oscillator / everget | indicador | Diferença entre dois passa-altas (períodos 125 e 100) do preço. Compra quando cruza acima de 0. | não | EV `oscillators/ehlers_decycler_oscillator.pine` | — |
| TV49 | Ehlers Cyber Cycle / everget | indicador | Ciclo extraído com filtro de 2 polos. Compra quando o Cycle cruza acima do Trigger (Cycle[1]). | não | EV `oscillators/ehlers_cyber_cycle.pine` | — |
| TV50 | Ehlers Center of Gravity / everget | indicador | CG = −Σ(i·preço[i])/Σpreço[i]. Compra quando o CG cruza acima do sinal (CG[1]). | não | EV `oscillators/center_of_gravity_oscillator.pine` | — |
| TV51 | Ehlers Roofing Filter / everget | indicador | Passa-alta de 48 mais SuperSmoother de 10. Compra quando cruza acima de 0 (ou acima do próprio valor atrasado de 2 candles). | não | EV `oscillators/ehlers_roofing_filter.pine` | — |

### Bloco 5: fluxo de volume (TV52–TV55) · testado na rodada 5
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV52 | Klinger Volume Oscillator (Stephen Klinger) / everget | indicador | KVO = EMA34 − EMA55 do "volume force". Compra quando o KVO cruza acima do sinal EMA(13), com filtro de tendência opcional. | não | EV `volume/klinger_volume_oscillator.pine` | parente do TV13; o volume force é diferente da ADL |
| TV53 | Chaikin Money Flow (CMF 20) / EMB, versão da comunidade "CMF [Yield]" | indicador | CMF = Σ(MFV,20)/Σ(vol,20). Compra quando cruza acima de +0,05 e vende abaixo de −0,05. | não | F13 `indicators/CMF [Yield]` | parente do TV13. Usa a soma em janela, não EMAs da ADL. |
| TV54 | Ease of Movement (Richard Arms) / EMB | indicador | EMV = ((H+L)/2 − (H+L)[1]/2) / (vol/(H−L)), com SMA(14). Compra quando cruza acima de 0. | não | EMB | — |
| TV55 | Negative Volume Index (Fosback) / everget | indicador | O NVI só muda nos candles de volume menor que o anterior. Comprado com NVI acima da própria EMA(255), fora abaixo. | não | EV `volume/negative_volume_index.pine` | — |

### Bloco 6: Elder e Bill Williams, regras ainda não testadas (TV56–TV59) · testado na rodada 5
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV56 | Elder-Ray (Bull/Bear Power) / EMB "Bull Bear Power" | indicador | Compra quando a EMA(13) sobe e o Bear Power (mín − EMA13) está negativo mas subindo. Venda espelhada com o Bull Power. | não | EMB | parente do TV12 (mesmo autor), mas aqui é pullback, não impulso |
| TV57 | Elder Force Index: pullback / EMB | indicador | Tendência pela EMA(22) subindo. Compra quando o Force Index(2) fica negativo e sai no positivo. | não | EMB | — |
| TV58 | Awesome Oscillator: "saucer" (Bill Williams) / everget | indicador | Com AO > 0, duas barras vermelhas seguidas de uma verde dão compra (espelho para venda). | não | EV `oscillators/awesome_oscillator.pine` | o cruzamento de zero do AO é DUPLICADO do T1, mas o padrão saucer não é |
| TV59 | Accelerator Oscillator (Bill Williams) / everget | indicador | AC = AO − SMA5(AO). Compra com 2 barras verdes seguidas acima de 0 ou 3 abaixo de 0. Venda espelhada. | não | EV `oscillators/accelerator_oscillator.pine` | parente do L14 (mesmo autor, outra regra) |

### Bloco 7: reversão curta e volatilidade (TV60–TV63) · testado na rodada 5
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV60 | Connors RSI (Connors & Alvarez) / EMB | indicador | CRSI = média de RSI(3), RSI(2) da sequência de altas e baixas e PercentRank(100) do retorno de 1 candle. Compra com CRSI < 10 acima da SMA200 e sai com CRSI > 70. | não | EMB; EV `oscillators/stochastic_connors_rsi.pine` (versão estocástica) | parente do L05; o oscilador é composto, não RSI(2) puro |
| TV61 | Double 7's (Connors) / regra do livro, com várias versões na comunidade | estratégia | Acima da SMA200, compra quando o fechamento faz a mínima de 7 candles e sai quando faz a máxima de 7. | não | TV (regra trivial) | parente do L05 e o inverso do T3 (Donchian usado para reversão) |
| TV62 | %b de Connors (3 dias abaixo de 0,2) / regra do livro | estratégia | Acima da SMA200, compra após 3 fechamentos seguidos com %B(20,2) < 0,2 e sai com %B > 0,8. | não | TV (regra trivial) | parente do G3; aqui não espera a volta para dentro da banda |
| TV63 | Mass Index "reversal bulge" (Donald Dorsey) / everget | indicador | Soma(25) de EMA9(H−L)/EMA9(EMA9(H−L)). Quando sobe acima de 27 e depois cai abaixo de 26,5, entra contra a direção da EMA(9). | não | EV `oscillators/mass_index.pine` | — |

### Bloco 8: padrões de barras (TV64–TV67) · testado na rodada 5
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV64 | Three Bar Reversal Pattern / LuxAlgo | indicador | Barra de baixa, depois barra de baixa com máxima e mínima menores, depois barra de alta com máxima acima da primeira. Compra na confirmação (fechamento acima da máxima da barra 1) e invalida abaixo da mínima. | não | DE `three-bar-reversal-pattern.ts` | — |
| TV65 | N Bar Reversal Detector / LuxAlgo | indicador | Generaliza o TV64 para N barras (com fração mínima de barras de baixa). Compra quando o fechamento rompe a máxima do padrão. | não | DE `n-bar-reversal-detector.ts` | variação do TV64; testar junto, no mesmo agente |
| TV66 | Pin Bar Magic v1 / ZenAndTheArtOfTrading (cópia no repositório Alorse) | estratégia | Pin bar (sombra ≥ 66% do range) que fura a EMA rápida, com leque EMA(10/20/50) alinhado. Ordem stop na máxima anterior, cancelada após 3 candles, com trailing por ATR. | não | AL `strategies/other/Pin Bar Magic v1.pine` | parente do L16 (padrão de candle mais tendência), mas é outro padrão |
| TV67 | Rally-Base-Drop Signals / LuxAlgo | indicador | Rally = 2 velas verdes, drop = 2 vermelhas, base = o resto. "Drop-Base-Rally" compra e "Rally-Base-Drop" vende. | não | DE `rally-base-drop-signals.ts` | parente do TV02, porém por fases e não por contagem |

### Bloco 9: rompimento estrutural (TV68–TV71)
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV68 | Breakout Finder / LonesomeTheBlue | indicador | Compra quando uma barra de alta fecha acima da máxima de N candles e de um grupo de ≥ 2 pivôs de alta dentro de uma faixa estreita (Threshold % do range de 300 candles). | atraso (pivôs) | DE `breakout-finder.ts` | parente do TV08. Exige consolidação testada várias vezes. |
| TV69 | Trendlines with Breaks / LuxAlgo | indicador | Linha de tendência a partir do pivô (14) com inclinação ATR×k/n. Compra quando o fechamento rompe a linha de baixa. | **sim no padrão (backpaint=on)**; testar com backpaint=false | DE `trendlines-with-breaks.ts` | o rompimento de linha inclinada é novo. "Pivot Trendlines with Breaks [HG]" (DE `pivot-trendlines-with-breaks.ts`) é variação deste item. |
| TV70 | Darvas Box (Nicolas Darvas) / comunidade | indicador | O topo da caixa é uma máxima de N candles que não é superada nos 3 candles seguintes. Compra quando o fechamento rompe o topo da caixa confirmada e sai quando perde o fundo. | não | DE `darvas-box.ts` | parente do T3. Exige confirmação da caixa, o que o Donchian não faz. |
| TV71 | Range Detector / LuxAlgo | indicador | Detecta lateralidade quando todos os fechamentos de N candles ficam a menos de 1 ATR da SMA. Compra quando o fechamento rompe o topo do range. | não | DE `range-detector.ts` | parente do L11 e do L09 (contração seguida de rompimento), com outra medida |

### Bloco 10: regime estatístico e direcional (TV72–TV75)
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV72 | Change-Point Detection (CUSUM) / LuxAlgo | indicador | CUSUM do z-score dos log-retornos (sPos/sNeg com k e h). Mudança para cima (sPos > h) compra e mudança para baixo vende. | não | DE `change-point-detection.ts` | — |
| TV73 | Random Walk Index (Michael Poulos) / everget | indicador | RWIhigh = (H − L[n])/(ATR·√n) e RWIlow espelhado. Compra quando o RWIhigh cruza acima do RWIlow com valor > 1. | não | EV `oscillators/random_walk_index.pine` | parente do TV22 e do L02 (cruzamento de linhas direcionais), com outra normalização |
| TV74 | Relative Volatility Index (Donald Dorsey) / everget | indicador | RSI calculado sobre o desvio-padrão(10) dos fechamentos que sobem e dos que caem. Compra quando o RVI cruza acima de 50, ou usar como filtro de um sinal de tendência. | não | EV `oscillators/relative_volatility_index.pine` | parente do FX-RSI, mas mede a direção da volatilidade |
| TV75 | Polarized Fractal Efficiency (Hans Hannula) / comunidade | indicador | Eficiência fractal de 10 candles com sinal (+/−), suavizada por EMA(5). Compra quando cruza acima de 0 e vende abaixo. | não | TV | parente do item Kaufman ER da FILA.md; conferir antes de testar |

---

## Prioridade MÉDIA (TV76–TV95)
Também são open-source e não repintam, mas a regra precisa ser escolhida ou montada (o autor não fecha a entrada), o código só existe no TradingView, ou o sistema tem muitas peças.

### Bloco 11: osciladores de zona com filtro (TV76–TV79)
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV76 | Volume Zone Oscillator (Walid Khalil) / LazyBear | indicador | VZO = 100·EMA(vol com sinal)/EMA(vol). Compra quando cruza acima de +40 com ADX > 18 e preço acima da EMA(60), regras do artigo da TASC. | não | TV (LazyBear) | parente do TV13 |
| TV77 | Price Zone Oscillator (Khalil) / LazyBear | indicador | Igual ao VZO, mas com o preço no lugar do volume. Mesma regra de zonas com ADX e EMA(60). | não | TV (LazyBear) | testar no mesmo agente do TV76 |
| TV78 | CM Stochastic POP (Jake Bernstein) / ChrisMoody | indicador | Estocástico entre 40 e 60 que "estoura" acima de 60 dá compra e abaixo de 40 dá venda. É momento, não reversão. | não | DE `stoch-pop-1.ts` | parente do L07 com a lógica oposta (rompimento de zona, não cruzamento em extremo) |
| TV79 | Derivative Oscillator (Constance Brown) / everget | indicador | RSI(14) suavizado duas vezes menos a SMA(9) dele mesmo. Compra quando cruza acima de 0. | não | EV `oscillators/derivative_oscillator.pine` | parente do FX-RSI e do TV09 (é um "MACD do RSI"). Conferir se o agente não vê como duplicado. |

### Bloco 12: sistemas compostos estilo NNFX e forex (TV80–TV83)
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV80 | SSL Hybrid / Mihkel00 | indicador | Baseline (HMA60) com canal de ATR, mais SSL2 para continuação e SSL3 para saída. Compra quando fecha acima do canal da baseline com SSL2 confirmando e sai no cruzamento da SSL de saída. | não | DE `ssl-hybrid.ts` | parente do TV15. A baseline com faixa de ATR e a saída separada mudam o sistema. |
| TV81 | Traders Dynamic Index (Dean Malone) / Goldminds e thienlovv | indicador | RSI(13) com bandas de Bollinger(34; 1,6185). Compra quando a linha de preço (SMA2 do RSI) cruza acima da linha de sinal (SMA7) acima de 50 e dentro das bandas. | não | DE `tdi-rsi.ts` | parente do FX-RSI; o cruzamento das médias do RSI é outra regra |
| TV82 | Absolute Strength Index / Zeiierman (a ASH, Absolute Strength Histogram, é a variante NNFX) | indicador | Retorno do período normalizado entre os percentis de vencedores e perdedores. Compra quando o ASI cruza acima da linha de sinal. | não | DE `absolute-strength-index.ts` | — |
| TV83 | Trendilo / dudeowns | indicador | ALMA da variação % comparada com a banda de RMS. Comprado quando fica acima de +banda, vendido abaixo de −banda. | não | TV | — |

### Bloco 13: aprendizado de máquina open-source (TV84–TV87)
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV84 | Machine Learning: kNN-based Strategy / capissimo | estratégia | Duas variáveis (RSI, CCI ou ROC curto e longo) e rótulo sign(Δfech). Os k vizinhos votam: soma > 0 compra, < 0 vende, com filtro ATR(10) > ATR(40). | não, se o treino for walk-forward | DE `ml-knn-strategy.ts` | parente do TV32 Lorentzian (em teste). Se o TV32 reprovar, rebaixar este item. |
| TV85 | AI Trend Navigator [K-Neighbor] / Zeiierman | indicador | Média kNN do preço com classificador de 10 vizinhos. Compra quando a linha kNN cruza acima da própria média. | não | DE `ai-trend-navigator.ts` | parente do T1 (cruzamento de linhas) e do TV32 |
| TV86 | Machine Learning: Logistic Regression / capissimo | estratégia | Regressão logística do preço contra uma série sintética em janela deslizante. Compra quando a previsão vira para cima. | não | TV | parente do TV32 |
| TV87 | Machine Learning: kNN Trend Predictor / tkarolak | indicador | Curva com média dos vizinhos. Comprado quando a curva fica abaixo do preço. | **sim se look-ahead=on**; usar off | DE `machine-learning-knn-trend-predictor.ts` | baixa dentro do bloco |

### Bloco 14: candle, volume e Renko (TV88–TV91)
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV88 | Full Candle [Alorse] | estratégia | Vela "cheia" (sombras ≤ x% do range) de alta acima da EMA compra; o espelho vende. Alvo curto. | não | AL `strategies/other/Full Candle.pine` | parente do L16 (outro padrão) |
| TV89 | Highest Volume Bar Range / tradeswithashish | indicador | Faixa da barra de maior volume de 75 candles. Compra quando o fechamento rompe a máxima dela, com volume > SMA20 e > volume anterior e fechamento na metade superior do candle. | não | F13 `strategies/Volume Bar Breakout and Breakdown` | parente do TV08 e do T3, mas o nível vem do volume |
| TV90 | Open Close Cross Strategy R5.1 / JustUncleL | estratégia | Média (SMMA/DEMA etc.) do fechamento contra a média da abertura. Compra quando a média do fechamento cruza acima da média da abertura. | não (versão NoRepaint) | DE `open-close-cross.ts` | parente do TV39 (cor de vela suavizada) e do T1. Conferir. |
| TV91 | Renko ATR overlay (troca de tijolo) / LonesomeTheBlue | indicador | Tijolos Renko de tamanho ATR desenhados sobre candles normais. Compra quando aparece o 1º (ou 2º) tijolo de alta depois de tijolos de baixa. | não sobre candles normais (o gráfico Renko nativo do TV repinta) | DE `renko-candles-overlay.ts`, `renko-flip-alert.ts` | parente do L01 (reversão por distância fixa) |

### Bloco 15: ciclos, telas múltiplas e perfil (TV92–TV95)
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV92 | Ehlers Sinewave (Even Better Sinewave) / comunidade e LazyBear | indicador | Compra quando a Sine cruza acima da LeadSine (modo ciclo) e só opera quando o ciclo é válido. | não | TV | — |
| TV93 | Elder Triple Screen / comunidade | estratégia | Tela 1: inclinação do histograma MACD no tempo gráfico maior (H4 ou D). Tela 2: Force Index(2) < 0. Tela 3: stop de compra na máxima anterior. | não, se o tempo gráfico maior usar candle fechado | TV | parente do TV12 e do TV57; testar depois deles |
| TV94 | Volatility Quality Index (Thomas Stridsman) / Alpha Extract | indicador | True range com o sinal da vela, suavizado. Compra quando o VQI vira para cima e cruza a própria média. | não | DE `volatility-quality.ts` | — |
| TV95 | Market Profile: regra dos 80% / LonesomeTheBlue (perfil), regra de Dalton | estratégia | Se o dia abre fora da value area (70%) do dia anterior e fecha 2 candles H1 dentro dela, o alvo é o outro extremo da value area. | não | DE `market-profile.ts` | parente do L15 e do G4 (nível do dia anterior), mas com nível de perfil |

---

## Prioridade BAIXA (TV96–TV103)
Pouca amostra, regra pouco definida, filtro sem sinal próprio ou código só no TradingView.

### Bloco 16: específicos do BTC (TV96–TV99)
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV96 | Bitcoin Mayer Multiple / sito4713 (Trace Mayer) | indicador | MM = fechamento/SMA200 diária. Compra com MM < 1 (ou < 0,8) e vende com MM > 2,4. | não | DE `bitcoin-mayer-multiple.ts` | poucos sinais; parente do Z-score da FILA.md |
| TV97 | CME Gap (BTC) / várias versões na comunidade | indicador | Gap entre o fechamento de sexta 21h UTC e a abertura de domingo 23h UTC no spot. Opera o fechamento do gap na semana. | não | TV; não achei código open-source confiável | parente do item "efeito fim de semana" da FILA.md; conferir |
| TV98 | Bitcoin Pi Cycle Top & Bottom / Commandoum (Philip Swift) | indicador | SMA111 cruza acima de 2×SMA350 e marca topo. A versão z-score também marca fundo. | não | DE `bitcoin-pi-cycle-top-bottom-indicator-z-score.ts` | só 3 ou 4 sinais na história, sem poder estatístico |
| TV99 | Weis Wave Volume / LazyBear | indicador | Volume somado por onda. Compra quando a onda de alta tem volume maior que a onda de alta anterior e o preço rompe a máxima da onda. A regra foi montada; o autor não a fecha. | não | DE `weis-wave-volume-lazybear.ts` | — |

### Bloco 17: diversos (TV100–TV103)
| ID | Nome / autor | Tipo | Regra central | Repinta | Código | Duplicidade |
|---|---|---|---|---|---|---|
| TV100 | Better Volume Indicator / LazyBear | indicador | Barra de clímax (volume × range máximo de 20) contra a tendência marca reversão. Regra montada. | não | DE `better-volume.ts` | — |
| TV101 | Rex Oscillator / comunidade NNFX | indicador | TVB = 3·fech − (mín+abert+máx), somado e suavizado. Compra quando cruza acima do sinal. | não | TV | — |
| TV102 | Damiani Volatmeter / comunidade (Luis Damiani) | indicador (filtro) | ATR(7)/ATR(50) contra o desvio-padrão. Só libera sinais quando a volatilidade "acorda". Testar como filtro de um item já CANDIDATA. | não | TV | filtro, não estratégia |
| TV103 | Swing Breakout Sequence / LuxAlgo | indicador | Sequência de 5 pontos de swing dentro do range A-B. Compra quando o fechamento rompe A depois da sequência de alta. | atraso (swings) | DE `swing-breakout-sequence.ts` | parente da Market Structure da FILA.md e do TV33 |

---

## Descartados: DUPLICADA, já na FILA.md, em teste ou repintam (66 linhas)

Cada linha diz qual regra do `registry.json` (ou da fila atual) já cobre o item. Mudar a série de entrada, o tipo de média ou o multiplicador não torna a regra nova.

| Nome / autor | Código | Motivo |
|---|---|---|
| UT Bot Alerts / QuantNomad (Yo_adriiiiaan) | DE `ut-bot.ts` | DUPLICADA do L01: stop móvel de ATR que vira com o fechamento |
| SuperTrend AI (Clustering) / LuxAlgo | DE `supertrend-ai-clustering.ts` | DUPLICADA do L01: Supertrend com multiplicador escolhido por k-means, que só troca o parâmetro |
| Pivot Point SuperTrend / LonesomeTheBlue | DE `pivot-point-supertrend.ts` | DUPLICADA do L01 (centro no pivô em vez de hl2) |
| Nick Rypock Trailing Reverse (NRTR) / everget | EV `trailing_stops/nrtr_nick_rypock_trailing_reverse.pine` | DUPLICADA do L01 (trailing-and-reverse) |
| Trailing Stop Loss (ATR) / KivancOzbilgic | DE `trailing-stop-loss-indicator-by-k-van-fr3762.ts` | DUPLICADA do L01 |
| SwingArm ATR Trend (Blackflag FTS) / vsnfnd | DE (lista dos mais curtidos) | DUPLICADA do L01 |
| SuperTrend Oscillator / LuxAlgo | DE `supertrend-oscillator.ts` | DUPLICADA do L01 (mesma virada, mostrada como oscilador) |
| ST0P / KivancOzbilgic | DE `st0p.ts` | DUPLICADA do L01 (stop percentual) |
| PMax, MOST, HOTT-LOTT, Stochastic OTT, OTT Bands / KivancOzbilgic | DE `profit-maximizer.ts`, `most-*.ts`, `hott-lott.ts`, `stochastic-ott.ts`, `ott-bands.ts` | variações internas do TV36 (OTT); só testar se o TV36 passar |
| Chandelier Exit / everget | EV `trailing_stops/chandelier_exit.pine` | JÁ NA FILA.md (Chandelier Exit) |
| Trend Trader Strategy (Andrew Abraham) / HPotter | DE `trend-trader.ts` | JÁ NA FILA.md: é um Chandelier (máxima de n − k·ATR) |
| Twin Range Filter / colinmck e KivancOzbilgic | DE `twin-range-filter.ts` | DUPLICADA do TV14 (dois Range Filters somados) |
| Range Filter 5min (guikroth) / PHVNTOM_TRADER | DE `range-filter-buy-sell-5min.ts` | DUPLICADA do TV14 |
| Gann High Low / KivancOzbilgic | DE `gann-high-low.ts` | DUPLICADA do TV15 (SMA das máximas e mínimas) |
| Target Trend / BigBeluga | DE `target-trend.ts` | DUPLICADA do TV15 e do L12 (SMA das máximas e mínimas ± ATR) |
| Zero Lag Trend Signals (MTF) / AlgoAlpha | DE (lista dos mais curtidos) | DUPLICADA do L12 (ZLEMA ± ATR, rompimento de faixa) |
| Volumatic VIDYA / BigBeluga | DE `volumatic-variable-index-dynamic-average.ts` | DUPLICADA do L12 (média ± ATR, rompimento de faixa) |
| Pretty Good Oscillator (Mark Johnson) / everget | EV `oscillators/pretty_good_oscillator.pine` | DUPLICADA do L12: (fech − SMA)/ATR > 3 é o rompimento de um Keltner |
| Bollinger Breakout [kodify] e BB Divergence [Alorse] | AL `mean-reversion/*.pine` | DUPLICADA do L12 (rompimento de canal de volatilidade) |
| Squeeze Momentum Indicator / LazyBear (nº 1 em curtidas) | DE `squeeze-momentum.ts` | DUPLICADA do L09 (TTM Squeeze) |
| Squeeze Momentum V2 / KivancOzbilgic e outros | DE `squeeze-momentum-indicator-version2-by-k-van.ts` | DUPLICADA do L09 |
| QQE MOD / Mihkel00 | DE `qqe-mod.ts` | DUPLICADA do TV17 |
| VuManChu Cipher B + Divergences | DE `market-cipher-b.ts` | DUPLICADA do TV16 (núcleo WaveTrend) |
| Market Cipher B Free / falconCoin | DE `market-cipher-b-free-version-with-buy-and-sell.ts` | DUPLICADA do TV16 |
| STC Indicator, A Better MACD / shayankm | DE (lista dos mais curtidos) | DUPLICADA do TV18 |
| CM MACD Custom MTF / ChrisMoody (nº 3 em curtidas) | DE `cm-macd-custom-mtf.ts` | DUPLICADA do TV09 |
| MACD-V / Spiroglou e Kivanc; MACD Leader / LazyBear | DE `macd-v.ts`, `macd-leader.ts` | DUPLICADA do TV09 (o cruzamento continua de MACD) |
| Omar MMR [Alorse] | AL `other/Omar MMR [Alorse].pine` | DUPLICADA do TV09 (cruzamento do MACD com filtros de EMA e RSI) |
| Kalman Trend Levels / BigBeluga | DE `kalman-trend-levels.ts` | DUPLICADA do T1 (filtro rápido contra filtro lento) |
| Super Guppy, CM Guppy, GMMA / JustUncleL, ChrisMoody | DE `super-guppy.ts`, `cm-guppy-ema.ts` | DUPLICADA do T1 (alinhamento de médias) |
| Madrid MA Ribbon e Madrid Trend Squeeze | DE `madrid-ma-ribbon.ts`, `madrid-trend-squeeze.ts` | DUPLICADA do T1 |
| Elliott Wave Oscillator / LazyBear e dgtrd; cruzamento de zero do AO | DE `elliott-wave-oscillator-lazybear.ts` | DUPLICADA do T1 (SMA5 − SMA35) |
| TRAMA / LuxAlgo; Signal MA / LuxAlgo | DE `trama.ts`, `signal-ma.ts` | DUPLICADA do T1 (preço ou média contra média) |
| MavilimW / KivancOzbilgic; MA Sabres / LuxAlgo | DE `mavilimw.ts`, `ma-sabres.ts` | DUPLICADA do TV20 (virada da inclinação de uma média) |
| Ehlers Instantaneous Trendline / LazyBear | DE `ehlers-instantaneous-trend.ts` | DUPLICADA do TV20 (filtro contra o próprio valor atrasado) |
| Nadaraya-Watson Envelope / LuxAlgo | DE `nadaraya-watson-envelope.ts` | **repinta** (suavizador não causal); a versão sem repintura é DUPLICADA do G3 |
| Mean Reversion Channel / fareidzulkifli | DE `mean-reversion-channel.ts` | DUPLICADA do G3 (volta da banda para dentro) |
| Flawless Victory / Bunghole (cópia no Alorse) | AL `other/Flawless Victory.pine` | DUPLICADA do G3 (Bollinger mais RSI/MFI) |
| Stochastic RSI (cruzamento %K/%D) | EMB | DUPLICADA do L07 (mesma regra, só muda a série de entrada) |
| SMI (UCSgears) e KDJ | DE `smi-ucs.ts`, `kdj.ts` | DUPLICADA do L07 |
| Inverse Fisher Transform RSI / KivancOzbilgic | DE `ift-stoch-rsi-cci.ts` | DUPLICADA do FX-RSI (cruzar ±0,5 = RSI suavizado em zona) |
| Chande Momentum Oscillator / everget | EV `oscillators/chande_momentum_oscillator.pine` | DUPLICADA do FX-RSI (CMO = 2·RSI − 100 com somas simples) |
| Double RSI e RSI + 1200 [Alorse]; Intraday Momentum Index; RMI | AL `momentum/*.pine`; EV | DUPLICADA do FX-RSI (RSI em zona com filtro) |
| CM RSI-2 Strategy / ChrisMoody | DE `cm-rsi-2-lower.ts` | DUPLICADA do L05 |
| CM Sling Shot / ChrisMoody; Scalping PullBack Tool / JustUncleL; Granville Entry Guide | DE `cm-sling-shot.ts`, `scalping-pullback-tool.ts`, `granville-entry-guide.ts` | DUPLICADA do T2 e do G1 (pullback para a EMA na tendência) |
| Support and Resistance Levels with Breaks / LuxAlgo | DE `sr-levels-breaks.ts` | DUPLICADA do TV08 (rompimento do último pivô, filtro de volume) |
| Isolated Peak & Bottom (Tuncer Şengöz) / KivancOzbilgic | DE `isolated-peak-bottom.ts` | DUPLICADA do L14 e do TV08 (fractal de 5 barras com confirmação) |
| Swing Failure Pattern / LuxAlgo; ICT Turtle Soup; Liquidity Swings | DE `swing-failure-pattern.ts` | DUPLICADA do G4 (fura o extremo e fecha de volta) |
| ORB, Initial Balance Breakout, Ultimate ORB, Asian Session Range | DE `ultimate-opening-range-breakout.ts`, `initial-balance-breakout-signals.ts` | DUPLICADA do G2 |
| NR4 & NR7 with Breakouts / LuxAlgo | DE `nr4-nr7-with-breakouts.ts` | DUPLICADA do L11 |
| Camarilla, R-Breaker e CPR (pivôs diários) | TV | DUPLICADA do L15 (níveis do dia anterior) |
| Dual Thrust | TV | DUPLICADA do L10 (abertura ± k·range) |
| Donchian Trend Ribbon / Turtle 20/55 | TV | DUPLICADA do T3 |
| Session Streaks / LuxAlgo | DE `session-streaks.ts` | DUPLICADA do TV02 (sequência de candles ou sessões) |
| Divergence for Many Indicators / LonesomeTheBlue; Price Divergence Detector / JustUncleL; RSI Divergence | DE `price-divergence-detector.ts` | DUPLICADA do G5 |
| Market Structure Trailing Stop / LuxAlgo | DE `market-structure-trailing-stop.ts` | EM TESTE: o TV33 (SMC BOS/CHoCH) tem a mesma virada por CHoCH |
| Smart Money Concepts / LuxAlgo (nº 2 em curtidas) | DE `smart-money-concepts-luxalgo.ts` | EM TESTE (TV33) |
| Lorentzian Classification / jdehorty; HalfTrend / everget; Coral, McGinley, Gaussian, Trend Magic, Waddah, Impulse MACD, VFI, Vix Fix, Andean | DE e EV | EM TESTE (TV24–TV35) |
| Order Block Detector, Fair Value Gap, ICT Silver Bullet / LuxAlgo | DE `order-block-detector.ts`, `fair-value-gap-luxalgo.ts`, `ict-silver-bullet.ts` | JÁ NA FILA.md (Order block / FVG); o Silver Bullet só acrescenta uma janela horária |
| Higher High Lower Low Strategy / LonesomeTheBlue | DE (lista dos mais curtidos) | JÁ NA FILA.md (Market Structure) |
| EMA Moving away [Alorse]; Disparity e Kairi | AL `trend/EMA Moving away Strategy [Alorse].pine`; EV | JÁ NA FILA.md (Z-score contra a média) |
| Laguerre RSI, DeMarker, Coppock, TRIX, KAMA, Ehlers MAMA, TII, VHF e Choppiness | EV `oscillators/*.pine`, `movings/*.pine` | JÁ NA FILA.md |
| Reversal Signals / LuxAlgo | DE `reversal-signals.ts` | JÁ NA FILA.md (contagem tipo TD Sequential) |
| Heikin Ashi Strategy V2 [FAKE] e Javo v1 [Repaint] / Alorse | AL | **repintam** (`lookahead_on`); descartados |
| ZigZag (RicardoSantos, LonesomeTheBlue, Trendoscope) e Auto Fib | DE | **repintam** (a última perna muda) |
| Hash Ribbons, Global Liquidity/M2, Open Interest, Liquidations, CVD | DE | precisam de dados externos ou por tick que não temos |

## Resumo da fila
- **68 itens novos** em 17 blocos de 4, de TV36 a TV103: 40 de prioridade alta (TV36–TV75), 20 de média (TV76–TV95) e 8 de baixa (TV96–TV103). O código de 50 deles já está clonado (Pine original ou port fiel: DE, EV, AL, F13). Outros 3 são indicadores embutidos com fórmula pública, e 15 só existem no TradingView ou como regra de livro.
- **66 linhas de descarte**, que cobrem mais de 90 scripts populares: 51 DUPLICADAS do registry, 1 grupo de variações internas do TV36, 7 já na FILA.md, 3 em teste em TV24–TV35, 3 que repintam e 1 que depende de dados externos. Contando as duas listas, são 134 itens catalogados.
- **Ordem sugerida:** blocos 1 a 10 primeiro. Antes de abrir cada bloco, conferir o `registry.json` de novo, porque os resultados de TV24–TV35 podem transformar mais itens em duplicados (por exemplo, o TV84–TV87 depende do TV32 Lorentzian).
