#!/usr/bin/env bash
# Verify Odoo 19 + PostgreSQL Docker stack health and connectivity.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}!${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*"; exit 1; }

echo "==> Checking Docker CLI"
command -v docker >/dev/null 2>&1 || fail "docker not found. Install Docker Desktop and ensure it is running."
docker info >/dev/null 2>&1 || fail "Docker daemon is not reachable. Open Docker Desktop and wait until it is ready."
ok "Docker daemon is running ($(docker version --format '{{.Server.Arch}}' 2>/dev/null || echo unknown arch))"

echo "==> Checking Compose services"
docker compose ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}' || true

DB_STATUS="$(docker compose ps db --format '{{.Status}}' 2>/dev/null || true)"
ODOO_STATUS="$(docker compose ps odoo --format '{{.Status}}' 2>/dev/null || true)"

echo "$DB_STATUS" | grep -qi 'up' || fail "db service is not Up. Run: docker compose up -d"
echo "$ODOO_STATUS" | grep -qi 'up' || fail "odoo service is not Up. Run: docker compose up -d"
ok "db and odoo containers are Up"

echo "==> PostgreSQL readiness (pg_isready)"
docker compose exec -T db pg_isready -U "${POSTGRES_USER:-odoo}" -d "${POSTGRES_DB:-postgres}" \
  || fail "PostgreSQL is not ready"
ok "PostgreSQL accepts connections"

echo "==> Odoo → PostgreSQL connection (from odoo container)"
# Uses the same credentials the Odoo entrypoint uses.
docker compose exec -T odoo bash -lc '
python3 - <<'"'"'PY'"'"'
import os, sys
try:
    import psycopg2
except ImportError:
    # Official odoo image may expose psycopg2 via odoo deps; fall back to socket probe.
    import socket
    host = os.environ.get("HOST", "db")
    port = int(os.environ.get("PORT", "5432"))
    s = socket.create_connection((host, port), timeout=5)
    s.close()
    print(f"TCP OK to {host}:{port} (psycopg2 not importable in this context)")
    sys.exit(0)

host = os.environ.get("HOST", "db")
port = os.environ.get("PORT", "5432")
user = os.environ.get("USER", "odoo")
password = os.environ.get("PASSWORD", "odoo")
dbname = "postgres"
conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname, connect_timeout=5)
cur = conn.cursor()
cur.execute("SELECT version();")
version = cur.fetchone()[0]
cur.close()
conn.close()
print(version)
PY
' || fail "Could not connect from Odoo container to PostgreSQL"
ok "Odoo container can reach PostgreSQL"

echo "==> Odoo HTTP endpoint"
ODOO_PORT="${ODOO_PORT:-8069}"
HTTP_CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "http://127.0.0.1:${ODOO_PORT}/web/database/selector" || true)"
if [[ "$HTTP_CODE" =~ ^(200|303)$ ]]; then
  ok "Odoo HTTP responded with ${HTTP_CODE} on port ${ODOO_PORT}"
else
  # Database manager may redirect; also accept root
  HTTP_ROOT="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "http://127.0.0.1:${ODOO_PORT}/" || true)"
  if [[ "$HTTP_ROOT" =~ ^(200|303)$ ]]; then
    ok "Odoo HTTP responded with ${HTTP_ROOT} on port ${ODOO_PORT}"
  else
    fail "Odoo HTTP not ready yet (selector=${HTTP_CODE}, root=${HTTP_ROOT}). Check: docker compose logs odoo"
  fi
fi

echo "==> Recent Odoo log tail"
if [[ -f logs/odoo.log ]]; then
  tail -n 15 logs/odoo.log || true
else
  docker compose logs --tail=15 odoo || true
  warn "logs/odoo.log not present yet (file logging may still be starting)"
fi

echo
ok "Stack verification passed. Open http://localhost:${ODOO_PORT}"
