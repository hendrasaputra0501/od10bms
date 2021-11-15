from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError

class UtilityUsage(models.Model):
    _name = 'bm.utility.entry'
    _description = 'BM Utility Usage'

    operator_id = fields.Many2one('res.users', string="Operator", default=lambda self: self.env.user.id, required=True)
    date_stop = fields.Date(string="As of Date", required=True)
    state = fields.Selection([('draft', 'Draft'),('done', 'Valid')], string="Status", default='draft')
    electricity_usage = fields.Boolean('Electricity Usage')
    water_usage = fields.Boolean('Water Usage')
    electricity_usage_ids = fields.One2many('bm.electricity.usage', 'entry_id', string="Electricity Usage")
    water_usage_ids = fields.One2many('bm.water.usage', 'entry_id', string="Water Usage")
    company_id = fields.Many2one('res.company', string="Company",
        default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string="Currency",
        default=lambda self: self.env.user.company_id.currency_id)
    initial_value = fields.Boolean('Initial Value')

    # ----------------------------------------
    # Actions
    # ----------------------------------------
    @api.multi
    def action_validate(self):
        drafts = self.filtered(lambda x: x.state=='draft')
        for entry in drafts:
            entry.electricity_usage_ids.allocate_price()
            entry.electricity_usage_ids.confirm()
            entry.water_usage_ids.allocate_price()
            entry.water_usage_ids.confirm()
        return self.write({'state': 'done'})

    @api.multi
    def set_draft(self):
        for entry in self:
            entry.electricity_usage_ids.set_draft()
            entry.water_usage_ids.set_draft()
        return self.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        valid = self.filtered(lambda x: x.state!='draft')
        if valid:
            raise ValidationError(_("Some of these data already Validated.\n \
                You can not delete data other than Draft State"))
        return super(UtilityUsage, self).unlink()