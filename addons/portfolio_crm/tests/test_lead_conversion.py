from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import PortfolioCrmCommon


@tagged("post_install", "-at_install")
class TestPortfolioLeadConversion(PortfolioCrmCommon):
    def test_manual_convert_lead_to_opportunity(self):
        lead = self.env["crm.lead"].with_context(skip_portfolio_auto_convert=True).create(
            {
                "name": "Manual convert lead",
                "type": "lead",
                "partner_name": "Manual Co",
                "email_from": "sam@manual.example",
                "team_id": self.team.id,
                "lead_quality": "cold",
            }
        )
        self.assertEqual(lead.type, "lead")
        self.assertFalse(lead.portfolio_auto_ready)
        lead.write({"contact_name": "Sam", "expected_revenue": 3000})
        lead.with_context(skip_portfolio_auto_convert=True).action_portfolio_convert()
        self.assertEqual(lead.type, "opportunity")
        self.assertTrue(lead.partner_id)
        self.assertTrue(lead.followup_date)

    def test_auto_convert_when_qualified(self):
        lead = self.env["crm.lead"].create(
            {
                "name": "Auto convert lead",
                "type": "lead",
                "partner_name": "Auto Co",
                "contact_name": "Alex",
                "email_from": "alex@auto.example",
                "phone": "+1 555 2000",
                "expected_revenue": 8000,
                "lead_quality": "hot",
                "user_id": self.user_crm_rep.id,
                "team_id": self.team.id,
                "description": "Complete data for auto convert",
            }
        )
        self.assertEqual(lead.type, "opportunity")
        self.assertTrue(lead.partner_id)

    def test_convert_requires_identity(self):
        lead = self.env["crm.lead"].with_context(skip_portfolio_auto_convert=True).create(
            {
                "name": "Anonymous lead",
                "type": "lead",
                "team_id": self.team.id,
            }
        )
        with self.assertRaises(UserError):
            lead.action_portfolio_convert()

    def test_won_and_lost_helpers(self):
        opportunity = self.env["crm.lead"].create(
            {
                "name": "Win/Lose opp",
                "type": "opportunity",
                "partner_id": self.partner.id,
                "expected_revenue": 1000,
                "probability": 20,
                "user_id": self.user_crm_rep.id,
                "team_id": self.team.id,
            }
        )
        opportunity.action_portfolio_mark_won()
        self.assertEqual(opportunity.probability, 100)
        self.assertTrue(opportunity.stage_id.is_won)

        opportunity2 = self.env["crm.lead"].create(
            {
                "name": "Lost opp",
                "type": "opportunity",
                "partner_id": self.partner.id,
                "expected_revenue": 1000,
                "probability": 20,
                "user_id": self.user_crm_rep.id,
                "team_id": self.team.id,
            }
        )
        opportunity2.action_portfolio_mark_lost()
        self.assertFalse(opportunity2.active)
        self.assertEqual(opportunity2.probability, 0)
