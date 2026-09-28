# N4: rotação relativa semanal BTC/ETH/SOL spot

Data: 28/09/2026. **Reprovada na triagem histórica; não validada e não candidata a forward.** Uma única regra foi registrada antes da execução; nenhum parâmetro foi ajustado após os resultados.

## Hipótese e diferença

N4 usa *momentum transversal*: a cada fechamento de domingo 23h UTC, compara os retornos dos sete dias completos de BTC, ETH e SOL, compra na abertura seguinte apenas o mais forte se o retorno for positivo e fica em caixa caso contrário. Rebalanceia na segunda seguinte e usa stop adverso de 8% do preço de entrada preenchido. É uma carteira spot comprada em **um ativo**, sem regressão, beta, hedge ou spread de duas pernas como N1. Também não usa EMA, pullback, Donchian, POC, zona, abertura de sessão, sinais de ouro/FX ou calendário de exposição fixo como N3. O estudo primário de [Drogen, Hoffstein e Otte](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4322637) investiga momentum transversal em cripto com horizontes diferentes; não comprova esta regra de sete dias em três moedas. [Han, Kang e Ryu](https://papers.ssrn.com/sol3/papers.cfm?abstractid=4675565) destacam a fragilidade do efeito sob premissas realistas, motivo para exigir resultado líquido e stress.

## Protocolo anterior aos resultados

O [protocolo N4](protocol-N4.json) fixou os três ativos, o retorno simples de 168 barras H1 contíguas e já **fechadas**, ranking domingo 23h, entrada no open de segunda 00h, stop 8%, capital spot integral sem alavancagem e nenhuma otimização. Empates seguem a ordem BTC, ETH, SOL. Se qualquer histórico semanal estiver incompleto, não há entrada. Em troca semanal, cobram-se venda e nova compra mesmo se o vencedor não mudar. No stop, execução no nível ou no open pior após gap; após stop, caixa até a próxima segunda. Lacuna de dados com posição aberta exige liquidação na primeira abertura observada. A única lacuna do cache está em 24/03/2023 13h UTC; nenhum candle foi inventado.

Fonte: caches Binance Spot H1 do projeto, auditados por SHA-256 do manifesto local e pelos [arquivos oficiais da Binance](https://github.com/binance/binance-public-data/blob/master/README.md). Abrangência 01/12/2021–31/08/2026. BTC SHA `eec6d00f0a38d5658b16c53928aed72cea3f1c925c8c73850ea75888c2ced678`; ETH `e476a43feed4716a833cbccfc6061816d19e722a8e439da0b8ff0b90f56a1ff3`; SOL `33393a1c43d34808db5755e905f3c3205eb836bbff9728e047830f894bd235f4`. Base: taxa 10 bps e slippage adverso 2 bps por execução; stress: 15 + 5 bps por execução. Patrimônio e drawdown são marcados a cada fechamento H1 com liquidação estimada; perdas intrabar podem exceder o drawdown registrado.

Janelas fixas como N3: desenvolvimento 2022–2024 (também por ano), validação 2025, final retrospectivo jan–ago/2026. Mínimos **inalterados**: 2/3 anos de desenvolvimento positivos, 140/45/25 negócios em desenvolvimento/validação/final, retorno base e stress positivo em validação e final, PF ≥1,20 e DD ≤20% em ambas. N4 tem uma única carteira, portanto o critério de 2/3 ativos independentes de N3 não se aplica; os demais limites não foram relaxados. O recorte final já foi usado em pesquisas anteriores do projeto: não é holdout intocado entre hipóteses.

## Resultados líquidos da carteira

| Recorte | Operações | Base | Stress | PF base | DD base |
| --- | ---: | ---: | ---: | ---: | ---: |
| Desenvolvimento 2022–2024 | 98 | +242,98% | +180,23% | 1,28 | 50,79% |
| Validação 2025 | 33 | −6,35% | −10,82% | 0,95 | 37,72% |
| Final retrospectivo jan–ago/2026 | 20 | −18,59% | −21,09% | 0,64 | 27,25% |

O desenvolvimento variou: 2022 +14,22%, 2023 +269,98%, 2024 −10,03% (base), com drawdowns anuais de 24,30%, 26,31% e 50,79%. O resultado agregado forte depende de 2023 e não se sustentou depois. Em 2025, houve 51 oportunidades semanais avaliadas, mas só 33 retornos vencedores positivos; no final, 34 semanas e 20 entradas. A seletividade deixa a amostra **abaixo dos mínimos**. Todos os critérios de validação e final de retorno, PF e DD falharam. Não há candidatura a forward.

## Reprodução e limites

Arquivos reproduzíveis nesta pasta do repositório: `run-rotation.mjs`, `screen-N4.json`, `result-N4.json`. Executar `node research/rotation/run-rotation.mjs --self-test`, depois `--phase=screen` e `--phase=final`. A fase final exige hashes imutáveis do protocolo e dos três caches iguais aos da triagem. O autoteste verifica ranking após fechamento, entrada na próxima abertura, as duas cobranças, stop em gap adverso e mudança de liderança pelo último close concluído. Resultado: `historicalScreenPass:false`, `validated:false`, `forwardPassed:false` e `holdoutUntouched:false`. Custos são cenários fixos, não uma medição de spreads/ordens executáveis da conta; não foram avaliados MT5/the5, limites diários da mesa, indisponibilidade de corretora nem operação prospectiva.
