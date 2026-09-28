import fs from 'node:fs/promises';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

// Fixed exploratory protocol. This is a two-leg spot-price proxy, not a borrowable
// spot strategy or a backtest of perpetual futures.
const ROOT = new URL('../', import.meta.url);
const WINDOW = 120;
const FROM = Date.parse('2024-09-01T00:00:00Z');
const TO = Date.parse('2026-09-01T00:00:00Z');
const FEE = 0.001;
const SLIP = 0.0002;
const CAPITAL = 10_000;
const MAX_HOLD = 24;
const hash = data => createHash('sha256').update(data).digest('hex');

function fit(logEth, logBtc, t) {
  const start = t - WINDOW;
  let sx = 0, sy = 0, sxx = 0, sxy = 0;
  for (let i = start; i < t; i++) {
    const x = logBtc[i], y = logEth[i];
    sx += x; sy += y; sxx += x * x; sxy += x * y;
  }
  const mx = sx / WINDOW, my = sy / WINDOW;
  const denominator = sxx - WINDOW * mx * mx;
  if (denominator <= 1e-12) return null;
  const beta = (sxy - WINDOW * mx * my) / denominator;
  const alpha = my - beta * mx;
  let sumSq = 0;
  for (let i = start; i < t; i++) {
    const residual = logEth[i] - alpha - beta * logBtc[i];
    sumSq += residual * residual;
  }
  const sigma = Math.sqrt(sumSq / (WINDOW - 2));
  return { alpha, beta, sigma };
}

function zAt(logEth, logBtc, t, f) {
  return (logEth[t] - f.alpha - f.beta * logBtc[t]) / f.sigma;
}

function entrySide(previousZ, currentZ, beta) {
  if (!(beta >= 0.1 && beta <= 5)) return 0;
  if (previousZ <= -2 && currentZ > -2 && currentZ < 0) return 1;
  if (previousZ >= 2 && currentZ < 2 && currentZ > 0) return -1;
  return 0;
}

function openPosition(equity, ethOpen, btcOpen, side, f, time, index) {
  const ethWeight = 1 / (1 + f.beta);
  const btcWeight = f.beta / (1 + f.beta);
  const ethSign = side, btcSign = -side;
  const ethQty = ethSign * equity * ethWeight / (ethOpen * (1 + ethSign * SLIP));
  const btcQty = btcSign * equity * btcWeight / (btcOpen * (1 + btcSign * SLIP));
  const ethEntry = ethOpen * (1 + ethSign * SLIP);
  const btcEntry = btcOpen * (1 + btcSign * SLIP);
  const fee = FEE * (Math.abs(ethQty) * ethEntry + Math.abs(btcQty) * btcEntry);
  return { ethQty, btcQty, ethEntry, btcEntry, entryFee: fee, entryEquity: equity, side, f, time, index };
}

function liquidation(p, ethPrice, btcPrice) {
  const ethExit = ethPrice * (1 - Math.sign(p.ethQty) * SLIP);
  const btcExit = btcPrice * (1 - Math.sign(p.btcQty) * SLIP);
  const gross = p.ethQty * (ethExit - p.ethEntry) + p.btcQty * (btcExit - p.btcEntry);
  const exitFee = FEE * (Math.abs(p.ethQty) * ethExit + Math.abs(p.btcQty) * btcExit);
  return gross - p.entryFee - exitFee;
}

