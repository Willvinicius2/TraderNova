# Exportar especificações MT5 — The5ers

O script `The5ersContractExport.mq5` consulta somente propriedades públicas dos símbolos na sessão MT5 conectada. Não envia ordens, lê posições/histórico, nem consulta login/saldo. Para ativos ausentes, registra `missing_on_server`; não tenta adivinhar sufixos. A lista é configurável pelo input `InpSymbols`.

## Executar

1. No MT5 da conta **High Stakes**, abra MetaEditor, crie um Script MQL5, substitua o conteúdo pelo arquivo e compile localmente.
2. Execute o script uma vez no terminal conectado. Inputs padrão: BTCUSD, ETHUSD, SOLUSD, XAUUSD, NAS100, EURUSD, USDJPY. Edite a lista para testar sufixos que a própria corretora indicar.
3. Encontre CSV e metadata em Pasta compartilhada `MetaQuotes/Terminal/Common/Files`, acima da pasta específica do terminal; não dentro dela. Verifique `status`, timestamp/tick atual e dados antes de usar.
4. `commission` é deliberadamente `unknown_requires_broker_confirmation`; números zero em outros campos podem representar propriedade indisponível e precisam ser cotejados no MT5/broker. O metadata marca `utcClockApproved=false` até validar sincronização de relógio.

O script seleciona os símbolos existentes para leitura, o que pode adicioná-los ao Market Watch. Não altera ordens ou conta.

Referências MQL5 oficiais:

- https://www.mql5.com/en/docs/marketinformation/symbolinfointeger
- https://www.mql5.com/en/docs/marketinformation/symbolinfodouble
- https://www.mql5.com/en/docs/marketinformation/symbolinfostring
- https://www.mql5.com/en/docs/marketinformation/symbolinfotick
- https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants
- https://www.mql5.com/en/docs/files/fileopen
- https://www.mql5.com/en/docs/account/accountinfostring
- https://www.mql5.com/en/docs/dateandtime/timegmt
- https://www.mql5.com/en/docs/dateandtime/timetradeserver

Exportador ainda não compilado nem executado neste PC. Propriedades cuja consulta falha aparecem em `unavailable_fields`; não inferir custos zero de campo indisponível. O horário do tick é do servidor e não foi certificado como UTC.

## Importação offline

CSV e metadata usam UTF-8. Preserve os dois arquivos originais. Na raiz do projeto, execute `python scripts/import_cfd_contracts.py --csv CAMINHO.csv --metadata CAMINHO_metadata.txt --output research/cache/validation/contratos-importados.json` com caminhos reais e uma saída ainda inexistente.

O importador limita arquivos/linhas, calcula SHA-256, conserva campos textuais e verifica estrutura, números, escalas e spread. Símbolos ausentes, sessões não coletadas, comissão desconhecida e relógio não certificado permanecem bloqueios. A importação nunca aprova custos, execução, estratégia ou resultado financeiro; o programa/servidor são declarações não verificadas. As duas formas de quoting possíveis foram testadas sinteticamente, mas ainda falta uma saída real do MT5. Não há coleta contínua de ticks nem executor neste script.
