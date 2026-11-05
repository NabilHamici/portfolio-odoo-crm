from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from .common import PortfolioCrmCommon


@tagged("post_install", "-at_install")
class TestPortfolioComputedFields(PortfolioCrmCommon):
    def test_weighted_revenue_and_qualification_score(self):
        lead = self.env["crm.lead"].create(
            {
                "name": "Score lead",
                "type": "lead",
                "partner_name": "Score Co",
                "contact_name": "Pat",
                "email_from": "pat@score.example",
                "phone": "+1 555 1000",
                "expected_revenue": 10000,
                "probability": 50,
                "lead_quality": "hot",
                "user_id": self.user_crm_rep.id,
                "team_id": self.team.id,
                "description": "Qualified inbound",
            }
        )
        # Auto-convert may turn this into opportunity; values remain valid either way.
        self.assertEqual(lead.weighted_revenue, 5000.0)
        self.assertGreaterEqual(lead.qualification_score, 70)

    def test_followup_overdue_flag(self):
        opportunity = self.env["crm.lead"].create(
            {
                "name": "Overdue opp",
                "type": "opportunity",
                "partner_id": self.partner.id,
                "expected_revenue": 2000,
                "probability": 30,
                "user_id": self.user_crm_rep.id,
                "team_id": self.team.id,
                "followup_date": fields.Date.today() - timedelta(days=2),
            }
        )
        self.assertTrue(opportunity.is_followup_overdue)
        self.assertLess(opportunity.days_to_followup, 0)

        opportunity.write({"followup_date": fields.Date.today() + timedelta(days=5)})
        self.assertFalse(opportunity.is_followup_overdue)
        self.assertEqual(opportunity.days_to_followup, 5)
