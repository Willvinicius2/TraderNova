import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import ts from 'typescript';
const require=createRequire(import.meta.url);
export async function loadResearchModules(){
 const temp=await fs.mkdtemp(path.join(os.tmpdir(),'tradernova-engine-'));
 try{
  for(const name of ['domain','indicators','research','calibration','calibration-v3','active-presets','live-market','historical','paper-engine']){
   const source=await fs.readFile(new URL(`../lib/tradernova/${name}.ts`,import.meta.url),'utf8');
   const js=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText.replace(/from '(\.\/[^']+)'/g,"from '$1.mjs'").replaceAll("'zod'",JSON.stringify(pathToFileURL(require.resolve('zod')).href));
   await fs.writeFile(path.join(temp,`${name}.mjs`),js);
  }
  return {domain:await import(pathToFileURL(path.join(temp,'domain.mjs'))),research:await import(pathToFileURL(path.join(temp,'research.mjs'))),calibration:await import(pathToFileURL(path.join(temp,'calibration.mjs'))),v3:await import(pathToFileURL(path.join(temp,'calibration-v3.mjs'))),historical:await import(pathToFileURL(path.join(temp,'historical.mjs'))),paper:await import(pathToFileURL(path.join(temp,'paper-engine.mjs'))),presets:await import(pathToFileURL(path.join(temp,'active-presets.mjs'))),cleanup:()=>fs.rm(temp,{recursive:true,force:true})};
 }catch(error){await fs.rm(temp,{recursive:true,force:true});throw error;}
}
