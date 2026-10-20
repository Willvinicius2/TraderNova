# Política de privacidade — RASCUNHO

> Rascunho técnico da Fase 2 (issue #23) para orientar o texto final da Fase 5 (#38). Não é aconselhamento jurídico e não está publicado.

## Quais dados o TraderNova guarda

| Dado | Onde | Para quê |
| --- | --- | --- |
| E-mail e identificador da conta | Supabase Auth | Entrar sem senha e separar os dados de cada pessoa. |
| Diário de decisões (decisão, anotação, retrato do sinal de exemplo, data) | Banco Supabase, tabela `journal_entries` | Mostrar o mesmo diário no celular e no computador. |
| Preferências (tema, densidade, alertas no app) | `user_preferences` | Manter a aparência e os avisos escolhidos. |
| Aparelhos para notificação | `push_devices` | Enviar alertas, quando existirem. |
| Plano | `entitlements` | Assinaturas futuras; hoje todos são gratuitos. |
| Dados locais (diário sem conta, tema, experimentos) | Armazenamento do navegador ou da WebView | Funcionar sem conta. Não saem do aparelho, a menos que você importe o diário. |

Não guardamos senha, dados de corretora, conta de negociação ou ordens. O TraderNova não envia ordens.

## Seus direitos (LGPD)

- **Acesso e portabilidade:** aba Conta → **Exportar meus dados** baixa um JSON com tudo o que está na conta.
- **Exclusão:** aba Conta → **Excluir conta** apaga a conta e, em cascata, diário, preferências, aparelhos e plano. Não pode ser desfeito.
- **Dados locais:** limpar os dados do site no navegador ou desinstalar o app apaga o que ficou só no aparelho.

## Pendente para o texto final

Controlador e contato, base legal de cada tratamento, prazo de retenção de logs do Supabase, região do servidor, operadores (Supabase, provedor de e-mail, hospedagem) e aviso de risco de mercado.
