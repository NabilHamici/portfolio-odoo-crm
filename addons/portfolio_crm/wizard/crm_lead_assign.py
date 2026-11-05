from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class PortfolioCrmLeadAssignWizard(models.TransientModel):
    _name = "portfolio.crm.lead.assign.wizard"
    _description = "Assign CRM Leads to Sales Representatives"

    lead_ids = fields.Many2many(
        comodel_name="crm.lead",
        string="Leads / Opportunities",
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Sales Representative",
        required=True,
        domain="[('share', '=', False)]",
    )
    team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Sales Team",
    )
    mode = fields.Selection(
        selection=[
            ("single", "Assign all to one salesperson"),
            ("round_robin", "Round-robin across team members"),
        ],
        string="Assignment Mode",
        default="single",
        required=True,
    )

    @api.onchange("user_id")
    def _onchange_user_id(self):
        if self.user_id and not self.team_id:
            team = self.env["crm.team"]._get_default_team_id(user_id=self.user_id.id)
            self.team_id = team

    def action_assign(self):
        self.ensure_one()
        if not self.lead_ids:
            raise UserError(_("Select at least one lead or opportunity."))

        if self.mode == "single":
            values = {"user_id": self.user_id.id}
            if self.team_id:
                values["team_id"] = self.team_id.id
            self.lead_ids.with_context(skip_portfolio_auto_convert=True).write(values)
            return {"type": "ir.actions.act_window_close"}

        members = self.team_id.member_ids | self.team_id.user_id if self.team_id else self.user_id
        members = members.filtered(lambda user: user.active and not user.share)
        if not members:
            raise UserError(_("No active salespeople available for round-robin assignment."))

        member_list = list(members)
        for index, lead in enumerate(self.lead_ids):
            salesperson = member_list[index % len(member_list)]
            values = {"user_id": salesperson.id}
            if self.team_id:
                values["team_id"] = self.team_id.id
            lead.with_context(skip_portfolio_auto_convert=True).write(values)
        return {"type": "ir.actions.act_window_close"}
