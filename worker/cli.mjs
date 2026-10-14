// Ponto de entrada: registra o carregador de TypeScript e delega para cli.ts.
import './register.mjs';
const {main} = await import('./cli.ts');
process.exitCode = await main(process.argv.slice(2), process.env);
