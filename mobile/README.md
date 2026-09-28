# TraderNova Mobile

Base Android/iPhone com **a mesma interface do site aprovado**: layout, cards, ícones, navegação, três temas, mercado, robô, estratégias, laboratório e diário.

## Executar

Requer Node 22.13+ (testado com Node 24).

```powershell
cd D:\openclaude\TradersNova\mobile
npm ci
npm start
```

Para testar explicitamente no Expo Go, use `npm run start:go`. Isso evita abrir uma development build não instalada. O celular precisa alcançar o servidor do computador. Para testar a interface sem depender dele, abra [TraderNova](https://tradernova.willvinicius.chatgpt.site/?aba=robo) no navegador do celular e use **Testar exemplo de sinal**. Em Android, use o menu do navegador para adicionar à tela inicial; em iPhone, Compartilhar → Adicionar à Tela de Início, quando disponível.

No iPhone, o Expo Go da App Store atende até SDK 54; este projeto usa SDK 57. Para testar a versão nativa, é preciso uma development build assinada ou Expo Go personalizado via `eas go`, com distribuição TestFlight e conta Apple Developer ativa. Não presuma compatibilidade com o Expo Go comum. `npm run android` usa emulador/aparelho com ambiente Android instalado. `npm run web` abre o próprio site no navegador.

## Funcionamento

- Expo + React Native WebView abre `https://tradernova.willvinicius.chatgpt.site/`.
- A interface é a publicação original, sem outra camada de cards, menus ou telas recriadas.
- Preferências, diário e experimentos usam o armazenamento do site dentro da WebView. Esse armazenamento é separado do navegador do computador e ainda não sincroniza pela conta.
- Área segura e barra de status acompanham o tema escolhido no site.
- Links externos HTTPS abrem no navegador. O botão voltar do Android retorna dos detalhes/abas; os links `tradernova://signal/ID` abrem exemplos já salvos na mesma WebView.
- Exportações JSON acionadas pelo site abrem o compartilhamento nativo.
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

## Teste imediato no iPhone

A versão web publicada já tem manifesto standalone e ícone Apple. Abra no Safari, use Compartilhar → Adicionar à Tela de Início e mantenha Abrir como App da Web ativo, se disponível. Confira instruções na aba Conta. Esta instalação não é um IPA e não depende do servidor local.

Fonte atualizada: https://docs.expo.dev/get-started/set-up-your-environment/?device=physical&mode=expo-go&platform=ios

## TestFlight preparado nesta revisão

Projeto vinculado: `@willvinicius/tradernova-mobile`, ID `f9e6ee09-4b87-47b7-a9b1-a1cbc3ca2a53`. Perfil `testflight` configurado para distribuição de loja em iPhone físico. Conta Free e cota iOS disponíveis verificadas; nenhuma cobrança ativada. A primeira tentativa parou por certificado/perfil ausentes, antes da compilação. O usuário decidiu concluir a assinatura Apple depois.

No diretório mobile, configurar assinatura interativamente: `npx eas-cli@24.8.0 credentials:configure-build --platform ios --profile testflight`. Depois: `npx eas-cli@24.8.0 build --platform ios --profile testflight`. Submissão via `npx eas-cli@24.8.0 submit --platform ios --profile testflight` depende do build concluído e acesso App Store Connect. Login e 2FA devem ser realizados nos prompts oficiais; não guardar senhas, certificados ou chaves no Git.
