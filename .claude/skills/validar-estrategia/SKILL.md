---
name: validar-estrategia
description: Use quando for testar, validar, aprovar ou reprovar uma estratégia ou hipótese de trading no TraderNova. Protocolo fixo — pré-registro, lookahead, walk-forward, CPCV, PBO, Deflated Sharpe, SPA, MCPT, bootstrap, estresse e reserva — com veredito por regra, nunca por opinião.
---

# Validar uma estratégia

O veredito sai de `research/ferramentas/portoes.json`, não da sua impressão. Não mude um portão depois de ver
um resultado; se um limite estiver errado, mude em nova versão, com motivo no README, antes da próxima hipótese.

## Passo a passo

1. **Dados.** `python research/ferramentas/dados_binance.py <SÍMBOLOS> --spot` se `research/cache/binance/` não
   tiver os arquivos. Confira lacunas no manifesto.
2. **Escreva a hipótese** em `research/ferramentas/hipoteses/<ID>.py` (modelo: `H01_donchian_ensemble.py`):
   `ID`, `NOME`, `FONTE` (artigo, livro ou script, sempre citado), `FREQ`, `ATIVOS`, `GRADE` e
   `posicao(df, **params)`. A grade é fixada AGORA e não muda depois de rodar. Grade pequena: cada variante
   aumenta o N do Deflated Sharpe.
3. **Rode** `python research/ferramentas/validar.py <ID> --rapido` para checar o código e depois sem `--rapido`.
   O primeiro uso registra o hash em `tentativas.jsonl` (pré-registro). Mudou o arquivo? Novo hash, nova tentativa,
   N maior: é assim que tem de ser.
4. **Leia `resultados/<ID>.json`.** O veredito é a primeira reprovação na ordem dos portões. Reporte sempre o lado
   comprado e o vendido separados (`walkForward.porLado`) e o efeito do funding (`estresse.semFunding`).
5. **Revisão cética.** Passe o JSON ao agente `revisor-cetico` antes de chamar qualquer resultado de bom.
6. **Reserva.** Só com `PASSOU_DESENVOLVIMENTO` e só uma vez: `--abrir-reserva`. Fica registrado; não reabre.
7. **Registre** a conclusão em uma linha no relatório da frente e faça commit do JSON, da hipótese e de
   `tentativas.jsonl` juntos.

## Estratégias que já existem em outro motor

Para o motor do laboratório (resultado em R por trade), gere a matriz T×N de retornos por barra de todas as
variantes da grade e chame `estatistica.pbo`, `estatistica.dsr` (N = `nHistorico` do portoes.json + tamanho da
grade), `estatistica.spa` e `estatistica.bootstrap_trades` direto. Converta R em fração da conta com o risco por
operação usado (ex.: 0,5%).

## Não faça

- Escolher a "melhor" variante olhando o fora da amostra.
- Rodar de novo com outra grade e esquecer a tentativa anterior: tudo conta no N.
- Aprovar por soma de pontos ("passou em quase tudo"). Um portão reprovado reprova.
- Apresentar resultado de desenvolvimento como se fosse da reserva.
