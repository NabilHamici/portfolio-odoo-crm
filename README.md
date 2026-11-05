# Portfolio Odoo CRM

Professional **Odoo 19 Community** portfolio project: a reproducible Docker development environment plus a custom CRM & Sales extension module.

**Repository:** [NabilHamici/portfolio-odoo-crm](https://github.com/NabilHamici/portfolio-odoo-crm)

---

## Author & role

| | |
|---|---|
| **Developer** | Nabil Hamici |
| **Role** | Sole developer — environment architecture, module design, implementation, security, tests, documentation |
| **Scope** | Local Odoo 19 stack + custom addon `portfolio_crm` |

This project demonstrates practical Odoo backend skills: Docker-based environments, ORM extensions, security (groups / ACLs / record rules), Sales integration, UI views, demo data, and automated `TransactionCase` tests.

---

## What is included

### 1. Development environment
- Odoo **19 Community** (`odoo:19.0`) on **macOS Apple Silicon**
- PostgreSQL **16** with persistent Docker volumes
- Docker Compose orchestration (Colima or Docker Desktop)
- Custom addons bind-mount (`./addons` → `/mnt/extra-addons`)
- Developer logging and hot-reload friendly config

### 2. Business module — `portfolio_crm`
Extends core `crm` + `sale_crm` (does **not** fork Odoo CRM):

- Lead / opportunity pipeline with qualification scoring
- Automatic lead → opportunity conversion when qualified
- Follow-up tracking and weighted pipeline revenue
- Salesperson assignment wizard
- Quotation status on opportunities
- CRM User / CRM Manager groups and record rules
- Dashboard (graph + pivot)
- Demo data + automated test suite

Module docs: [`addons/portfolio_crm/README.md`](addons/portfolio_crm/README.md)

---

## Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Application | Odoo 19 CE | ERP / CRM runtime |
| Database | PostgreSQL 16 | Persistent business data |
| Orchestration | Docker Compose | Local services |
| Runtime (macOS arm64) | Colima (recommended) or Docker Desktop | Container engine |
| Custom code | `./addons` | Portfolio modules |

---

## Repository structure

```text
.
├── addons/
│   └── portfolio_crm/          # Advanced CRM & Sales module
├── config/
│   └── odoo.conf               # Odoo runtime configuration
├── data/postgresql/            # Reserved (named volumes used by default)
├── logs/                       # Host-visible Odoo logs (gitignored content)
├── scripts/
│   └── verify_stack.sh         # Stack health checks
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Prerequisites

- macOS Apple Silicon (arm64) recommended
- [Homebrew](https://brew.sh)
- Docker engine + Compose (**Colima** or **Docker Desktop**)
- Git
- ~10–15 GB free disk for first image pull

### Start Docker (Colima)

```bash
brew install colima docker docker-compose
mkdir -p ~/.docker
# In ~/.docker/config.json add:
#   "cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"]

colima start --arch aarch64 --vm-type=vz --cpu 4 --memory 4 --disk 30
docker context use colima
```

### Or Docker Desktop

```bash
brew install --cask docker
# Open Docker.app, then:
docker version && docker compose version
```

---

## Quick start

```bash
git clone https://github.com/NabilHamici/portfolio-odoo-crm.git
cd portfolio-odoo-crm

cp .env.example .env

docker compose pull
docker compose up -d
docker compose logs -f odoo
```

When Odoo is ready, open **http://localhost:8069**

Master password for the database manager: `admin` (see `config/odoo.conf`).

### Install the CRM module (demo database)

```bash
docker compose stop odoo
docker compose run --rm --no-deps --entrypoint bash odoo -lc '
odoo -d portfolio \
  --db_host=db --db_user=odoo --db_password=odoo \
  --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons \
  -i portfolio_crm --without-demo=False --stop-after-init --logfile=
'
docker compose start odoo
```

### Verify the stack

```bash
./scripts/verify_stack.sh
```

---

## Demo logins

After installing with demo data on database `portfolio`:

| Login | Password | Role |
|-------|----------|------|
| `admin` | `admin` | Administrator |
| `crm_rep` | `crm_rep` | CRM User (own + unassigned records) |
| `crm_manager` | `crm_manager` | CRM Manager (all CRM records) |

> If passwords were reset in a local environment, use the values configured on that database.

---

## Day-to-day commands

| Task | Command |
|------|---------|
| Start | `docker compose up -d` |
| Stop | `docker compose stop` |
| Logs (Odoo) | `docker compose logs -f odoo` |
| Shell (Odoo) | `docker compose exec odoo bash` |
| `psql` | `docker compose exec db psql -U odoo postgres` |
| Remove containers (keep volumes) | `docker compose down` |
| Wipe DB + filestore | `docker compose down -v` |

---

## Configuration

| Topic | Detail |
|-------|--------|
| Custom addons | `./addons` mounted at `/mnt/extra-addons` |
| PostgreSQL data | Named volume `odoo19-db-data` |
| Odoo filestore | Named volume `odoo19-web-data` |
| Logs | `./logs` → `/var/log/odoo` |
| HTTP | `8069` |
| Longpolling | `8072` |
| PostgreSQL | `5432` |

Ports are overridable via `.env` (see `.env.example`).

---

## Tests

```bash
docker compose stop odoo
docker compose run --rm --no-deps --entrypoint bash odoo -lc '
odoo -d portfolio_test --db_host=db --db_user=odoo --db_password=odoo \
  --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons \
  -i portfolio_crm --test-enable --test-tags=/portfolio_crm \
  --without-demo=True --stop-after-init --logfile= --log-level=test
'
docker compose start odoo
```

Expected: `0 failed, 0 error(s)` for the `portfolio_crm` suite.

---

## Troubleshooting (Apple Silicon)

| Symptom | Fix |
|---------|-----|
| `docker: command not found` | Start Colima / Docker Desktop |
| Port already in use | Change ports in `.env` |
| Odoo cannot reach DB | `docker compose ps` — wait until `db` is healthy |
| Permission errors on `./logs` | `mkdir -p logs && chmod 777 logs` |
| Slow first start | First pull downloads ~1.3 GB of images |

---

## License

Custom portfolio code under `addons/portfolio_crm` is provided for demonstration purposes (LGPL-3 aligned with Odoo Community addons). Odoo itself remains under its own license.