function run(eth, btc) {
  assert.equal(eth.length, btc.length);
  for (let i = 0; i < eth.length; i++) {
    if (eth[i].time !== btc[i].time || !Number.isFinite(eth[i].close) || !Number.isFinite(btc[i].close) || eth[i].close <= 0 || btc[i].close <= 0 || eth[i].open <= 0 || btc[i].open <= 0 || (i && eth[i].time - eth[i - 1].time !== 3_600_000)) throw new Error(`Invalid paired H1 candle at ${i}`);
  }
  const logEth = eth.map(b => Math.log(b.close)), logBtc = btc.map(b => Math.log(b.close));
  let equity = CAPITAL, peak = CAPITAL, maxDrawdown = 0, position = null, pending = null;
  const trades = [];
  let observations = 0, signals = 0;
  for (let i = WINDOW; i < eth.length; i++) {
    const time = eth[i].time;
    if (time < FROM) continue;
    if (time >= TO) break;
    if (pending) {
      if (pending.kind === 'exit') {
        const pnl = liquidation(position, eth[i].open, btc[i].open);
        equity += pnl;
        trades.push({ entry: position.time, exit: time, side: position.side, beta: position.f.beta, hours: i - position.index, netPnl: pnl, netPct: 100 * pnl / position.entryEquity, reason: pending.reason });
        position = null;
      } else if (pending.kind === 'entry') {
        position = openPosition(equity, eth[i].open, btc[i].open, pending.side, pending.fit, time, i);
      }
      pending = null;
    }
    // The last opening in the historical horizon is an administrative exit,
    // scheduled by the fixed study boundary rather than by future price data.
    if (i === eth.length - 1 || eth[i + 1].time >= TO) {
      if (position) {
        const pnl = liquidation(position, eth[i].open, btc[i].open);
        equity += pnl;
        trades.push({ entry: position.time, exit: time, side: position.side, beta: position.f.beta, hours: i - position.index, netPnl: pnl, netPct: 100 * pnl / position.entryEquity, reason: 'study-end' });
        position = null;
      }
    } else {
      observations++;
      if (position) {
        const z = zAt(logEth, logBtc, i, position.f);
        const target = position.side === 1 ? z >= 0 : z <= 0;
        const stop = position.side === 1 ? z <= -3 : z >= 3;
        if (target || stop || i - position.index + 1 >= MAX_HOLD) pending = { kind: 'exit', reason: target ? 'mean' : stop ? 'invalidated' : 'time' };
      } else if (i + 2 < eth.length && eth[i + 2].time < TO) {
        const f = fit(logEth, logBtc, i);
        if (f && f.sigma > 1e-6) {
          const previousZ = zAt(logEth, logBtc, i - 1, f);
          const currentZ = zAt(logEth, logBtc, i, f);
          const side = entrySide(previousZ, currentZ, f.beta);
          if (side) { pending = { kind: 'entry', side, fit: f }; signals++; }
        }
      }
    }
    const marked = equity + (position ? liquidation(position, eth[i].close, btc[i].close) : 0);
    peak = Math.max(peak, marked);
    maxDrawdown = Math.max(maxDrawdown, 100 * (peak - marked) / peak);
  }
  const wins = trades.filter(t => t.netPnl > 0).reduce((n, t) => n + t.netPnl, 0);
  const losses = trades.filter(t => t.netPnl < 0).reduce((n, t) => n - t.netPnl, 0);
  return { trades: trades.length, netPct: 100 * (equity / CAPITAL - 1), profitFactor: losses > 0 ? wins / losses : null, drawdownPct: maxDrawdown, signals, observations, tradeLog: trades };
}

async function loadSeries(symbol, manifest) {
  const meta = manifest.series.find(s => s.symbol === symbol && s.interval === 60);
  if (!meta) throw new Error(`Missing ${symbol} H1 manifest entry`);
  const bytes = await fs.readFile(new URL(`../research/cache/${meta.file}`, import.meta.url));
  if (hash(bytes) !== meta.sha256) throw new Error(`${symbol} SHA-256 mismatch`);
  const series = JSON.parse(bytes);
  if (series.length !== meta.bars || series[0].time !== meta.first || series.at(-1).time + 3_600_000 !== meta.toExclusive) throw new Error(`${symbol} coverage mismatch`);
  return { series, meta };
}

function selfTest() {
  const eth = [], btc = [];
  for (let i = 0; i < 122; i++) { btc.push(Math.log(100 + i)); eth.push(1 + 1.5 * btc[i] + 0.001 * Math.sin(i)); }
  const f = fit(eth, btc, 120);
  assert(f.beta > 1.49 && f.beta < 1.51);
  const altered = [...eth]; altered[120] += 99;
  assert.deepEqual(fit(altered, btc, 120), f, 'fit must exclude signal candle');
  assert.equal(entrySide(-2.1, -1.5, 1.2), 1);
  assert.equal(entrySide(2.1, 1.5, 1.2), -1);
  assert.equal(entrySide(-2.1, 0.5, 1.2), 0);
  const p = openPosition(CAPITAL, 100, 100, 1, { beta: 1 }, 0, 0);
  assert(Math.abs(p.entryFee - FEE * (Math.abs(p.ethQty) * p.ethEntry + Math.abs(p.btcQty) * p.btcEntry)) < 1e-10);
  assert(liquidation(p, 100, 100) < -23 && liquidation(p, 100, 100) > -25, 'both legs and both fills need costs');
  console.log('research-pairs self-test OK');
}

