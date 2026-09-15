# TraderNova

- Preserve o visual original do site e os três temas: Essencial Dark, Nova Lab, Claro & Direto. O usuário rejeitou uma interface mobile recriada.
- O mobile usa a interface publicada em React Native WebView. Não substitua por outro layout sem pedido explícito.
- Web na raiz: pnpm na versão de package.json, lockfile preservado. Mobile em mobile/: npm e lockfile próprios.
- Catálogo: XAUUSD, NAS100, BTCUSD, ETHUSD, SOLUSD, EURUSD, USDJPY. Sinais são exemplos; nenhuma estratégia aprovada e nenhuma execução de ordens.
- Leia docs/ESCOPO_CONSOLIDADO.md e mobile/README.md antes de alterar funcionalidades ou integrações.
- Não ative cobrança, infraestrutura paga, publicação nas lojas ou negociação para completar configuração técnica.
- Prefira respostas concisas e chamadas necessárias. Delegue apenas subtarefas independentes que compensem seu custo; preferência do usuário: gpt-6-astra com esforço max quando a ferramenta confirmar disponibilidade. Repasse estas preferências aos subagentes.
- Valide o motor com npm test na raiz; o mobile com npm run typecheck, npm test e npm run export dentro de mobile/.
