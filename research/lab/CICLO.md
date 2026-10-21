# Ciclo automático do laboratório

Roteiro de cada rodada automática (o Claude segue isto a cada disparo agendado).

1. `git pull` no ramo do laboratório; se não houver dados em `research/cache/lab`, clonar o Bitstamp e rodar `data.py` (instruções no topo do arquivo).
2. Ler `FILA.md`, `registry.json` e o último `RODADA_N.md`. Escolher os próximos itens não marcados que não repetem nada do registro.
3. Lançar 4 agentes de estratégia (4 estratégias cada) + 1 agente de dados, com as mesmas regras da rodada 2 (`protocol.json` lab-v2, `status.py`, notas em `notes/rN-*.md`).
4. Ao fim: `diagnose.py`, `report.py --round N`, `export_dashboard.py`, atualizar o painel, escrever `RODADA_N.md`, marcar a fila, commit e push.
5. Candidatas novas e antigas: rodar em todo ativo novo que o agente de dados trouxer, com os mesmos parâmetros (sem recalibrar).
6. Mandar ao Will um resumo curto (o que passou, o que falhou, placar acumulado). Se a meta de `FILA.md` for atingida, avisar com destaque.
