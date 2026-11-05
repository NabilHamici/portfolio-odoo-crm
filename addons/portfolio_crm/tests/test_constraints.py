from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import PortfolioCrmCommon


@tagged("post_install", "-at_install")
class TestPortfolioConstraints(PortfolioCrmCommon):
    def test_negative_expected_revenue_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["crm.lead"].create(
                {
                    "name": "Bad revenue",
                    "type": "opportunity",
                    "partner_id": self.partner.id,
                    "expected_revenue": -10,
                    "team_id": self.team.id,
                }
            )

    def test_followup_after_deadline_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["crm.lead"].create(
                {
                    "name": "Bad followup",
                    "type": "opportunity",
                    "partner_id": self.partner.id,
                    "expected_revenue": 100,
                    "date_deadline": fields.Date.today() + timedelta(days=5),
                    "followup_date": fields.Date.today() + timedelta(days=10),
                    "team_id": self.team.id,
                }
            )

    @mute_logger("odoo.sql_db")
    def test_followup_too_far_sql_constraint(self):
        with self.assertRaises(Exception):
            self.env["crm.lead"].create(
                {
                    "name": "Far followup",
                    "type": "opportunity",
                    "partner_id": self.partner.id,
                    "expected_revenue": 100,
                    "followup_date": fields.Date.today() + timedelta(days=400),
                    "team_id": self.team.id,
                }
            )
            self.env.cr.flush()
