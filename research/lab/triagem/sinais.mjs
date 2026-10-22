// Triagem em massa: calcula os sinais de cada indicador da biblioteca deepentropy (ports em TypeScript dos scripts do
// TradingView) com os parâmetros padrão do autor, num ativo e tempo gráfico, e grava as listas de candles com sinal.
//
// Uso: node sinais.mjs <lci.mjs> <pasta de candles> <ativo> <tf,tf> <pasta de saída> <id> [<id> ...]
//
// Para cada indicador saem "regras" (pares compra/venda) de três fontes, nesta ordem:
//   alerta   alertcondition() do autor, classificado como compra ou venda pelo título;
//   marcador plotshape/labels do autor (forma, posição ou texto) e alert() com mensagem de compra/venda;
//   generica só quando o autor não marca sinal: fechamento x linha 0 (sobreposto ao preço), linha 0 x linha 1,
//            ou linha 0 x zero (oscilador que troca de sinal).
// Teste de repintura (ao vivo): sinais sorteados precisam aparecer quando o indicador só vê os candles até o próprio
// sinal; quem falha usa dado futuro, é marcado como repinta e não segue para o backtest.
import fs from 'fs';
import path from 'path';

const [lciPath, barsDir, asset, tfArg, outDir, ...ids] = process.argv.slice(2);
const lib = await import(path.resolve(lciPath));
const reg = new Map(lib.indicatorRegistry.map((e) => [e.id, e]));

const LONG = /\b(buy|long|bull|bullish|up|uptrend|upward|green|rising|rise|positive|oversold|support|golden|enter long|call|crossover|cross over|crosses over|crosses above|above|higher|long entry)\b/i;
const SHORT = /\b(sell|short|bear|bearish|down|dn|downtrend|downward|red|falling|fall|negative|overbought|resistance|death|enter short|put|crossunder|cross under|crosses under|crosses below|below|lower|short entry)\b/i;
const EXITY = /\b(exit|take profit|tp\d?|stop loss|sl hit|close long|close short)\b/i;

function side(text) {
  const t = (text || '').replace(/[_\-]/g, ' ');
  if (EXITY.test(t)) return 0;
  const l = LONG.test(t), s = SHORT.test(t);
  if (l && !s) return 1;
  if (s && !l) return -1;
  // "X to Y": vale o destino (ex.: "Downtrend to Uptrend")
  const m = t.match(/\bto\b(.*)$/i);
  if (m) { const l2 = LONG.test(m[1]), s2 = SHORT.test(m[1]); if (l2 && !s2) return 1; if (s2 && !l2) return -1; }
  return 0;
}
function markerSide(mk) {
  const t = side(mk.text);
  if (t) return t;
  const sh = mk.shape || '', pos = mk.position || '';
  if (/arrowUp|triangleUp|labelUp/.test(sh)) return 1;
  if (/arrowDown|triangleDown|labelDown/.test(sh)) return -1;
  if (pos === 'belowBar') return 1;
  if (pos === 'aboveBar') return -1;
  return 0;
}
const words = (s) => new Set((s || '').toLowerCase().replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter((w) => w && !LONG.test(w) && !SHORT.test(w)));
const sim = (a, b) => { const A = words(a), B = words(b); let k = 0; for (const w of A) if (B.has(w)) k++; return k / Math.max(1, Math.max(A.size, B.size)); };

function rulesOf(e, r, bars) {
  const idx = new Map(bars.map((b, i) => [b.time, i]));
  const toIdx = (times) => [...new Set(times.map((t) => idx.get(t)).filter((i) => i !== undefined))].sort((a, b) => a - b);
  const rules = [];
  // 1) alertcondition: pares compra/venda por semelhança de título
  const al = (r.alerts || []).filter((a) => a.times && a.times.length);
  const L = al.filter((a) => side(a.title) === 1), S = al.filter((a) => side(a.title) === -1);
  const used = new Set();
  for (const a of L) {
    let best = null, bs = -1;
    for (const b of S) { if (used.has(b.id)) continue; const s = sim(a.title, b.title); if (s > bs) { bs = s; best = b; } }
    if (best) { used.add(best.id); rules.push({ fonte: 'alerta', nome: `${a.title} / ${best.title}`, long: toIdx(a.times), short: toIdx(best.times) }); }
    if (rules.length >= 3) break;
  }
  // 2) marcadores (plotshape, labels) e alert()
  if (!rules.length) {
    const lt = [], st = [];
    for (const mk of r.markers || []) { const s = markerSide(mk); if (s > 0) lt.push(mk.time); else if (s < 0) st.push(mk.time); }
    for (const c of r.alertCalls || []) { const s = side(c.message); if (s > 0) lt.push(c.time); else if (s < 0) st.push(c.time); }
    for (const lb of r.labels || []) { const s = side(lb.text); if (s > 0 && lb.time !== undefined) lt.push(lb.time); else if (s < 0 && lb.time !== undefined) st.push(lb.time); }
    if (lt.length && st.length) rules.push({ fonte: 'marcador', nome: 'marcadores de compra / venda', long: toIdx(lt), short: toIdx(st) });
  }
  // 3) genérica pelas linhas
  if (!rules.length && r.plots) {
    const ps = Object.values(r.plots).filter((p) => Array.isArray(p) && p.length === bars.length)
      .map((p) => p.map((x) => (x && x.value != null && isFinite(x.value) ? x.value : NaN)))
      .filter((v) => v.filter((x) => !isNaN(x)).length > bars.length * 0.5);
    const cross = (a, b) => { const up = [], dn = [];
      for (let i = 1; i < a.length; i++) { const x = a[i] - b[i], y = a[i - 1] - b[i - 1]; if (isNaN(x) || isNaN(y)) continue; if (x > 0 && y <= 0) up.push(i); else if (x < 0 && y >= 0) dn.push(i); }
      return { up, dn }; };
    const close = bars.map((b) => b.close);
    if (ps.length) {
      let g = null;
      if (e.overlay) { g = cross(close, ps[0]); g.nome = 'fechamento x linha 1'; }
      else if (ps.length >= 2) { g = cross(ps[0], ps[1]); g.nome = 'linha 1 x linha 2'; }
      else { const v = ps[0].filter((x) => !isNaN(x)); if (Math.min(...v) < 0 && Math.max(...v) > 0) { g = cross(ps[0], ps[0].map(() => 0)); g.nome = 'linha 1 x zero'; } }
      if (g && g.up.length && g.dn.length) rules.push({ fonte: 'generica', nome: g.nome, long: g.up, short: g.dn });
    }
  }
  return rules;
}

