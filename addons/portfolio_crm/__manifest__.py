{
    "name": "Portfolio CRM & Sales",
    "version": "19.0.1.0.0",
    "category": "Sales/CRM",
    "summary": "Advanced CRM pipeline, assignment, and Sales quotation integration",
    "description": """
Portfolio-grade CRM extensions for Odoo 19 Community.

Extends core CRM and sale_crm (does not fork crm.lead) with:
- Lead qualification scoring and automatic lead→opportunity conversion
- Follow-up tracking and weighted pipeline revenue
- Sales representative assignment wizard
- Quotation status visibility on opportunities
- Dedicated CRM User / CRM Manager security groups and record rules
- Pipeline dashboards and demo data
    """,
    "author": "Portfolio Lab",
    "license": "LGPL-3",
    "depends": [
        "crm",
        "sale_crm",
        "sale_management",
    ],
    "data": [
        "security/portfolio_crm_security.xml",
        "security/ir.model.access.csv",
        "wizard/crm_lead_assign_views.xml",
        "views/crm_lead_views.xml",
        "views/crm_dashboard_views.xml",
        "views/crm_menus.xml",
        "data/crm_stage_data.xml",
    ],
    "demo": [
        "data/demo_data.xml",
    ],
    "installable": True,
    "application": True,
}
