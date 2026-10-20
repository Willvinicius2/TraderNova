#!/usr/bin/env bash
# Instala o worker como serviço numa VM Debian/Ubuntu já com Node 22+ (recomendado 24) e git. Idempotente. Ver docs/DEPLOY.md.
# Uso (como root): bash deploy/worker/install.sh [ref]   (ref padrão: main)
set -euo pipefail
REPO=${TRADERNOVA_REPO:-https://github.com/Willvinicius2/TraderNova.git}
REF=${1:-main}
DIR=/opt/tradernova
[ "$(id -u)" -eq 0 ] || { echo "Rode como root (sudo)."; exit 2; }
node -e 'process.exit(Number(process.versions.node.split(".")[0])>=22?0:1)' || { echo "Instale o Node 22 ou mais novo antes (ver docs/DEPLOY.md)."; exit 2; }
if [ -d "$DIR/.git" ]; then git -C "$DIR" fetch --depth 1 origin "$REF" && git -C "$DIR" checkout -q --detach FETCH_HEAD
else git clone --depth 1 --branch "$REF" "$REPO" "$DIR"; fi
cd "$DIR"
npm run install:ci
install -d -m 700 /etc/tradernova
if [ ! -f /etc/tradernova/worker.env ]; then
  install -m 600 deploy/worker/worker.env.example /etc/tradernova/worker.env
  echo "Preencha TRADERNOVA_SUPABASE_SERVICE_KEY em /etc/tradernova/worker.env e rode de novo."; exit 3
fi
grep -q '^TRADERNOVA_SUPABASE_SERVICE_KEY=.\+' /etc/tradernova/worker.env || { echo "TRADERNOVA_SUPABASE_SERVICE_KEY vazia em /etc/tradernova/worker.env."; exit 3; }
install -m 644 deploy/worker/tradernova-worker.service /etc/systemd/system/tradernova-worker.service
systemctl daemon-reload
systemctl enable --now tradernova-worker
systemctl restart tradernova-worker
sleep 5
systemctl --no-pager --lines 20 status tradernova-worker || true
echo "Logs: journalctl -u tradernova-worker -f"