if (process.argv.includes('--self-test')) selfTest();
else {
  const manifest = JSON.parse(await fs.readFile(new URL('../research/cache/manifest.json', import.meta.url)));
  const [eth, btc] = await Promise.all([loadSeries('ETHUSDT', manifest), loadSeries('BTCUSDT', manifest)]);
  const result = run(eth.series, btc.series);
  const output = {
    generatedAt: new Date().toISOString(), validated: false,
    candidates: [
      { id: 'N1', name: 'Reversão relativa ETH/BTC', family: 'arbitragem estatística de pares', thesis: 'Desvios temporários do log-preço relativo podem reverter à média; uma posição em ETH é compensada por exposição oposta em BTC conforme beta causal.', rules: [
        'H1: OLS de log(ETH) em log(BTC) nos 120 candles fechados anteriores; z atual é fora da janela, z anterior usa o mesmo ajuste.',
        'Sinal quando z retorna de fora de ±2 para dentro ainda do mesmo lado da média; exigir 0,1 ≤ beta ≤ 5 e σ residual > 0,000001.',
        'Entrar no open H1 seguinte: ETH e BTC em sentidos opostos, notional bruto distribuído 1:beta; congelar alfa, beta e sigma.',
        'Sair no open seguinte a z atingir média, romper ±3 na direção adversa ou completar 24 candles; encerrar na abertura final do estudo.',
        'Triagem com capital 10.000 USDT, gross 100%, taxa 0,10% e slippage 0,02% por lado e perna, sem otimização.'
      ], requiredData: ['BTCUSDT e ETHUSDT spot H1 sincronizados e auditados', 'Preço e disponibilidade reais da perna vendida, borrow/margem e custos por venue para validação executável'], status: 'exploratory-rejected', results: { trades: result.trades, netPct: result.netPct, profitFactor: result.profitFactor, drawdownPct: result.drawdownPct }, limitations: [
        'Triagem retrospectiva exploratória: mesmo histórico já inspecionado por pesquisas anteriores; não é amostra intocada nem validação prospectiva.',
        'Venda spot é hipotética; aluguel, juros, margem, liquidação, restrições de lote e impacto não constam do cache.',
        'Beta OLS local não demonstra cointegração; correlação e hedge podem romper. Dados Binance spot/USDT não equivalem ao Kraken USD ou ao contrato da the5.',
        `Fonte: manifest SHA-256 ETH ${eth.meta.sha256}, BTC ${btc.meta.sha256}; ${result.signals} sinais, ${result.observations} fechamentos analisados.`
      ], references: [
        { title: 'Binance Public Data — arquivos spot e formato de klines', url: 'https://github.com/binance/binance-public-data/blob/master/README.md' },
        { title: 'Gatev, Goetzmann e Rouwenhorst — Pairs Trading (NBER)', url: 'https://www.nber.org/papers/w7032' }
      ] },
      { id: 'N2', name: 'Carry de funding spot–perpétuo', family: 'carry de funding com hedge spot', thesis: 'Quando funding realizado compensa base e custos, long spot e short perpétuo do mesmo ativo podem receber funding com delta aproximado de zero.', rules: [
        'Avaliar apenas contratos perpétuos com histórico real de funding realizado, horários e preços spot/perpétuo sincronizados.',
        'Usar funding conhecido antes de cada decisão como filtro; nunca antecipar a taxa liquidada futura.',
        'Comprar spot e vender perpétuo no mesmo notional; registrar margem, mark price, base, taxas, slippage e cada pagamento real de funding.',
        'Encerrar se expectativa causal líquida deixar de cobrir custos e risco de base, ou se limites de margem forem alcançados; parâmetros serão fixados antes da triagem.'
      ], requiredData: ['Funding realizado por símbolo e timestamp (ex.: GET /fapi/v1/fundingRate)', 'Klines/trades do perpétuo e spot sincronizados, mark price e base', 'Taxas executáveis, margem, liquidação e custo de capital'], status: 'awaiting-required-data', limitations: [
        'Sem backtest ou métricas: os caches locais contêm candles spot, não pagamentos de funding nem preços do perpétuo.',
        'Funding pode mudar de sinal e de intervalo; pagamentos só ocorrem se a posição estiver aberta no horário de liquidação.',
        'Hedge não elimina base, liquidação, risco de venue e execução. Não é compatível automaticamente com conta the5.'
      ], references: [
        { title: 'Binance USDⓈ-M Futures API — funding rate history e mark price', url: 'https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data' },
        { title: 'Binance Futures — funding rates e liquidação', url: 'https://www.binance.com/en/support/faq/detail/360033525031' }
      ] }
    ]
  };
  await fs.writeFile(new URL('../public/research/novel-study.json', import.meta.url), JSON.stringify(output, null, 2) + '\n');
  console.log(JSON.stringify({ ...result, tradeLog: undefined, ethSha256: eth.meta.sha256, btcSha256: btc.meta.sha256 }));
}
