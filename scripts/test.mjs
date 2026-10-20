import { spawnSync } from 'node:child_process';
for (const file of ['core', 'live-market', 'market-sources', 'calibration-research', 'historical-forward', 'calibration-presets', 'calibration-v3', 'signal-record', 'signal-route', 'supabase-signals', 'worker-status', 'worker', 'account']) {
  const result = spawnSync(process.execPath, [`tests/${file}.mjs`], { stdio: 'inherit' });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}
