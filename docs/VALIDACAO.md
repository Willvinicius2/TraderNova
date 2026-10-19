# Verificação da entrega inicial — 15/09/2026

- Código do site recuperado com histórico; arquivos de interface e motor mantidos sem alteração.
- Web: tipos, quatro grupos de testes existentes e build de produção concluídos.
- Mobile: tipos, testes de origem/links/navegação e exportação JavaScript Android/iOS/web concluídos; Expo Doctor: 21/21 verificações.
- Site original conferido visualmente em largura de celular: navegação inferior, cards, tema Nova Lab e cotação Kraken recebida ao vivo.
- Compartilhamento de arquivos, botão voltar e deep links nativos implementados; validação em aparelho real ainda necessária.
- Não foi gerado APK/IPA, não houve publicação nas lojas e não foram ativados serviços pagos.

Os testes não aprovam estratégias financeiras. Nenhum backtest histórico externo relatado nos chats foi reproduzido nesta entrega.

O CI está habilitado em [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (Fase 1, issue #9): web (tipos, lint, testes), RLS das migrações num Postgres descartável e mobile (tipos, testes, exportação).

## Etapa posterior — motor e simulações

Estudo real reproduzido: 18 combinações, 150 arquivos Binance com checksum, 24 meses mais aquecimento. Nenhuma combinação passou. Laboratório agora oferece presets de backtest e acompanhamento ao vivo; Robô mostra apenas sinais e busca condicionada à aprovação. Ver [motor e validação](MOTOR_E_VALIDACAO.md) e [resultados](../research/RESULTADOS.md).
