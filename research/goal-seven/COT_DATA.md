# N8 / H3 — auditoria CFTC Gold, sem backtest

**Decisão:** no snapshot histórico disponível, a regra H3 original não alcança a amostra mínima. O arquivo CFTC permite contar candidatos por data de referência, mas não reconstruir com segurança o instante em que cada observação ficou disponível. Não há resultado de negociação, validação ou estratégia aprovada.

## Fonte e integridade

Em 28/09/2026, `scripts/download-goal-cot.py` preservou os ZIPs oficiais [Disaggregated, Futures Only, histórico comprimido](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm): arquivo conjunto de 2006–2016 e anuais de 2017–2026. Foram selecionadas exclusivamente as linhas `GOLD - COMMODITY EXCHANGE INC.` / código CFTC `088691`, com `Open_Interest_All`, `M_Money_Positions_Long_All` e `M_Money_Positions_Short_All`. Há 1.059 observações distintas por `Report_Date_as_YYYY-MM-DD`, de 13/06/2006 a 22/09/2026. Os ZIPs originais e o CSV derivado ficam em `research/cache/goal-seven/cot/` (ignorado pelo Git); URLs, tamanhos, SHA-256, abrangência e contagens estão em `research/goal-seven/cot-data-manifest.json`. `python scripts/download-goal-cot.py --verify` confere os arquivos locais sem baixar nem alterar o snapshot. O script recusa sobrescrever ZIP local se o fornecedor publicar bytes diferentes.

O campo `Report_Date_as_YYYY-MM-DD` é **data das posições**, geralmente terça-feira, não timestamp de publicação. A [agenda CFTC](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm) indica publicação usual sexta-feira às 15h30 ET, sujeita a feriados. A [FAQ CFTC](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) afirma que não há lista completa das datas históricas de publicação, apenas aproximadamente 13 meses no site. Logo, a regra “primeira abertura após a publicação” não pode ser executada retrospectivamente só com esses ZIPs. Não atribuir sexta-feira por fórmula, nem transformar terça em entrada.

As [comunicações especiais CFTC](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm) registram a suspensão por shutdown em 2018–2019, o atraso e a recuperação gradual após o incidente ION em fevereiro–março/2023, e o atraso por interrupção de dotações em outubro–dezembro/2025. Também registram correção posterior envolvendo **CMX Gold** para relatório de março/2019. Portanto, a consulta ao arquivo anual atual não demonstra que seus números coincidam com cada versão vista pelo mercado no passado, mesmo que a FAQ descreva a política geral de não atualizar dados históricos. Os [esclarecimentos CFTC](https://www.cftc.gov/MarketReports/CommitmentsofTraders/DisaggregatedExplanatoryNotes/index.htm) dizem ainda que o histórico 2006–2009 foi disponibilizado apenas em outubro/2009 e reconstruído com classificações posteriores; ele serve para aquecimento descritivo, não como divulgação semanal contemporânea. **Vintage/PIT não verificado.**

## Teto de sinais da regra prévia

Somente contagem, sem preço nem PnL. Para cada relatório, `P=(Long−Short)/Open Interest`. O script usa as 104 observações **anteriores** e percentis de posto mais próximo (10º = 11ª ordem; 90º = 94ª ordem). Candidato vendido exige `P` atual estritamente acima do percentil 90 e `P` em duas quedas consecutivas; comprado exige estritamente abaixo do percentil 10 e duas altas. As janelas, fixadas antes da contagem, são aquecimento 2006–2010, desenvolvimento 2011–2015, validação 2016–2020 e recente 2021–agosto/2026.

**Desvio de sequência:** a instrução era contar primeiro apenas o desenvolvimento e encerrar ao falhar. Também consultei as contagens de sinais da validação e do período recente após constatar 12/100 no desenvolvimento. Não consultei preços nem PnL nessas janelas, mas elas **não são holdouts intocados para H3**. Esta consulta está registrada também no manifesto; nenhum parâmetro foi recalibrado.

| Janela | Relatórios | Teto de candidatos H3 | Mínimo de trades exigido |
| --- | ---: | ---: | ---: |
| Desenvolvimento 2011–2015 | 261 | 12 | 100 |
| Validação 2016–2020 | 261 | 5 | 100 |
| Recente 2021–ago/2026 | 295 | 10 | 50 |

Esses números são **tetos condicionais ao snapshot atual**, pois cada candidato foi contado na data de referência sem demonstrar divulgação oportuna, abertura executável ou ausência de posição durante as cinco sessões. Não são tetos provados para vintages históricos desconhecidos. Com no máximo uma abertura por relatório, a configuração H3 calculada nesses dados não alcança 100/100/50 nem sob execução perfeita. Assim, H3 fica encerrada nesta configuração por insuficiência de amostra, independentemente de lucro; a falta de vintages é uma barreira separada. Mudar percentis, janela ou duração após esta contagem constituiria outra hipótese e exigiria registro anterior a qualquer novo teste; não resgata a aprovação de H3.

Fixture sintética da contagem: conferi exclusão do relatório atual nas 104 observações do percentil, limites estritos (igualdade não aciona), direções comprada/vendida e duas altas/quedas consecutivas. Nenhuma série de preços ou retorno entrou nesse teste.

Um coletor prospectivo, caso se investigue uma hipótese futura, deve consultar somente a publicação oficial ativa da CFTC, salvar **bytes brutos imutáveis**, URL, hora UTC de recebimento observada e SHA-256 em log incremental, e registrar qualquer correção como nova versão. E-mail oficial de aviso de publicação pode ser evidência auxiliar, mas não substitui o snapshot do relatório. Mesmo essa coleta não reconstitui vintages anteriores a seu início.
