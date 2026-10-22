---
name: ferramentas-pesquisa
description: Use antes de qualquer trabalho de pesquisa de estratégias de trading no TraderNova (dados históricos, backtest, calibração, validação, triagem de scripts do TradingView, estatística de overfitting). Diz qual ferramenta, biblioteca, skill ou MCP usar em cada função e como adotar uma nova sem pedir ao usuário.
---

# Ferramentas da pesquisa

O usuário pediu que a escolha de ferramentas seja automática: você decide qual usar, usa, e registra. Não pergunte
"qual biblioteca usar?" nem "posso instalar X?" quando a resposta estiver nas regras abaixo.

## 1. Consulte o mapa

Leia `research/ferramentas/README.md`. A tabela "função → ferramenta" é a fonte da verdade. Se a função que você
precisa está lá, use a ferramenta indicada. Atalhos:

- Dados de cripto (spot ou perpétuo, funding, open interest): `research/ferramentas/dados_binance.py`.
  A rede da nuvem bloqueia `data.binance.vision`; o script cai no espelho S3 sozinho. Não tente Yahoo, Kaggle,
  Hugging Face, CoinGecko nem APIs de corretora: estão bloqueados.
- Validar uma estratégia: skill `validar-estrategia` (pipeline `research/ferramentas/validar.py`).
- Só a estatística sobre resultados que você já tem: `research/ferramentas/estatistica.py`
  (`pbo`, `dsr`, `psr`, `min_trl`, `spa`, `mcpt`, `bootstrap_trades`, `cpcv`, `walk_forward`, `checar_lookahead`).
- Backtest por trade com stop e alvo: motor do laboratório (`research/lab/engine.py`). Backtest por posição com
  funding: `research/ferramentas/backtest.py`.
- Revisar um resultado antes de chamá-lo de bom: agente `revisor-cetico`.

## 2. Função sem ferramenta no mapa

Delegue ao agente `curador-ferramentas` (ou faça você mesmo, seguindo o mesmo método) e siga em frente com a
recomendação dele. Ele escolhe, instala com versão fixada, escreve um teste mínimo e atualiza o mapa. O usuário
só é consultado se a ferramenta custar dinheiro, pedir chave/conta, ou puder enviar ordens.

## 3. Regras fixas

- Nada que envie ordens, consulte conta ou peça chave de corretora. MCPs só com escopo de dados de mercado.
- Licença permissiva para qualquer coisa que possa ir ao app. AGPL/GPL só em script offline, anotado no mapa.
- Versão fixada em `research/ferramentas/requirements.txt`.
- Se reescrever cabe em ~50 linhas com teste, reescreva em vez de puxar dependência.
- Skills ou repositórios de terceiros com scripts: leia o código antes de rodar e fixe o commit.
- Toda adoção, troca ou descarte entra na tabela do README no mesmo commit, com o motivo.
- Não edite arquivos nem ramos de outra frente; ofereça a ferramenta por mensagem.
