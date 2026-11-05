from odoo.addons.mail.tests.common import mail_new_test_user
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class PortfolioCrmCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        cls.user_crm_rep = mail_new_test_user(
            cls.env,
            name="CRM Rep Test",
            login="portfolio_crm_rep",
            email="portfolio.crm.rep@example.com",
            groups="portfolio_crm.group_crm_user,crm.group_use_lead,base.group_user",
        )
        cls.user_crm_manager = mail_new_test_user(
            cls.env,
            name="CRM Manager Test",
            login="portfolio_crm_manager",
            email="portfolio.crm.manager@example.com",
            groups="portfolio_crm.group_crm_manager,crm.group_use_lead,base.group_user",
        )
        cls.user_other_rep = mail_new_test_user(
            cls.env,
            name="Other Rep Test",
            login="portfolio_crm_other",
            email="portfolio.crm.other@example.com",
            groups="portfolio_crm.group_crm_user,crm.group_use_lead,base.group_user",
        )

        cls.team = cls.env["crm.team"].create(
            {
                "name": "Portfolio Test Team",
                "use_leads": True,
                "use_opportunities": True,
                "member_ids": [(4, cls.user_crm_rep.id), (4, cls.user_other_rep.id)],
                "user_id": cls.user_crm_manager.id,
            }
        )

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer Co",
                "email": "buyer@testcustomer.example",
                "is_company": True,
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Implementation Service",
                "list_price": 1000.0,
                "type": "service",
                "invoice_policy": "order",
            }
        )