function loadBars(tf) {
  const B = JSON.parse(fs.readFileSync(path.join(barsDir, `${asset}_${tf}.json`)));
  return B.time.map((t, i) => ({ time: t, open: B.open[i], high: B.high[i], low: B.low[i], close: B.close[i], volume: B.volume[i] }));
}

const tfs = tfArg.split(',');
const barsBy = Object.fromEntries(tfs.map((tf) => [tf, loadBars(tf)]));
for (const id of ids) {
  const e = reg.get(id);
  for (const tf of tfs) {
    const bars = barsBy[tf];
    const out = { id, tf, asset, nome: e ? e.name : id, grupo: e?.group, categoria: e?.category, overlay: e?.overlay, regras: [] };
    const t0 = Date.now();
    try {
      if (!e) throw new Error('id desconhecido');
      if (e.requiredSymbols) { const rq = e.requiredSymbols(e.defaultInputs); if (rq && rq.length) throw new Error('precisa de outro ativo'); }
      if (e.usesVisibleRange) throw new Error('depende da área visível do gráfico');
      const r = e.calculate(bars, { ...e.defaultInputs });
      const rules = rulesOf(e, r, bars);
      // Teste "ao vivo": para até 12 sinais sorteados de cada regra (entre 40% e 95% do histórico), o indicador é
      // recalculado só com os candles até o candle do sinal; o sinal precisa aparecer ali, no último candle. Um sinal
      // desenhado para trás (pivô, divergência confirmada depois) some nesse teste. E em 6 cortes ao acaso, um sinal no
      // último candle do histórico cortado precisa continuar no histórico completo (sinal que some depois = repinta).
      const cache = new Map();
      const at = (j) => { if (!cache.has(j)) cache.set(j, rulesOf(e, e.calculate(bars.slice(0, j + 1), { ...e.defaultInputs }), bars.slice(0, j + 1))); return cache.get(j); };
      let seed = 12345; const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
      const lo = Math.floor(bars.length * 0.4), hi = Math.floor(bars.length * 0.95);
      for (const ru of rules) {
        const sig = [...ru.long.map((i) => [i, 'long']), ...ru.short.map((i) => [i, 'short'])].filter(([i]) => i >= lo && i < hi);
        const pick = [];
        while (pick.length < Math.min(12, sig.length)) { const x = sig[Math.floor(rnd() * sig.length)]; if (!pick.includes(x)) pick.push(x); }
        let miss = 0;
        for (const [j, sd] of pick) { const o = at(j).find((x) => x.nome === ru.nome); if (!o || !o[sd].includes(j)) miss++; }
        ru.repinta = miss; ru.checados = pick.length;
      }
      for (let k = 0; k < 6; k++) {
        const j = lo + Math.floor(rnd() * (hi - lo));
        for (const o of at(j)) {
          const ru = rules.find((x) => x.nome === o.nome); if (!ru) continue;
          for (const sd of ['long', 'short']) if (o[sd].includes(j) && !ru[sd].includes(j)) ru.repinta = (ru.repinta || 0) + 1;
        }
      }
      out.regras = rules;
    } catch (err) {
      out.erro = String(err && err.message ? err.message : err).slice(0, 200);
    }
    out.n = bars.length;
    for (const ru of out.regras) ru.n = bars.length;
    out.ms = Date.now() - t0;
    const dir = path.join(outDir, asset, tf);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, `${id}.json`), JSON.stringify(out));
  }
}
