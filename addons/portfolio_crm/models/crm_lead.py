from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class CrmLead(models.Model):
    _inherit = "crm.lead"

    followup_date = fields.Date(
        string="Follow-up Date",
        tracking=True,
        help="Date by which the salesperson must follow up with this lead/opportunity.",
    )
    is_followup_overdue = fields.Boolean(
        string="Follow-up Overdue",
        compute="_compute_followup_status",
        store=True,
        help="True when follow-up date is in the past and the record is still open.",
    )
    days_to_followup = fields.Integer(
        string="Days to Follow-up",
        compute="_compute_followup_status",
        store=True,
    )
    weighted_revenue = fields.Monetary(
        string="Weighted Revenue",
        currency_field="company_currency",
        compute="_compute_weighted_revenue",
        store=True,
        help="Expected revenue weighted by win probability (expected × probability / 100).",
    )
    lead_quality = fields.Selection(
        selection=[
            ("cold", "Cold"),
            ("warm", "Warm"),
            ("hot", "Hot"),
        ],
        string="Lead Quality",
        default="warm",
        tracking=True,
    )
    qualification_score = fields.Integer(
        string="Qualification Score",
        compute="_compute_qualification_score",
        store=True,
        help="0–100 score based on completeness of lead information.",
    )
    portfolio_auto_ready = fields.Boolean(
        string="Ready for Auto-Convert",
        compute="_compute_portfolio_auto_ready",
        store=True,
        help="Lead meets the portfolio qualification threshold for automatic conversion.",
    )
    assignment_date = fields.Datetime(
        string="Salesperson Assigned On",
        readonly=True,
        copy=False,
    )
    portfolio_notes = fields.Text(string="Portfolio Notes")
    quotation_state_summary = fields.Char(
        string="Quotation Status",
        compute="_compute_quotation_state_summary",
    )
    open_quotation_count = fields.Integer(
        string="Open Quotations",
        compute="_compute_open_quotation_count",
        store=True,
    )

    _check_followup_horizon = models.Constraint(
        "CHECK(followup_date IS NULL OR followup_date <= (CURRENT_DATE + INTERVAL '365 day'))",
        "Follow-up date cannot be more than one year in the future.",
    )

    @api.depends("followup_date", "active", "probability", "stage_id", "stage_id.is_won")
    def _compute_followup_status(self):
        today = fields.Date.context_today(self)
        for lead in self:
            if not lead.followup_date or not lead.active or lead.probability == 0 or lead.stage_id.is_won:
                lead.is_followup_overdue = False
                lead.days_to_followup = 0
                continue
            delta = (lead.followup_date - today).days
            lead.days_to_followup = delta
            lead.is_followup_overdue = delta < 0

    @api.depends("expected_revenue", "probability")
    def _compute_weighted_revenue(self):
        for lead in self:
            lead.weighted_revenue = (lead.expected_revenue or 0.0) * ((lead.probability or 0.0) / 100.0)

    @api.depends(
        "contact_name",
        "partner_name",
        "partner_id",
        "email_from",
        "phone",
        "expected_revenue",
        "lead_quality",
        "user_id",
        "description",
    )
    def _compute_qualification_score(self):
        for lead in self:
            score = 0
            if lead.partner_id or lead.partner_name:
                score += 20
            if lead.contact_name:
                score += 15
            if lead.email_from:
                score += 20
            if lead.phone:
                score += 10
            if lead.expected_revenue:
                score += 15
            if lead.user_id:
                score += 10
            if lead.description:
                score += 5
            if lead.lead_quality == "hot":
                score += 5
            elif lead.lead_quality == "warm":
                score += 2
            lead.qualification_score = min(score, 100)

    @api.depends("type", "active", "qualification_score", "email_from", "partner_id", "partner_name")
    def _compute_portfolio_auto_ready(self):
        threshold = self._portfolio_auto_convert_threshold()
        for lead in self:
            lead.portfolio_auto_ready = bool(
                lead.type == "lead"
                and lead.active
                and lead.qualification_score >= threshold
                and lead.email_from
                and (lead.partner_id or lead.partner_name)
            )

    @api.depends("order_ids.state", "order_ids")
    def _compute_open_quotation_count(self):
        for lead in self:
            lead.open_quotation_count = len(
                lead.order_ids.filtered(lambda order: order.state in ("draft", "sent"))
            )

    @api.depends("order_ids.state", "order_ids")
    def _compute_quotation_state_summary(self):
        for lead in self:
            orders = lead.order_ids
            if not orders:
                lead.quotation_state_summary = _("No quotations")
                continue
            draft = orders.filtered(lambda order: order.state in ("draft", "sent"))
            confirmed = orders.filtered(lambda order: order.state in ("sale", "done"))
            cancelled = orders.filtered(lambda order: order.state == "cancel")
            parts = []
            if draft:
                parts.append(_("Open: %s") % len(draft))
            if confirmed:
                parts.append(_("Confirmed: %s") % len(confirmed))
            if cancelled:
                parts.append(_("Cancelled: %s") % len(cancelled))
            lead.quotation_state_summary = " | ".join(parts) if parts else _("No quotations")

    @api.onchange("lead_quality")
    def _onchange_lead_quality(self):
        """UI hint only: suggest priority from quality when priority is still default/empty."""
        mapping = {"cold": "0", "warm": "1", "hot": "2"}
        if self.lead_quality in mapping and self.priority in (False, "0", "1"):
            self.priority = mapping[self.lead_quality]

    @api.onchange("date_deadline")
    def _onchange_date_deadline_followup(self):
        """UI assistance: default follow-up a week before expected closing."""
        if self.date_deadline and not self.followup_date:
            self.followup_date = self.date_deadline - timedelta(days=7)

    @api.constrains("expected_revenue", "type")
    def _check_opportunity_revenue(self):
        for lead in self:
            if lead.type == "opportunity" and lead.expected_revenue < 0:
                raise ValidationError(_("Expected revenue cannot be negative on an opportunity."))

    @api.constrains("followup_date", "date_deadline")
    def _check_followup_before_deadline(self):
        for lead in self:
            if lead.followup_date and lead.date_deadline and lead.followup_date > lead.date_deadline:
                raise ValidationError(
                    _(
                        "Follow-up date (%(followup)s) cannot be after the expected closing "
                        "date (%(deadline)s)."
                    )
                    % {
                        "followup": lead.followup_date,
                        "deadline": lead.date_deadline,
                    }
                )

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._portfolio_touch_assignment_date(force_unassign=False)
        if not self.env.context.get("skip_portfolio_auto_convert"):
            leads._portfolio_auto_convert_qualified()
        return leads

    def write(self, vals):
        res = super().write(vals)
        if "user_id" in vals:
            self._portfolio_touch_assignment_date(force_unassign=True)
        if not self.env.context.get("skip_portfolio_auto_convert"):
            self._portfolio_auto_convert_qualified()
        return res

    def _portfolio_touch_assignment_date(self, force_unassign=False):
        now = fields.Datetime.now()
        to_stamp = self.filtered(lambda lead: lead.user_id and not lead.assignment_date)
        if to_stamp:
            super(CrmLead, to_stamp).write({"assignment_date": now})
        if force_unassign:
            to_clear = self.filtered(lambda lead: not lead.user_id and lead.assignment_date)
            if to_clear:
                super(CrmLead, to_clear).write({"assignment_date": False})

    @api.model
    def _portfolio_auto_convert_threshold(self):
        return 70

    def _portfolio_auto_convert_qualified(self):
        ready = self.filtered(lambda lead: lead.portfolio_auto_ready)
        if ready:
            ready.with_context(skip_portfolio_auto_convert=True).action_portfolio_convert()

    def action_portfolio_convert(self):
        """Convert qualified leads to opportunities using core CRM APIs."""
        leads = self.filtered(lambda lead: lead.type == "lead" and lead.active)
        if not leads:
            raise UserError(_("Only active leads can be converted to opportunities."))
        for lead in leads:
            if not (lead.partner_id or lead.partner_name or lead.contact_name):
                raise UserError(
                    _(
                        "Lead '%s' needs a contact name, partner name, or customer before conversion."
                    )
                    % lead.display_name
                )
            lead._handle_partner_assignment(create_missing=True)
            lead.convert_opportunity(lead.partner_id)
            if not lead.followup_date:
                lead.with_context(skip_portfolio_auto_convert=True).write(
                    {"followup_date": fields.Date.context_today(lead) + timedelta(days=3)}
                )
        return True

    def action_portfolio_mark_won(self):
        return self.action_set_won()

    def action_portfolio_mark_lost(self):
        return self.action_set_lost()

    def action_portfolio_assign_wizard(self):
        return {
            "name": _("Assign Sales Representative"),
            "type": "ir.actions.act_window",
            "res_model": "portfolio.crm.lead.assign.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_lead_ids": [(6, 0, self.ids)],
            },
        }
