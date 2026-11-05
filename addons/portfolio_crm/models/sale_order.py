from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Intentionally thin: sale_crm already links sale.order ↔ crm.lead via opportunity_id.
    # Quotation status on opportunities is computed from order_ids in crm.lead.
