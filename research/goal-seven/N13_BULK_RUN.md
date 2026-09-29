# N13: rodada histórica ampliada

Iniciada no PC em **2026-09-29 01:41:39 UTC** (28/09, 22:41:39 em São Paulo), PID **24080**, processo Python com janela oculta. O horário é o relógio local, que está aproximadamente 33 segundos adiantado em relação à calibração pública; não é prova de publicação histórica.

Código preservado no commit `c8e5a35d7c774ba851b1231f1552f73f3300d09b`. SHA-256 de `scripts/download-goal-options-trades-v2.py`: `04e6ce00384be21052fb406a381b46f6cd18a53adb7e0dabbd033924f5c261e3`. A rodada começou no snapshot piloto `2a9e16fa3654b2a7a4198d27697a4179169be850400f9fd9d0326ca50a12a860`.

Limites: 15.000 consultas públicas, 20.000.000.000 bytes brutos, 43.200 segundos, intervalo mínimo de um segundo e teto conjunto de cache dos negócios de 5.000.000.000 bytes. A primeira condição atingida encerra a rodada; erros, bloqueio HTTP, estado inconsistente e marcador STOP também interrompem. Não há ordens, autenticação ou contratação de dados. O processo depende de o PC e a rede continuarem disponíveis.

Recibo de lançamento e logs: `research/cache/goal-seven/options-trades-v2/bulk-20260929T014139Z.launch.json`, `.stdout.log` e `.stderr.log`, preservados fora do Git. Estado vivo em `options-trades-v2-data-manifest.json`; conferir `runningPid`, processo e recibos antes de afirmar continuidade. Não iniciar outra instância nem editar o código durante esta rodada. O manifesto muda durante a coleta; o commit preserva o checkpoint anterior, não uma alegação de completude.

Na primeira conferência posterior ao lançamento: processo presente, estado `running`, 28 GETs totais incluindo os pilotos, 20 folhas, 2.363 intervalos pendentes e zero erros. Essas quantidades descrevem somente aquele instante. A coleta ainda não estava completa e não foi calculado skew, sinal ou PnL real N13.

Antes do lançamento passaram dez testes sintéticos do coletor v2, cinco do auditor de identidade, seis do gerador N13 e as verificações de execução long/short v4. A revisão corrigiu a persistência dos motivos de parada, além dos limites de leitura e espera. Esses testes não validam rentabilidade.

Depois da aquisição: auditoria integral de identidades; join integral dos contratos; implementação/testes do pipeline offline; freeze antes dos skews reais; contagem DEV; backtest base/stress somente se a amostra permitir. Os subagentes atingiram limite de uso durante a preparação do pipeline offline, antes de criar seus arquivos. Não reexecutar delegações automaticamente para contornar a limitação; prosseguir diretamente quando possível. A meta permanece ativa, **0/7 aprovadas**.
