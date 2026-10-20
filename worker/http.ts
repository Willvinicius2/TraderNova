import {createServer, type Server} from 'node:http';
import type {AddressInfo} from 'node:net';
import {isPublicSignalId} from '../lib/tradernova/signal-record';
import type {Logger} from './log';
import {findSignalOnDisk} from './signal-file-store';
import {readFileStatuses} from './status-file';
export const readHost = '127.0.0.1';
const allowedHosts = new Set(['127.0.0.1', 'localhost', '[::1]']);
/** Servidor HTTP somente leitura (GET /signals/:id e GET /status) preso a 127.0.0.1, sem CORS: quem consulta é o servidor web, nunca o navegador. */
export function createSignalReadServer(opts: {signalsDir: string; statusDir?: string; log?: Logger}): Server {
  return createServer(async (req, res) => {
    const send = (status: number, body: unknown) => {
      res.writeHead(status, {'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'});
      res.end(JSON.stringify(body));
    };
    try {
      if (!allowedHosts.has((req.headers.host ?? '').replace(/:\d+$/, '').toLowerCase())) return send(403, {error: 'host-not-allowed'}); // contra DNS rebinding
      const pathname = new URL(req.url ?? '/', `http://${readHost}`).pathname;
      const match = /^\/signals\/([^/]+)$/.exec(pathname);
      if (!match && !(pathname === '/status' && opts.statusDir)) return send(404, {error: 'not-found'});
      if (req.method !== 'GET') { res.setHeader('Allow', 'GET'); return send(405, {error: 'method-not-allowed'}); }
      if (!match) return send(200, await readFileStatuses(opts.statusDir!));
      let id: string;
      try { id = decodeURIComponent(match[1]); } catch { return send(400, {error: 'invalid-id'}); }
      if (!isPublicSignalId(id)) return send(400, {error: 'invalid-id'});
      const record = await findSignalOnDisk(opts.signalsDir, id);
      return record ? send(200, record) : send(404, {error: 'not-found'});
    } catch (error) {
      opts.log?.error('leitura_http_falhou', {error: error instanceof Error ? error.message : String(error)});
      if (!res.headersSent) send(500, {error: 'read-failed'}); else res.end();
    }
  });
}
/** Sobe o servidor de leitura. `port` 0 = porta efêmera (testes). Rejeita se a porta estiver ocupada. */
export function startSignalReadServer(opts: {signalsDir: string; statusDir?: string; port: number; log?: Logger}): Promise<{server: Server; port: number; close(): Promise<void>}> {
  const server = createSignalReadServer(opts);
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(opts.port, readHost, () => {
      server.off('error', reject);
      resolve({server, port: (server.address() as AddressInfo).port, close: () => new Promise<void>((done) => { server.close(() => done()); server.closeAllConnections(); })});
    });
  });
}
