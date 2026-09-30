import { spawnSync } from 'node:child_process';
for (const file of ['core', 'live-market', 'market-sources', 'calibration-research', 'historical-forward', 'calibration-presets', 'calibration-v3', 'production-workspace', 'validation-plan']) {
  const result = spawnSync(process.execPath, [`tests/${file}.mjs`], { stdio: 'inherit' });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}
const captureTests=spawnSync(process.execPath,['--test','tests/continuous-depth-worker.test.mjs'],{stdio:'inherit'});
if(captureTests.error)throw captureTests.error;
if(captureTests.status!==0)process.exit(captureTests.status??1);
for (const file of ['cfd-contract-import', 'capture-aave-finalized', 'aave-bundle-audit', 'n21-signal-features']) {
  const result=spawnSync('python',[`tests/${file}.py`],{stdio:'inherit',timeout:180000});
  if(result.error)throw result.error;
  if(result.status!==0)process.exit(result.status??1);
}
