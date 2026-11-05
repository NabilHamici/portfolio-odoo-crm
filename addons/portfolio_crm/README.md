# Portfolio CRM & Sales (`portfolio_crm`)

Odoo **19** Community extension that turns core CRM + Sales into a portfolio-ready pipeline application.

This module **extends** `crm` and `sale_crm`. It does not fork `crm.lead` or replace Odoo Sales.

## Features

- Lead / opportunity pipeline with Kanban stages (core CRM)
- Qualification score, lead quality, follow-up dates, weighted revenue
- Automatic lead → opportunity conversion when qualification threshold is met
- Manual convert / won / lost actions
- Salesperson assignment wizard (single or round-robin)
- Quotation creation and status on opportunities (`sale_crm`)
- Dedicated **CRM User** / **CRM Manager** groups + record rules
- Portfolio dashboard (graph + pivot)

## Architecture

```text
portfolio_crm/
├── models/
│   ├── crm_lead.py          # extends crm.lead
│   └── sale_order.py        # thin sale.order inherit
├── wizard/
│   └── crm_lead_assign.py   # assignment transient model
├── security/                # groups, ACLs, record rules
├── views/                   # form/list/kanban/search/dashboard/menus
├── data/                    # feature flags + demo
└── tests/                   # TransactionCase suite
```

### Dependencies

`crm`, `sale_crm`, `sale_management`

### Key model extensions (`crm.lead`)

| Field | Type | Notes |
|-------|------|-------|
| `followup_date` | Date | Sales follow-up deadline |
| `is_followup_overdue` | Boolean (stored) | Computed from follow-up vs today |
| `weighted_revenue` | Monetary (stored) | `expected_revenue × probability / 100` |
| `qualification_score` | Integer (stored) | 0–100 completeness score |
| `portfolio_auto_ready` | Boolean (stored) | Ready for auto-convert |
| `quotation_state_summary` | Char | Open / confirmed / cancelled quotes |

Business conversions call core APIs: `convert_opportunity()`, `action_set_won()`, `action_set_lost()`, `action_new_quotation()`.

### Security

| Group | Implies | Access |
|-------|---------|--------|
| CRM User | Sales: Own Documents | Own + unassigned CRM leads |
| CRM Manager | CRM User + Sales Administrator | All CRM leads |

## Installation (Docker / Colima)

From the repository root:

```bash
colima start
docker context use colima
cd ~/Desktop/OdooProject

# Stop the long-running web process to avoid DB lock contention during install
docker compose stop odoo

# Create DB + install with demo data
# Use --entrypoint bash so CLI flags are not swallowed by the image entrypoint.
docker compose run --rm --no-deps --entrypoint bash odoo -lc '
odoo -d portfolio \
  --db_host=db --db_user=odoo --db_password=odoo \
  --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons \
  -i portfolio_crm --without-demo=False --stop-after-init --logfile=
'

docker compose start odoo
```

Open http://localhost:8069 — database `portfolio`.

Demo logins (with demo data):

| Login | Password | Role |
|-------|----------|------|
| `admin` | (set at DB creation) | Admin / CRM Manager |
| `crm_rep` | `crm_rep` | CRM User |
| `crm_manager` | `crm_manager` | CRM Manager |

Master password for DB manager: `admin` (see `config/odoo.conf`).

### Upgrade after code changes

```bash
docker compose stop odoo
docker compose run --rm --no-deps --entrypoint bash odoo -lc '
odoo -d portfolio --db_host=db --db_user=odoo --db_password=odoo \
  --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons \
  -u portfolio_crm --stop-after-init --logfile=
'
docker compose start odoo
```

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

Expected result: `0 failed, 0 error(s)` for the `portfolio_crm` suite.

## Workflows

1. **Lead intake** → set contact/email/quality → score updates automatically  
2. **Auto-convert** when score ≥ 70 and email + partner identity exist  
3. **Assign** salesperson via header action / list server action  
4. **Opportunity** → set expected revenue, probability, follow-up  
5. **New Quotation** (sale_crm) → track status on the Portfolio tab  
6. **Mark Won / Lost** when the deal closes  

## Quality notes

- Computed fields use `@api.depends`; stored where used in search/group/dashboard  
- `@api.onchange` is UI-only (priority / follow-up suggestions)  
- SQL + Python constraints validate follow-up horizon and revenue  
- Compatible with Odoo 19 patterns (`models.Constraint`, `res.groups.privilege`, `group_ids`)
