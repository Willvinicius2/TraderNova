@AGENTS.md

## Pesquisa de estratégias

- Antes de qualquer trabalho de pesquisa (dados históricos, backtest, calibração, validação, triagem de scripts), use a skill `ferramentas-pesquisa`: ela diz qual ferramenta usar em cada função. O mapa fica em `research/ferramentas/README.md`.
- Função sem ferramenta no mapa: o agente `curador-ferramentas` escolhe, adota e registra sem perguntar ao usuário (exceto se custar dinheiro, pedir chave ou puder enviar ordens).
- Validar ou reprovar estratégia: skill `validar-estrategia`. Antes de chamar um resultado de bom: agente `revisor-cetico`.
