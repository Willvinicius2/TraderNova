# Calibração H1 v2

Solicitada após o usuário observar que as estratégias iniciais eram ruins. O escopo continua sendo pesquisa: nenhuma aprovação para operar e nenhuma mudança na corretora. Usa a amostra Binance já verificada; não houve compra de dados, troca de fonte, redução de custos simulados ou aumento de risco para melhorar a apresentação.

## Procedimento reproduzível

Protocolo fixado em `research/calibration-protocol.json` antes da primeira execução. A grade tem 27 variantes (nove por família), avaliadas igualmente nos três ativos. Não houve segunda busca guiada pelos resultados finais. Reproduzir: `npm run research:calibrate`, após baixar os arquivos com `npm run research:download` se o cache estiver ausente.

Entradas originais, filtro EMA200/tendência/custo, ou alternativa paciente (T1 EMA20/50; T2 RSI até60; T3 canal55). Saídas originais, 2ATR/2R/24h ou 3ATR/3R/72h. Custo mínimo do stop fixo em 0,72% do preço para os perfis filtrados; corresponde a três vezes 24bps de custo estimado de ida e volta. Aumentar custos no stress não muda os sinais ou o filtro. Risco continua 0,5%; compras spot sem alavancagem.

Ranking apenas nos dois semestres do desenvolvimento set/2024–ago/2025, por ativo: mediana dos seis retornos menos 0,25 vezes o pior drawdown. Mínimo de cinco trades em cada célula e 60 agregados. Um perfil por família, comum aos três ativos. A seleção é gravada em `research/calibration-selection.json` antes de abrir a validação/final. Para adotar na **simulação**, precisa superar o controle no desenvolvimento e melhorar a validação em pelo menos dois ativos e na média. Logo, a validação também participa da seleção para adoção; só o período final fica fora desta decisão.

Todos esses períodos já haviam sido examinados anteriormente. A calibração é exploratória e retrospectiva; não oferece uma nova amostra independente. Os ativos são correlacionados e 27 variantes aumentam o risco de sobreajuste. Os critérios de aprovação antigos permanecem, incluindo 100 trades por janela. Os filtros de seleção com cinco/60 trades não substituem esses critérios. Indicadores com EMA200 exigem 600 candles anteriores nas janelas históricas; os arquivos H1 têm um mês completo de aquecimento. Na fonte ao vivo, o mesmo filtro aguarda 600 candles fechados.

## Decisão desta rodada

- **T1:** ajuste testado, mas não adotado; melhorou somente um ativo na validação. Permanece EMA9/21, stop1,5ATR, alvo2R e até8h. Seus ganhos no período final não foram usados para inverter essa decisão.
- **T2:** stop3ATR, alvo3R e até72h; entrada original preservada. Adotado apenas para pesquisa por reduzir perdas de validação em todos os ativos. Seu score no desenvolvimento ainda é negativo; continua perdedor.
- **T3:** Donchian20 e EMA50, mais fechamento/EMA50 acima da EMA200 crescente em24h; stop3ATR, alvo3R e até72h; filtro de custos. Adotado apenas para pesquisa. Fica em destaque por ter a melhor média de validação entre os perfis adotados, não por escolher o melhor ativo na avaliação final.

Resultados completos: `research/CALIBRACAO.md` e `public/research/calibration.json`. Todos os trades, inclusive controles, em `public/research/calibrated-*.json`. O estudo original permanece publicado. As nove células selecionadas continuam sem aprovação; a T3 tem somente 31–36 operações na avaliação final, BTC falha no stress e SOL teve validação negativa.

## Integração e sessões

`active-presets.ts` é gerado pelo script a partir das regras de adoção. Backtest de um clique, monitor de pesquisa e evidências do Robô usam esse registro. Valores não ficam editáveis na interface. O Robô continua sem estratégias autorizadas; uma aprovação futura deve corresponder ao identificador exato do preset, fonte, ativo e período.

Cada sessão nova grava o identificador do preset. Sessões anteriores são restauradas; posições abertas continuam usando seus níveis e prazo já registrados. Enquanto o preset estiver desatualizado, não há novas entradas. Depois de terminar a posição, iniciar a versão calibrada arquiva a sessão anterior, sem apagar trades. O histórico antigo pode ser exportado. As pesquisas não se misturam numa mesma curva.

Testes: equivalência exata dos controles, causalidade das27variantes, seleção pelos resultados de desenvolvimento, adoção apenas pela regra da validação, filtros fixos no stress, alvo/prazo novos na simulação e aprovação vinculada à versão. A revisão independente também confirmou hashes, métricas e resultados originais.
