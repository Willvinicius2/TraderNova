# TraderNova

- Preserve o visual original do site e os três temas: Essencial Dark, Nova Lab, Claro & Direto. O usuário rejeitou uma interface mobile recriada.
- O mobile usa a interface publicada em React Native WebView. Não substitua por outro layout sem pedido explícito.
- Web na raiz: pnpm na versão de package.json, lockfile preservado. Mobile em mobile/: npm e lockfile próprios.
- Catálogo: XAUUSD, NAS100, BTCUSD, ETHUSD, SOLUSD, EURUSD, USDJPY. Sinais são exemplos; nenhuma estratégia aprovada e nenhuma execução de ordens.
- Leia docs/ESCOPO_CONSOLIDADO.md e mobile/README.md antes de alterar funcionalidades ou integrações.
- Não ative cobrança, infraestrutura paga, publicação nas lojas ou negociação para completar configuração técnica.
- Prefira respostas concisas e chamadas necessárias. Modelo principal (Fable 5.1 ou Opus 5.5, escolhido pelo usuário) orquestra: planejamento, decisões, integração e revisão final. Trabalho pesado delimitado vai para o subagente `trabalho-pesado` (Haiku 5.5, esforço baixo); tarefas que exigem mais raciocínio, ou após duas falhas do Haiku, para `trabalho-medio` (Sonnet 5.5, esforço médio). Economia substitui a antiga preferência Astra Max. Contexto mínimo, sem duplicação, sem pesquisa aberta ou repetições sem necessidade; repasse essas regras. Não prometa consumo de cota nem ative APIs pagas.
- Meta vigente desde 29/09/2026: no mínimo sete famílias economicamente distintas validadas, conforme research/validation/protocol.json. Preserve os protocolos e freezes anteriores em research/goal-seven sem reescrevê-los; reduzir a quantidade não reduz os critérios de aprovação.
- Valide o motor com npm test na raiz; o mobile com npm run typecheck, npm test e npm run export dentro de mobile/.
