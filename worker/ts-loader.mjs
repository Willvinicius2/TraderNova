// Hooks do Node: carregam .ts transpilando com o `typescript` já instalado (sem dependências novas).
// Resolvem imports sem extensão ('./domain') e o alias '@/' usados em lib/.
import {existsSync, statSync} from 'node:fs';
import {readFile} from 'node:fs/promises';
import {fileURLToPath, pathToFileURL} from 'node:url';
import path from 'node:path';
import ts from 'typescript';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const isFile = (p) => existsSync(p) && statSync(p).isFile();
function candidates(base) {
  return [base, `${base}.ts`, path.join(base, 'index.ts')];
}
export async function resolve(specifier, context, next) {
  let base = null;
  if (specifier.startsWith('@/')) base = path.join(root, specifier.slice(2));
  else if ((specifier.startsWith('./') || specifier.startsWith('../')) && context.parentURL?.startsWith('file:')) {
    base = path.resolve(path.dirname(fileURLToPath(context.parentURL)), specifier);
  }
  if (base && !/\.(m?js|json|node)$/.test(base)) {
    const hit = candidates(base).find(isFile);
    if (hit) return {url: pathToFileURL(hit).href, shortCircuit: true};
  }
  return next(specifier, context);
}
export async function load(url, context, next) {
  if (!url.startsWith('file:') || !url.endsWith('.ts')) return next(url, context);
  const source = await readFile(fileURLToPath(url), 'utf8');
  const {outputText} = ts.transpileModule(source, {fileName: fileURLToPath(url), compilerOptions: {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022}});
  return {format: 'module', source: outputText, shortCircuit: true};
}
