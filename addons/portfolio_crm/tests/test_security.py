from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import PortfolioCrmCommon


@tagged("post_install", "-at_install")
class TestPortfolioCrmSecurity(PortfolioCrmCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Lead = cls.env["crm.lead"].with_context(skip_portfolio_auto_convert=True)
        cls.lead_rep = Lead.create(
            {
                "name": "Rep owned lead",
                "type": "lead",
                "partner_name": "Rep Co",
                "email_from": "repco@example.com",
                "user_id": cls.user_crm_rep.id,
                "team_id": cls.team.id,
            }
        )
        cls.lead_other = Lead.create(
            {
                "name": "Other owned lead",
                "type": "lead",
                "partner_name": "Other Co",
                "email_from": "otherco@example.com",
                "user_id": cls.user_other_rep.id,
                "team_id": cls.team.id,
            }
        )
        # Explicitly clear salesperson: crm.lead defaults user_id to env.user.
        cls.lead_unassigned = Lead.create(
            {
                "name": "Unassigned lead",
                "type": "lead",
                "partner_name": "Free Co",
                "email_from": "free@example.com",
                "team_id": cls.team.id,
                "user_id": False,
            }
        )
        cls.lead_unassigned.user_id = False

    def test_user_sees_own_and_unassigned_only(self):
        Lead = self.env["crm.lead"].with_user(self.user_crm_rep)
        visible_ids = set(Lead.search([]).ids)
        self.assertIn(self.lead_rep.id, visible_ids)
        self.assertIn(self.lead_unassigned.id, visible_ids)
        self.assertNotIn(self.lead_other.id, visible_ids)

    def test_user_cannot_read_other_assigned_lead(self):
        with self.assertRaises(AccessError):
            self.lead_other.with_user(self.user_crm_rep).read(["name"])

    def test_manager_sees_all(self):
        Lead = self.env["crm.lead"].with_user(self.user_crm_manager)
        visible_ids = set(Lead.search([]).ids)
        self.assertTrue(
            {self.lead_rep.id, self.lead_other.id, self.lead_unassigned.id}.issubset(visible_ids)
        )

    def test_assignment_wizard_round_robin(self):
        leads = self.lead_unassigned | self.lead_rep
        wizard = (
            self.env["portfolio.crm.lead.assign.wizard"]
            .with_user(self.user_crm_manager)
            .create(
                {
                    "lead_ids": [(6, 0, leads.ids)],
                    "user_id": self.user_crm_rep.id,
                    "team_id": self.team.id,
                    "mode": "round_robin",
                }
            )
        )
        wizard.action_assign()
        self.assertTrue(all(lead.user_id for lead in leads))
        self.assertTrue(all(lead.assignment_date for lead in leads))
