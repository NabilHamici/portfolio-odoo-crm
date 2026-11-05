from odoo.tests import tagged

from .common import PortfolioCrmCommon


@tagged("post_install", "-at_install")
class TestPortfolioQuotationIntegration(PortfolioCrmCommon):
    def test_quotation_linked_to_opportunity_and_status_summary(self):
        opportunity = self.env["crm.lead"].create(
            {
                "name": "Quote opportunity",
                "type": "opportunity",
                "partner_id": self.partner.id,
                "expected_revenue": 5000,
                "probability": 60,
                "user_id": self.user_crm_rep.id,
                "team_id": self.team.id,
            }
        )
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "opportunity_id": opportunity.id,
                "user_id": self.user_crm_rep.id,
                "team_id": self.team.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )
        self.assertIn(order, opportunity.order_ids)
        self.assertEqual(opportunity.quotation_count, 1)
        self.assertEqual(opportunity.open_quotation_count, 1)
        self.assertIn("Open", opportunity.quotation_state_summary)

        order.action_confirm()
        opportunity.invalidate_recordset(["quotation_state_summary", "open_quotation_count", "sale_order_count"])
        self.assertEqual(opportunity.open_quotation_count, 0)
        self.assertGreaterEqual(opportunity.sale_order_count, 1)
        self.assertIn("Confirmed", opportunity.quotation_state_summary)

    def test_action_new_quotation_context_from_sale_crm(self):
        opportunity = self.env["crm.lead"].create(
            {
                "name": "New quote action",
                "type": "opportunity",
                "partner_id": self.partner.id,
                "expected_revenue": 2500,
                "user_id": self.user_crm_rep.id,
                "team_id": self.team.id,
            }
        )
        action = opportunity.action_new_quotation()
        self.assertEqual(action["res_model"], "sale.order")
        self.assertEqual(action["context"].get("default_opportunity_id"), opportunity.id)
        self.assertEqual(action["context"].get("default_partner_id"), self.partner.id)
