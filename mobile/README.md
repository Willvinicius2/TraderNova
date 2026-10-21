# TraderNova Mobile

Base Android/iPhone com **a mesma interface do site aprovado**: layout, cards, ícones, navegação, três temas, mercado, robô, estratégias, laboratório e diário.

## Executar

Requer Node 22.13+ (testado com Node 24).

```powershell
cd D:\openclaude\TradersNova\mobile
npm ci
npm start
```

Use Expo Go compatível com SDK 57 ou uma development build. `npm run android` usa emulador/aparelho com ambiente Android instalado. `npm run web` abre o próprio site no navegador.

## Funcionamento

- Expo + React Native WebView abre `https://tradernova.willvinicius.chatgpt.site/`.
- A interface é a publicação original, sem outra camada de cards, menus ou telas recriadas.
- Preferências, diário e experimentos usam o armazenamento do site dentro da WebView. Esse armazenamento é separado do navegador do computador e ainda não sincroniza pela conta.
- Área segura e barra de status acompanham o tema escolhido no site.
- Links externos HTTPS abrem no navegador. O botão voltar do Android retorna dos detalhes/abas; os links `tradernova://signal/<uuid>` (somente UUID v4) abrem a ficha do sinal persistido na mesma WebView (`?aba=robo&sinal=<uuid>`); ver docs/SINAIS.md.
- Exportações JSON acionadas pelo site abrem o compartilhamento nativo.
- Push (Fase 4, preparado): `expo-notifications` com canal `sinais`. A permissão só é pedida quando o site envia `push-register` (após login); o toque na notificação abre a ficha pelo mesmo link `tradernova://signal/<uuid>`. Sem conta Expo vinculada, nenhum token é gerado. Ver [docs/NOTIFICACOES.md](../docs/NOTIFICACOES.md).
- Em falha de carregamento, há aviso e tentativa de reconexão. **O app depende de internet**; não há funcionamento offline completo ou feed contínuo em segundo plano.

## Verificar

```powershell
npm run typecheck
npm test
npm run export
npx expo-doctor
```

`export` gera bundles JavaScript Android/iOS/web em `dist/`; **não gera APK/IPA**. Testes de origem, links e navegação ficam em `tests/site.mjs`. O motor e a interface web continuam no projeto raiz, com testes em `../tests/`.

## Builds e lojas

`eas.json` prepara development build, APK interno e produção. Para gerar APK, vincule à sua conta Expo e execute `npx eas-cli build --platform android --profile preview`. Builds iOS locais exigem macOS/Xcode; distribuição iOS exige credenciais Apple. Builds remotos dependem da disponibilidade/franquia da conta. Nenhum serviço pago ou envio às lojas foi ativado.

Os identificadores iniciais `com.willvinicius.tradernova` devem ser confirmados antes das lojas. Aprovação nas lojas, testes físicos, push remoto, Supabase/login, compras/recibos e privacidade/exclusão seguem pendentes. O aplicativo contém a funcionalidade atual do site; não ativa estratégias, notificações ou assinaturas que ainda não existem nele.

Referências: [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/), [builds Expo](https://docs.expo.dev/build/setup/). Veja também [escopo consolidado](../docs/ESCOPO_CONSOLIDADO.md).
